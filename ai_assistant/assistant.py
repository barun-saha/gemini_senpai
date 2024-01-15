import datetime
from typing import List, Dict
from vertexai.generative_models._generative_models import HarmBlockThreshold, HarmCategory
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
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
}
MODEL_CONFIG = {
    'max_output_tokens': 8192,
    'temperature': 0,
    'top_p': 1,
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
            tools=[self.tools]
        )
        self.system_prompt: str = (
            f'Today is {get_today()}.'
            ' Answer the question as best as you can.'
            ' You have a set of tools to help generate the answer.'
            ' When required, you can use one or more of those tools.'
            ' Plan and solve the problem step-by-step. Look at the previous output and decide what to do next.'
            ' Accordingly, plan what tool to use if any.'
            ' When you have the final answer for the question available,'
            f' you will call the `{FinalAnswerTool.name}` and do nothing more.'
            '\n\n'
            'Question:'
        )
        self.max_steps: int = 10
        self.verbose = verbose

    @staticmethod
    def get_chat_response(chat: ChatSession, prompt: str) -> str:
        response = chat.send_message(prompt)
        # print(response)
        # return response.text
        return response

    def run(self, question: str):
        # prompt = f'{self.system_prompt} {question}'
        chat = self.model.start_chat()
        Assistant.get_chat_response(chat, self.system_prompt)
        prompt = question

        for idx in range(self.max_steps):
            print(f'\n>>>>> Turn {idx + 1} <<<<<')

            if self.verbose:
                print(f'*** The current prompt is: --->\n{prompt}<---')

            # response = self.model.generate_content(
            #     prompt,
            #     generation_config=MODEL_CONFIG,
            #     safety_settings=SAFETY_SETTINGS,
            #     tools=[self.tools]
            # )

            response = Assistant.get_chat_response(chat, prompt)

            if response.candidates[0].finish_reason == 'SAFETY':
                print(f'*** Execution stopped because of SAFETY reasons')
                break

            # print(response.candidates[0].content.parts[0])
            print('-' * 20)

            func_call = response.candidates[0].content.parts[0].function_call
            func_name = func_call.name
            func_args = func_call.args

            params = {}
            for arg in func_args:
                params[arg] = func_args[arg]

            if self.verbose:
                print(f'*** Function call: {func_name=}, {params=}')

            if func_name == FinalAnswerTool.name:
                print(f'Exiting loop after {idx + 1} runs because the final answer was found!')
                break
            elif func_name == '':
                print('* An error occurred: an empty function name was generated! Exiting...')
                break

            action_output = self.tools_by_name[func_name].use(params)

            if self.verbose:
                print(f'*** Output of the function call: {action_output}')

            prompt += '\nPrevious output:\n' + str(response.candidates[0].content.parts[0])
            # prompt += f'\nPreviously used tool: {func_name}\nOutput of the previous action:\n{action_output}'


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
    #     ' Save it in a file called test_demo.py. Execute the code and display the results.'
    #     ' All source code and other files should be created inside the `test_demo` directory.'
    # )

    # Example 4: a more detailed prompt
    # Here, no explicit directory creation is suggested. However, the LLM sometimes creates
    # a new dir while interpreting 'Python project' in the prompt. This behavior is not
    # guaranteed. So, a side effect is that some existing files may get overwritten!
    text = (
        'The `inputs.txt` file contains a list of natural numbers, one in each line.'
        ' Create a Python project to read each such number and determine whether or not it is a prime number.'
        ' The output should be `Prime` or `Not prime`, written in a separate file.'
        ' Create a separate module that checks whether or not the numbers belong to Fibonacci sequence.'
        ' For this, the output should be `Fibonacci` or `Not Fibonacci`, written in another file.'
        ' All functions and modules should have appropriate docstrings.'
        ' Also, add a README.md file for the project.'
        ' Finally, execute the code and verify that everything is working fine.'
    )

    assistant = Assistant(
        tools=[CodeExecutionTool, WriteFileTool, FinalAnswerTool, MakeDirectoryTool, ]
    )
    assistant.run(text.strip())
