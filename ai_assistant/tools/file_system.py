import io
import os
import re

from pylint.lint import Run
from typing import Dict
from pylint.reporters.text import TextReporter
from vertexai.preview.generative_models import FunctionDeclaration

from ai_assistant.tools.base import ToolInterface


class WriteFileTool(ToolInterface):
    name: str = 'WriteFileTool'
    description: str = (
        'Use only when you need to create, write, or append to a file with a given name and content.'
        ' Returns the file writing status. In case of .py files, it also returns the result of Pylint scan.'
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
                'file_write_mode': {
                    'type': 'string',
                    'description': 'File writing modes: `w` for write; `a` for append'
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
        if 'file_name' not in params:
            return (
                '* Error: The `file_name` key is missing!'
                ' Please use the function based on the description provided.'
            )
        if 'content' not in params:
            return (
                '* Error: The `content` key is missing!'
                ' Please use the function based on the description provided.'
            )
        if 'file_write_mode' not in params:
            return (
                '* Error: The `file_write_mode` key is missing!'
                ' Please use the function based on the description provided.'
            )

        file_name = params['file_name'].strip()
        content = params['content'].strip()
        mode = params['file_write_mode'].strip()
        # Courtesy: ChatGPT
        file_extension = file_name.split('.')[-1]
        content = content.encode().decode('unicode_escape')

        if file_extension and file_extension == 'py':
            content = WriteFileTool.fix_fstring_expressions(content)

        if mode not in ('w', 'a'):
            return (
                f'* Error:: Failed to write to file {file_name} because an incorrect file open mode is specified: {mode}.'
                f' The supported file opening modes are: "w" for write; "a" for append.'
            )

        try:
            with open(file_name, 'w', encoding='utf-8') as out_file:
                out_file.write(content)

            msg = f'Successfully wrote to the file: {file_name}'

            # Perform a static analysis of Python code to catch early errors
            # often arising due to wrong formatting or encoding
            if file_extension and file_extension == 'py':
                pylint_output = io.StringIO()  # Custom open stream
                reporter = TextReporter(pylint_output)
                Run(['--errors-only', file_name], reporter=reporter, exit=False)
                result = pylint_output.getvalue()
                msg = '\n'.join([
                    msg,
                    f'Pylint static analysis result for {file_name} --'
                    f' please regenerate the code if there is any error:',
                    result
                ])

                print(f'Pylint result for {file_name}: {result}')

            return msg
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


class ListDirectoryTool(ToolInterface):
    name: str = 'ListDirectoryTool'
    description: str = (
        'Use only when you need to list the contents of a directory.'
        ' Returns the names of files and subdirectories, each separated by a newline.'
    )
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
            items = os.listdir(dir_name)
            return '\n'.join(items)
        except NotADirectoryError as nde:
            return f'* Error:: {dir_name} is not a directory. Use this tool only with a directory: {nde}'
        except Exception as ex:
            return f'* Error:: Failed to fetch the contents of dir {dir_name} because of the following error: {ex}'

