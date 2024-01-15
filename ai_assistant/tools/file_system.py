import os
from typing import Dict
from vertexai.preview.generative_models import FunctionDeclaration, Tool

from ai_assistant.tools.base import ToolInterface


class WriteFileTool(ToolInterface):
    name: str = 'WriteFileTool'
    description: str = (
        'Use only when you need to create or write to a file with a given name and content.'
        ' Returns the file creation status.'
    )
    function_declaration: FunctionDeclaration = FunctionDeclaration(
        name=name,
        description=description,
        parameters={
            'type': 'object',
            'properties': {
                'file_name': {
                    'type': 'string', 'description': 'Name of the file'
                },
                'content': {
                    'type': 'string', 'description': 'Content of the file'
                }
            },
        },
    )

    @staticmethod
    def use(params: Dict[str, str]) -> str:
        file_name = params['file_name'].strip()
        content = params['content'].strip().replace('\\n', '\n')

        try:
            with open(file_name, 'w') as out_file:
                out_file.write(content)

            return f'Successfully created the file {file_name} using {WriteFileTool.name}'
        except Exception as ex:
            return f'* Error:: Failed to write to the file {file_name} because of the following error: {ex}'


class ReadFileTool(ToolInterface):
    name: str = 'ReadFileTool'
    description: str = (
        'Use only when you need to read from a file with a given.'
        ' Returns the file content or error message.'
    )
    function_declaration: FunctionDeclaration = FunctionDeclaration(
        name=name,
        description=description,
        parameters={
            'type': 'object',
            'properties': {
                'file_name': {
                    'type': 'string', 'description': 'Name of the file'
                },
            },
        },
    )

    @staticmethod
    def use(params: Dict[str, str]) -> str:
        file_name = params['file_name'].strip()

        try:
            with open(file_name, 'r') as in_file:
                return in_file.read()
        except Exception as ex:
            return f'* Error:: Failed to read from the file {file_name} because of the following error: {ex}'


class MakeDirectoryTool(ToolInterface):
    name: str = 'MakeDirectoryTool'
    description: str = 'Use only when you need to create a directory. Returns the dir creation status.'
    function_declaration: FunctionDeclaration = FunctionDeclaration(
        name=name,
        description=description,
        parameters={
            'type': 'object',
            'properties': {
                'dir_name': {
                    'type': 'string', 'description': 'Name of the directory (must not contain any space)'
                },
            },
        },
    )

    @staticmethod
    def use(params: Dict[str, str]) -> str:
        dir_name = params['dir_name'].strip()

        try:
            os.mkdir(dir_name)
            return f'Successfully created the directory {dir_name} using {MakeDirectoryTool.name}'
        except Exception as ex:
            return f'* Error:: Failed to write to the file {dir_name} because of the following error: {ex}'

