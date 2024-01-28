import os
from typing import Dict

import requests
from vertexai.preview.generative_models import FunctionDeclaration

from ai_assistant.tools.base import ToolInterface
from ai_assistant.tools.file_system import MakeDirectoryTool


class DownloadFileTool(ToolInterface):
    name: str = 'DownloadFileTool'
    description: str = (
        'Use only when you need to download a file from the Internet.'
        ' Returns the file download status or error message.'
    )
    function_declaration: FunctionDeclaration = FunctionDeclaration(
        name=name,
        description=description,
        parameters={
            'type': 'object',
            'properties': {
                'url': {
                    'type': 'string', 'description': 'URL of the file'
                },
                'file_name': {
                    'type': 'string', 'description': 'The name of the file used to save on the disk'
                },
            },
        },
    )

    @staticmethod
    def use(params: Dict[str, str]) -> str:
        url = params['url'].strip()
        file_name = params['file_name'].strip()

        try:
            dir_name = os.path.dirname(file_name)
            if dir_name:
                MakeDirectoryTool.use({'dir_name': dir_name})

            response = requests.get(url, timeout=15)
            # Check if the request was successful
            if response.status_code == 200:
                # Open the file in write mode
                with open(file_name, 'wb') as file:
                    # Write the contents of the response to the file
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            file.write(chunk)

                return f'Successfully downloaded the file and saved it as: {file_name}'
            # Else
            return f'* Error:: Failed to download file {url}. HTTP response code: {response.status_code}'
        except requests.exceptions.Timeout:
            return f'* Error: The request timed out for {url}'
        except Exception as ex:
            return f'* Error:: Failed to download {url} because of the following error: {ex}'
