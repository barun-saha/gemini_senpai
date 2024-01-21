from ai_assistant.assistant import Assistant
from ai_assistant.tools.base import FinalAnswerTool
from ai_assistant.tools.code_execution import CodeExecutionTool
from ai_assistant.tools.file_system import WriteFileTool, MakeDirectoryTool


def main():
    """
    Define prompts describing the tasks. Invoke an assistant to get the jobs done.
    """

    # # Example 1: simple prompt, no file name
    # prompt = '''
    # Write Python code to display the current date. Also, find out tomorrow's date.
    # '''

    # # Example 2: simple prompt with a file name
    # prompt = (
    #     'Write a Python program to print the current date and time.'
    #     ' Save it in a file called test_demo.py. Execute the code and display the results.'
    # )

    # # Example 3
    # # This prompt asks to create a file in a directory
    # prompt = (
    #     'Write a Python program to print the current date and time.'
    #     ' Based on the day of the month, print all the natural numbers up to it.'
    #     ' Save the code in a file called test_demo.py. Execute the code and display the results.'
    #     ' All source code and other files should be created inside the `test_demo` directory.'
    # )

    # # Example 4: a more detailed prompt -- This does NOT work because of runtime errors
    # # The likely reason is that the response is being blocked.
    # # Here, no explicit directory creation is suggested. However, the LLM sometimes creates
    # # a new dir while interpreting 'Python project' in the prompt. This behavior is not
    # # guaranteed. So, a side effect is that some existing files may get overwritten!
    # prompt = (
    #     'The `inputs.txt` file containing a list of natural numbers, one in each line.'
    #     ' Create a Python project to read each such number and determine whether or not it is a prime number.'
    #     ' The output should be `Prime` or `Not prime`, written in a separate file.'
    #     ' Create a separate module that checks whether or not the numbers belong to Fibonacci sequence.'
    #     ' For this, the output should be `Fibonacci` or `Not Fibonacci`, written in another file.'
    #     ' All functions and modules should have appropriate docstrings.'
    #     ' Also, add a README.md file for the project.'
    #     ' Finally, execute the code and verify that everything is working fine.'
    # )

    # Example 5: build a website
    prompt = (
        'Background:\n'
        'John M. Doe is a scientist with Alien Institute of Artificial Intelligence.'
        ' He has five years of experience in the areas of NLP and computer vision.'
        ' He has worked with several AI frameworks. John has published several research papers.'
        ' John is also an avid photographer. He has captured several images of UFOs around the world.'
        ' He was also a winner in the Best Annual Alien Silhouette Photography Competition.'
        '\n\nTasks:'
        '\nCreate a personal website for John. The website should use Bootstrap 5 as the CSS framework.'
        ' Create a separate page for each of the following sections: about, research, and hobbies.'
        ' Generate additional relevant content for each page based on the background provided.'
        ' Create an impressive 200-words biography of John. Create some research projects.'
        ' There should be a navigation bar at the top.'
        ' Ensure that all the pages are linked correctly from every other page.'
        ' The color theme should be primarily white with a dash of violet.'
        ' The footer should contain copyright notice and social media links.'
        ' All the files should be created inside a directory called `personal_website`.'
        ' When including CSS scripts from CDNs, do not add the integrity check.'
        ' Make sure that all code are correct and content properly formatted. There should be no broken links.'
    )

    assistant = Assistant(
        tools=[CodeExecutionTool, WriteFileTool, FinalAnswerTool, MakeDirectoryTool, ]
    )
    assistant.run(prompt.strip())


if __name__ == '__main__':
    main()
