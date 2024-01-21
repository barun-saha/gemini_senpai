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
        )
        self.max_steps: int = 15
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
            # vertexai.generative_models._generative_models.ResponseBlockedError: The response was blocked.

            if response.candidates[0].finish_reason == 'SAFETY':
                print(f'*** Execution stopped because of SAFETY reasons')
                break

            # print(response.candidates[0].content.parts[0])
            print('-' * 20)

            func_call = response.candidates[0].content.parts[0].function_call
            func_name = func_call.name
            func_args = func_call.args

            if func_name == '' or func_name is None or func_args is None:
                prompt = (
                    f'Incorrect choice generated:: {func_name=}, {func_args=}.'
                    f' Please generate a valid function choice based on the following:'
                    f'\n{self.tools}'
                )
                continue

            params = {}
            for arg in func_args:
                params[arg] = func_args[arg]

            if self.verbose:
                print(f'*** Function call: {func_name=}, {params=}')

            if func_name == FinalAnswerTool.name:
                print(f'Exiting loop after {idx + 1} runs because the final answer was found!')
                print(params['answer'])
                break

            action_output = self.tools_by_name[func_name].use(params)

            if self.verbose:
                print(f'*** Output of the function call: {action_output}')

            prompt = f'\nPreviously used tool: {func_name}\nOutput of the previous action: {action_output}'
