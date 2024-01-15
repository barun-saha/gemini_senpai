from typing import Dict

from vertexai.preview.generative_models import FunctionDeclaration, Tool


class ToolInterface(object):
    """
    An abstract for creating a tool.
    """
    name: str = 'tool-name'
    description: str = 'Description of the tool.'
    function_declaration: FunctionDeclaration = None

    @staticmethod
    def get_tool() -> Tool:
        """
        Get the tool as per Gemini's function calling.

        :return: The tool.
        """

        return Tool(
            function_declarations=[ToolInterface.function_declaration],
        )

    @staticmethod
    def use(params: Dict[str, str]) -> str:
        """
        Make use this tool based on the parameters provided.

        :param params: The parameters to be used for function calling.
        :return: The output of the tool's action.
        """

        raise NotImplementedError('use() method not implemented')  # Implement in subclass


class FinalAnswerTool(ToolInterface):
    name: str = 'FinalAnswerTool'
    description: str = 'Use this when you have the final answer available.'
    function_declaration: FunctionDeclaration = FunctionDeclaration(
        name=name,
        description=description,
        parameters={
            'type': 'object',
            'properties': {
                'answer': {
                    'type': 'string', 'description': 'The final answer'
                },
            },
        },
    )

    @staticmethod
    def use(params: Dict[str, str]) -> str:
        return params['answer']
