# import os
# import subprocess
#
# from llm_agents.tools.base import ToolInterface
#
#
# class CodeExecutionTool(ToolInterface):
#     """
#     A tool to create a file.
#     """
#
#     name: str = 'CodeExecutionTool'
#     description: str = (
#         'Use only when you need to run Python program, identified with a file name.'
#         ' The file must be existing in the filesystem or need to be created before execution.'
#     )
#
#     def use(self, input_text: str) -> str:
#         """
#         Run a program with a given file name.
#
#         :param input_text: The name of the file containing code.
#         :return: The code execution output or error.
#         """
#
#         # Does the path also contains a directory?
#         # If so, set the current working directory
#         input_text = input_text.strip()
#         try:
#             cwd, file_name = os.path.dirname(input_text), os.path.basename(input_text)
#         except Exception as ex:
#             print(ex)
#             cwd, file_name = None, input_text
#
#         response = subprocess.run(
#             ['python', file_name],
#             shell=False,
#             capture_output=True,
#             text=True,
#             cwd=cwd
#         )
#
#         if response.returncode != 0:
#             return response.stderr
#         else:
#             return response.stdout
#
#
# if __name__ == '__main__':
#     import tempfile
#     from llm_agents.tools.base import ToolInterface
#     from llm_agents.tools.file_system import WriteFileTool, ReadFileTool
#
#     file_create_tool = WriteFileTool()
#     read_file_tool = ReadFileTool()
#     _, tmp_file_name = tempfile.mkstemp(dir='.')
#
#     with open(tmp_file_name, 'w') as tmp_file:
#         print(f'{tmp_file.name=}')
#         tmp_file_name = tmp_file.name
#         code = '''import time
# print(time.time())'''
#         text = f'''<NAME>{tmp_file_name}</NAME><CONTENT>{code}</CONTENT>'''
#         result = file_create_tool.use(text)
#         print(result)
#
#     result = read_file_tool.use(tmp_file_name)
#     print(result)
#
#     result = CodeExecutionTool().use(tmp_file_name)
#     print(result)
import os
import subprocess
from typing import Dict

from vertexai.preview.generative_models import FunctionDeclaration, Tool

from ai_assistant.tools.base import ToolInterface


class CodeExecutionTool(ToolInterface):
    name: str = 'CodeExecutionTool'
    description: str = (
        'Use only when you need to run Python program, identified with a file name.'
        ' The file must be existing in the filesystem or need to be created before execution.'
    )
    function_declaration: FunctionDeclaration = FunctionDeclaration(
        name=name,
        description=description,
        parameters={
            'type': 'object',
            'properties': {
                'file_name': {
                    'type': 'string',
                    'description': (
                        'Name or path of the Python source code file to be executed.'
                        ' This must not contain any space.'
                    )
                }
            },
        },
    )

    @staticmethod
    def use(params: Dict[str, str]) -> str:
        # Does the path also contains a directory?
        # If so, set the current working directory
        input_text = params['file_name'].strip()
        try:
            cwd, file_name = os.path.dirname(input_text) or None, os.path.basename(input_text)
        except Exception as ex:
            print(ex)
            cwd, file_name = None, input_text

        print(f'{cwd=}, {file_name=}')

        try:
            response = subprocess.run(
                ['python', file_name],
                shell=False,
                capture_output=True,
                text=True,
                cwd=cwd
            )

            if response.returncode != 0:
                return response.stderr
            else:
                return response.stdout
        except Exception as ex:
            return f'* Error:: Failed to run the program with file {file_name} because of the following error: {ex}'
