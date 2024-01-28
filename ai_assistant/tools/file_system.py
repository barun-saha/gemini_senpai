import codecs
import io
import os
import re

from typing import Dict
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from vertexai.preview.generative_models import FunctionDeclaration

from ai_assistant.tools.base import ToolInterface


class WriteFileTool(ToolInterface):
    name: str = 'WriteFileTool'
    description: str = (
        'Use only when you need to create, write, or append to a file with a given name and content.'
        ' Returns the file writing status. In case of .py files, it also returns Pylint errors if found.'
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
    def fix_fstring_expressions(content) -> str:
        """
        Try and fix potential mismatch in quotes inside f-strings.
        Courtesy: Bing Copilot

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
            # Else
            # Replace double quotes with single quotes and escape existing single quotes
            print('Replacing 2:', "f'" + s[2:-1].replace("'", "\\'") + "'")
            return "f'" + s[2:-1].replace("'", "\\'") + "'"

        # Replace f-string expressions in the content
        return re.sub(pattern, replacer, content)

    @staticmethod
    def decode_until_no_escaped_newlines(text) -> str:
        """
        Perform repeated unicode decoding to potentially handle long escape sequences.
        This usually works but sometimes may break source code.

        :param text: The text.
        :return: The text with escape sequences decoded.
        """

        # This pattern matches an escaped newline sequence that is not preceded by a backslash
        # pattern = re.compile(r'(?<!\\)\\n')
        #
        # while re.search(pattern, text):
        #     text = codecs.decode(text, 'unicode_escape')

        old_text = text

        # Try at most 10 times -- even a lower value should be sufficient
        for _ in range(10):
            text = codecs.decode(text, 'unicode_escape')
            if text == old_text:
                break
            old_text = text

        return text

    @staticmethod
    def run_code_lint(file_name: str) -> str:
        """
        Run Pylint on a .py file.

        :param file_name: The source file name.
        :return: The result of Pylint scan.
        """

        pylint_output = io.StringIO()
        reporter = TextReporter(pylint_output)
        Run(['--errors-only', file_name], reporter=reporter, exit=False)
        result = pylint_output.getvalue()
        return result

    @staticmethod
    def fix_unterminated_string_literal(file_name: str, line_number: int, col_number: int):
        """
        Try to fix the unterminated string literal error from Pylint
        by replacing a newline with the \\n escape sequence.

        :param file_name: The file to fix.
        :param line_number: The line number in error.
        :param col_number: The character position in the line.
        """

        with open(file_name, 'r+', encoding='utf-8') as in_file:
            lines = in_file.readlines()
            lines[line_number - 1] = (
                    lines[line_number - 1][:col_number] + '\\n' + lines[line_number - 1][col_number + 1:]
            )
            in_file.seek(0)
            in_file.writelines(lines)
            in_file.truncate()

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
        file_extension = file_name.split('.')[-1]

        # The problem:
        # Gemini may generate content with arbitrary number of escape sequences, e.g., \\\\n
        # These lead to syntax error in code. Such code cannot be executed.
        # The idea here is to decode all escape sequences until any is left.
        # This usually works but can lead to another problem: when a string contains
        # a newline literal ('\n'), it can get replaced with an actual newline, which
        # again would lead to syntax error. At this point the applications asks Gemini
        # to regenerate correct code or hopes the user would fix it!
        # The `decode_until_no_escaped_newlines` with regex-based implementation is generated by Bing Copilot.
        # Said implementation has been replaced with a finite loop.
        # TODO: Investigate this problem again in the future for a hopefully better solution
        content = WriteFileTool.decode_until_no_escaped_newlines(content)

        if file_extension and file_extension == 'py':
            content = WriteFileTool.fix_fstring_expressions(content)

        if mode not in ('w', 'a'):
            return (
                f'* Error:: Failed to write to file {file_name} because'
                f' an incorrect file open mode is specified: {mode}.'
                f' The supported file opening modes are: "w" for write; "a" for append.'
            )

        try:
            dir_name = os.path.dirname(file_name)
            if dir_name:
                MakeDirectoryTool.use({'dir_name': dir_name})

            with open(file_name, mode, encoding='utf-8') as out_file:
                out_file.write(content)

            msg = f'Successfully wrote to the file: {file_name}'

            # Perform a static analysis of Python code to catch early errors
            # often arising due to wrong formatting or encoding
            if file_extension and file_extension == 'py':
                # Run in a loop and try to fix all potential errors because of string split into two lines
                while True:
                    result = WriteFileTool.run_code_lint(file_name).strip()

                    if result:
                        # Try to fix the unterminated string literal errors
                        pattern = r"(\d+):(\d+): E0001: Parsing failed: 'unterminated string literal"
                        match = re.search(pattern, result, re.UNICODE | re.DOTALL)

                        if match:
                            # Extract the line number and column number from the match
                            line_number = int(match.group(1))
                            column_number = int(match.group(2))
                            WriteFileTool.fix_unterminated_string_literal(file_name, line_number, column_number)
                        else:  # Do not try to fix any other kind of error
                            break
                    else:  # Empty result -- no error
                        break

                with open(file_name, 'r', encoding='utf-8') as in_file:
                    code = in_file.read().strip()

                if result:
                    msg = '\n'.join([
                        msg,
                        f'Pylint throws the following error for {file_name}:\n',
                        result,
                        '\nPlease regenerate the code to fix the error. The concerned code is:',
                        code
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
            with open(file_name, 'r', encoding='utf-8') as in_file:
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
            if not os.path.exists(dir_name):
                os.mkdir(dir_name)
                return f'Successfully created the directory: {dir_name}'

            return f'Directory {dir_name} already exists: this action is complete'
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
