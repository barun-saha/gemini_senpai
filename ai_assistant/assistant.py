import datetime
import sys
import termcolor as tc
import toml
import vertexai

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


class Assistant:
    COLOR_TEXT = 'green'
    COLOR_DEBUG = 'yellow'
    COLOR_ERROR = 'red'

    SETTINGS_FILE_NAME: str = 'settings.toml'

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
        self.max_steps: int = 15
        self.verbose: bool = verbose
        self.debug: bool = False
        self.model = None
        self.prompt = None
        self.prompt_comment_symbol = '#>#'

        self.configure()

        self.system_prompt: str = (
            f'Today is {get_today()}. You are an AI assistant.'
            ' Answer users questions or help attain the specified objectives as best as you can.'
            ' You have a set of tools to help generate the solution.'
            ' When required, you can use one or more of those tools.'
            ' Plan and solve the problem step-by-step.'
            ' Look at the previous steps, their output, and decide what to do next.'
            f' Accordingly, plan what tool to use from the following: {", ".join(self.tools_by_name.keys())}.'
            ' When all the prior steps are successfully completed'
            ' and you have the final answer for the question available,'
            f' you will call the `{FinalAnswerTool.name}` and do nothing more.'
            ' However, if the action taken in any of the steps results in any error,'
            ' the subsequent steps should try to fix it before reaching the final answer.'
        )

    def configure(self):
        """
        Set some of the configurations of the Assistant and the Gemini Pro LLM.
        """

        try:
            with open(Assistant.SETTINGS_FILE_NAME, 'r', encoding='utf-8') as in_file:
                data = toml.load(in_file)

            if 'Assistant' in data.keys():
                params = data['Assistant']

                if 'verbose' in params:
                    self.verbose = params['verbose']
                if 'debug' in params:
                    self.debug = params['debug']
                if 'max_steps' in params:
                    self.max_steps = params['max_steps']
                if 'prompt_comment_symbol' in params:
                    self.prompt_comment_symbol = params['prompt_comment_symbol']

                if 'prompt_file' in params:
                    try:
                        with open(params['prompt_file'], 'r', encoding='utf-8') as prompt_file:
                            lines = []

                            for line in prompt_file.readlines():
                                line = line.strip()
                                if not line.startswith(self.prompt_comment_symbol):
                                    lines.append(line)

                            self.prompt = '\n'.join(lines)
                    except FileNotFoundError:
                        tc.cprint(
                            f'\n* Error: The prompt file was not found: {params["prompt_file"]}'
                            f'\nExiting...',
                            Assistant.COLOR_ERROR
                        )
                        sys.exit(1)
                    except IOError as ioe:
                        tc.cprint(
                            f'\n* Error: I/O error occurred while reading the prompt file was not found: {ioe}'
                            f'\nExiting...',
                            Assistant.COLOR_ERROR
                        )
                        sys.exit(1)

            model_config = MODEL_CONFIG.copy()

            if 'Gemini' in data.keys():
                params = data['Gemini']

                if 'temperature' in params:
                    model_config['temperature'] = params['temperature']
                if 'max_output_tokens' in params:
                    model_config['max_output_tokens'] = params['max_output_tokens']
                if 'top_k' in params:
                    model_config['top_k'] = params['top_k']
                if 'top_p' in params:
                    model_config['top_p'] = params['top_p']

            self.model = GenerativeModel(
                model_name='gemini-pro',
                generation_config=model_config,
                safety_settings=SAFETY_SETTINGS,
                tools=[self.tools],
            )

            if self.debug:
                tc.cprint(f'Using tools:\n{self.tools}', Assistant.COLOR_DEBUG)
        except FileNotFoundError:
            tc.cprint(
                f'\n* Error: The {Assistant.SETTINGS_FILE_NAME} file ws not found. Will use the default settings.',
                Assistant.COLOR_ERROR
            )
        except Exception as ex:
            msg = (
                f'\n* An exception occurred while reading the {Assistant.SETTINGS_FILE_NAME} file: {ex}.'
                f'\nWill use the default settings.'
            )
            tc.cprint(msg, Assistant.COLOR_ERROR)
        finally:
            if self.model is None:
                self.model = GenerativeModel(
                    model_name='gemini-pro',
                    generation_config=MODEL_CONFIG,
                    safety_settings=SAFETY_SETTINGS,
                    tools=[self.tools],
                )


    @staticmethod
    def get_chat_response(chat_session: ChatSession, prompt: str) -> MultiCandidateTextGenerationResponse:
        """
        Get chat response from Gemini.

        :param chat_session: The ongoing chat session.
        :param prompt: The user prompt.
        :return: The response object.
        """

        response = chat_session.send_message(prompt)
        return response

    def run(self):
        """
        Execute the assistant to solve a specified problem.
        """

        if not self.prompt:
            tc.cprint(
                '\n* Error: The prompt is not set! '
                'Please specify a correct, non-empty prompt file in the settings.'
                '\nExiting...',
                Assistant.COLOR_ERROR
            )
            sys.exit(1)

        print(f'running now for max {self.max_steps} steps')

        # Since Gemini does not allow system prompt/context, mimic to have one
        history = [
            Content(role='user', parts=[Part.from_text(self.system_prompt)]),
            Content(role='model', parts=[
                Part.from_text('Okay. I will follow the instructions and help you achieve the goal.')
            ]),
        ]

        if self.debug:
            tc.cprint(f'Setting chat history to:\n{history}', Assistant.COLOR_DEBUG)

        chat = self.model.start_chat(history=history)
        Assistant.get_chat_response(chat, self.prompt)
        prompt = self.prompt

        for idx in range(self.max_steps):
            msg = f'\n\n>>>>> Step {idx + 1} <<<<<'
            tc.cprint(msg, Assistant.COLOR_TEXT)

            # if self.debug:
            #     tc.cprint(f'>> The chat history so far:\n{chat.history}', Assistant.COLOR_DEBUG)

            print(f'{prompt}')

            try:
                response = Assistant.get_chat_response(chat, prompt)
            except vertexai.generative_models._generative_models.ResponseBlockedError as rbe:
                tc.cprint(
                    f'*** Error while generating a response using Gemini: {rbe}',
                    Assistant.COLOR_ERROR
                )
                tc.cprint('Exiting...please try running again later', Assistant.COLOR_ERROR)
                sys.exit(1)
                # prompt = f'\nOutput based on the previous action: {rbe}'
                # continue

            if response.candidates[0].finish_reason == 'SAFETY':
                msg = '*** Execution stopped because of SAFETY reasons'
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

            params = dict(func_args)

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
