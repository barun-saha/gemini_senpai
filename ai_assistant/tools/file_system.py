import os
import re
from typing import Dict
from vertexai.preview.generative_models import FunctionDeclaration

from ai_assistant.tools.base import ToolInterface


class WriteFileTool(ToolInterface):
    name: str = 'WriteFileTool'
    description: str = (
        'Use only when you need to create, write, or append to a file with a given name and content.'
        ' Returns the file writing status.'
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
                },
                'mode': {
                    'type': 'string',
                    'description': 'File writing modes: "w" for write; "a" for append'
                }
            },
        },
    )

    @staticmethod
    def fix_fstring_expressions(content):
        """
        Try and fix potential mismatch in quotes inside f-strings.
        Courtesy: ChatGPT

        :param content: The code.
        :return: The code with f-strings fixed.
        """

        # Regular expression pattern to match f-string expressions
        pattern = r"f'{.*?}'|f\"{.*?}\""

        # Function to replace single quotes with double quotes in f-string expressions
        def replacer(match):
            s = match.group(0)
            if s.startswith("f'"):
                # Replace single quotes with double quotes and escape existing double quotes
                print('Replacing 1:', 'f"' + s[2:-1].replace('"', '\\"') + '"')
                return 'f"' + s[2:-1].replace('"', '\\"') + '"'
            else:
                # Replace double quotes with single quotes and escape existing single quotes
                print('Replacing 2:', "f'" + s[2:-1].replace("'", "\\'") + "'")
                return "f'" + s[2:-1].replace("'", "\\'") + "'"

        # Replace f-string expressions in the content
        return re.sub(pattern, replacer, content)

    @staticmethod
    def use(params: Dict[str, str]) -> str:
        file_name = params['file_name'].strip()
        content = params['content'].strip()
        mode = params['mode'].strip()
        # Courtesy: ChatGPT
        content = WriteFileTool.fix_fstring_expressions(content.encode().decode('unicode_escape'))

        if mode not in ('w', 'a'):
            return (
                f'* Error:: Failed to write to file {file_name} because an incorrect file open mode is specified: {mode}.'
                f' The supported file opening modes are: "w" for write; "a" for append.'
            )

        try:
            with open(file_name, 'w') as out_file:
                out_file.write(content)

            return f'Successfully wrote to the file: {file_name}'
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
            return f'Successfully created the directory: {dir_name}'
        except Exception as ex:
            return f'* Error:: Failed to write to the file {dir_name} because of the following error: {ex}'

