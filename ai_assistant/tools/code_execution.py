import os
import subprocess
import sys
from typing import Dict

from vertexai.preview.generative_models import FunctionDeclaration

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

        try:
            response = subprocess.run(
                [sys.executable, file_name],
                shell=False,
                capture_output=True,
                text=True,
                cwd=cwd
            )

            if response.returncode != 0:
                return response.stderr

            return response.stdout

        except Exception as ex:
            return f'* Error:: Failed to run the program with file {file_name} because of the following error: {ex}'
