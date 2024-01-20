import datetime
from typing import List, Dict

from vertexai.generative_models._generative_models import HarmBlockThreshold, HarmCategory, Content, Part
from vertexai.language_models._language_models import MultiCandidateTextGenerationResponse
from vertexai.preview.generative_models import (
    GenerativeModel,
    Tool,
)
from vertexai.preview.language_models import ChatSession

from ai_assistant.tools.base import ToolInterface, FinalAnswerTool
from ai_assistant.tools.code_execution import CodeExecutionTool
from ai_assistant.tools.file_system import WriteFileTool, MakeDirectoryTool

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
}
MODEL_CONFIG = {
    'max_output_tokens': 8192,
    'temperature': 0,
    'top_p': 0.5,
}


def get_today() -> str:
    today = datetime.date.today()
    return today.strftime('%B %d, %Y')


class Assistant(object):
    def __init__(self, tools: List[ToolInterface], verbose: bool = True):
        self.tools = Tool(
            function_declarations=[
                tool.function_declaration for tool in tools
            ]
        )
        self.tools_by_name: Dict[str, ToolInterface] = {
            tool.name: tool for tool in tools
        }
        self.model = GenerativeModel(
            'gemini-pro',
            generation_config=MODEL_CONFIG,
            safety_settings=SAFETY_SETTINGS,
            tools=[self.tools],
        )
        self.system_prompt: str = (
            f'Today is {get_today()}. Answer the question as best as you can.'
            ' You have a set of tools to help generate the answer.'
            ' When required, you can use one or more of those tools.'
            ' Plan and solve the problem step-by-step. Look at the previous output and decide what to do next.'
            ' Accordingly, plan what tool to use if any.'
            ' When all the prior steps are successful and you have the final answer for the question available,'
            f' you will call the `{FinalAnswerTool.name}` and do nothing more.'
            ' However, if the action taken in any of the steps results in any error,'
            ' the subsequent steps should try to fix it before reaching the final answer.'
            # '\n\n'
            # 'Question:'
        )
        self.max_steps: int = 10
        self.verbose = verbose

    @staticmethod
    def get_chat_response(chat_session: ChatSession, prompt: str) -> MultiCandidateTextGenerationResponse:
        response = chat_session.send_message(prompt)
        return response

    def run(self, question: str):
        # prompt = f'{self.system_prompt} {question}'
        # Since Gemini does not allow system prompt/context, mimic to have one
        history = [
            Content(role='user', parts=[Part.from_text(self.system_prompt)]),
            Content(role='model', parts=[
                Part.from_text('Okay. I will follow the instructions and help you achieve the goal.')
            ]),
        ]
        chat = self.model.start_chat(history=history)
        Assistant.get_chat_response(chat, question)
        prompt = question

        for idx in range(self.max_steps):
            print(f'\n>>>>> Turn {idx + 1} <<<<<')

            if self.verbose:
                print(f'>> The chat history so far:\n{chat.history}')
                print(f'?? The prompt: {prompt}')

            # try:
            response = Assistant.get_chat_response(chat, prompt)
            # except google.api_core.exceptions.Unknown as ux:
            #     print(f'*** An unknown exception occurred: {ux}')

            if response.candidates[0].finish_reason == 'SAFETY':
                print(f'*** Execution stopped because of SAFETY reasons')
                break

            # print(response.candidates[0].content.parts[0])
            print('-' * 20)

            func_call = response.candidates[0].content.parts[0].function_call
            func_name = func_call.name
            func_args = func_call.args
            # print(f'*** Function call: {func_name=}, {func_args=}')

            params = {}
            for arg in func_args:
                params[arg] = func_args[arg]

            if self.verbose:
                print(f'*** Function call: {func_name=}, {params=}')

            if func_name == FinalAnswerTool.name:
                print(f'Exiting loop after {idx + 1} runs because the final answer was found!')
                print(params['answer'])
                break
            elif func_name == '':
                print('* An error occurred: an empty function name was generated! Exiting...')
                break

            action_output = self.tools_by_name[func_name].use(params)

            if self.verbose:
                print(f'*** Output of the function call: {action_output}')

            prompt = f'\nPreviously used tool: {func_name}\nOutput of the previous action: {action_output}'


if __name__ == '__main__':
    # # Example 1: simple prompt, no file name
    # text = '''
    # Write Python code to display the current date. Also, find out tomorrow's date.
    # '''

    # # Example 2: simple prompt with a file name
    # text = (
    #     'Write a Python program to print the current date and time.'
    #     ' Save it in a file called test_demo.py. Execute the code and display the results.'
    # )

    # # Example 3
    # # This prompt asks to create a file in a directory
    # text = (
    #     'Write a Python program to print the current date and time.'
    #     ' Based on the day of the month, print all the natural numbers up to it.'
    #     ' Save the code in a file called test_demo.py. Execute the code and display the results.'
    #     ' All source code and other files should be created inside the `test_demo` directory.'
    # )

    # # Example 4: a more detailed prompt -- This does NOT work because of runtime errors
    # # Here, no explicit directory creation is suggested. However, the LLM sometimes creates
    # # a new dir while interpreting 'Python project' in the prompt. This behavior is not
    # # guaranteed. So, a side effect is that some existing files may get overwritten!
    # text = (
    #     ' You have the `inputs.txt` file containing a list of natural numbers, one in each line.'
    #     ' Create a Python project to read each such number and determine whether or not it is a prime number.'
    #     ' The output should be `Prime` or `Not prime`, written in a separate file.'
    #     ' Create a separate module that checks whether or not the numbers belong to Fibonacci sequence.'
    #     ' For this, the output should be `Fibonacci` or `Not Fibonacci`, written in another file.'
    #     ' All functions and modules should have appropriate docstrings.'
    #     ' Also, add a README.md file for the project.'
    #     ' Finally, execute the code and verify that everything is working fine.'
    # )

    # Example 5: build a website
    text = (
        'Background:\n'
        'John M. Doe is a scientist with Alien Institute of Artificial Intelligence.'
        ' He has five years of experience in the areas of NLP and computer vision.'
        ' He has published several research papers.'
        ' John is also an avid photographer. He has captured several images of UFOs around the world.'
        ' He was also a winner in the Best Annual Alien Silhouette Photography Competition.'
        '\n\nTasks:'
        '\nCreate a personal website for John. The website should use Bootstrap 5 as the CSS framework.'
        ' Create a separate page for each of the following sections: about, research, and hobbies.'
        ' Generate appropriate content for each page based on the background provided.'
        ' Add more relevant text to the pages by expanding the background.'
        ' There should be a navigation bar at the top. Ensure that all the pages are linked correctly.'
        ' The color theme should be primarily white with a dash of violet.'
        ' The footer should contain copyright notice and social media links.'
        ' All the files should be created inside a directory called `personal_website`.'
        ' When including CSS scripts from CDNs, do not add the integrity check.'
        ' Make sure that all code are correct and content properly formatted. There should be no broken links.'
    )

    assistant = Assistant(
        tools=[CodeExecutionTool, WriteFileTool, FinalAnswerTool, MakeDirectoryTool, ]
    )
    assistant.run(text.strip())
