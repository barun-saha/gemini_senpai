from ai_assistant.assistant import Assistant
from ai_assistant.tools.base import FinalAnswerTool
from ai_assistant.tools.file_system import WriteFileTool, MakeDirectoryTool
from ai_assistant.tools.code_execution import CodeExecutionTool
# from ai_assistant.tools.web_tools import DownloadFileTool


def main():
    """
    Create an assistant. Provide it with a set of tools. Then run it.
    The prompt file to use is specified in `settings.toml`.
    """

    assistant = Assistant(
        tools=[WriteFileTool, CodeExecutionTool, FinalAnswerTool, MakeDirectoryTool, ],
        verbose=False
    )
    assistant.run()


if __name__ == '__main__':
    main()
