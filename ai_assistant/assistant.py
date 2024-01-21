import datetime
import termcolor as tc
from typing import List, Dict

from vertexai.generative_models._generative_models import (
    HarmBlockThreshold,
    HarmCategory,
    Content,
    Part
)
from vertexai.language_models._language_models import MultiCandidateTextGenerationResponse
from vertexai.preview.generative_models import (
    GenerativeModel,
    Tool,
)
from vertexai.preview.language_models import ChatSession

from ai_assistant.tools.base import ToolInterface, FinalAnswerTool


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
    """
    Get today's date in `Month Day, Year` format.

    :return: The date.
    """

    today = datetime.date.today()
    return today.strftime('%B %d, %Y')


class Assistant(object):
    COLOR_TEXT = 'green'
    COLOR_DEBUG = 'yellow'
    COLOR_ERROR = 'red'

    def __init__(self, tools: List[ToolInterface], verbose: bool = True):
        print('Initializing AI Assistant...', end='')

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
        self.verbose: bool = verbose
        self.debug: bool = False

    @staticmethod
    def get_chat_response(chat_session: ChatSession, prompt: str) -> MultiCandidateTextGenerationResponse:
        response = chat_session.send_message(prompt)
        return response

    def run(self, question: str):
        print(f'running now for max {self.max_steps} steps')

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
            msg = f'\n\n>>>>> Step {idx + 1} <<<<<'
            tc.cprint(msg, Assistant.COLOR_TEXT)

            if self.debug:
                tc.cprint(f'>> The chat history so far:\n{chat.history}', Assistant.COLOR_DEBUG)

            print(f'{prompt}')

            # try:
            response = Assistant.get_chat_response(chat, prompt)
            # except google.api_core.exceptions.Unknown as ux:
            #     print(f'*** An unknown exception occurred: {ux}')
            # vertexai.generative_models._generative_models.ResponseBlockedError: The response was blocked.

            if response.candidates[0].finish_reason == 'SAFETY':
                msg = f'*** Execution stopped because of SAFETY reasons'
                tc.cprint(msg, Assistant.COLOR_ERROR)
                break

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
                tc.cprint(f'*** Function call: {func_name=}, {params=}', Assistant.COLOR_TEXT)

            if func_name == FinalAnswerTool.name:
                msg = (
                    f'\nExiting the loop after {idx + 1} runs because the final answer was found:'
                    f'\n\n{params["answer"]}'
                )
                tc.cprint(msg, Assistant.COLOR_TEXT)
                break

            action_output = self.tools_by_name[func_name].use(params)

            if self.verbose:
                tc.cprint(f'*** Output of the function call: {action_output}', Assistant.COLOR_TEXT)

            prompt = f'Previously used tool: {func_name}\nOutput of the previous action: {action_output}'
