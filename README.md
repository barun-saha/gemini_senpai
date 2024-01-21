# Gemini Senpai

*Build your software with AI assistant, collaboratively*



## Overview
Agents (autonomous agents or LLM agents) extend the capability of LLMs by equipping them with tools, which essentially are functions defined to achieve specific tasks. Google's Gemini has introduced support for function calling, much like OpenAI's GPT, allowing the Generative AI models support advanced workflows.

Gemini Senpai is a small, experimental AI assistant prototype built using Gemini's function calling. Currently, Gemini Senpai allows users to generate Python code and small Python applications spanning multiple modules.



## Usage

Get the source code of Gemini Senpai from GitHub:

```bash
git clone git@github.com:barun-saha/gemini_senpai.git
```

Add your prompt and run the assistant:

```bash
python run_assistant.py
```


## Limitations and Known Issues

To be updated.



## Acknowledgement

Gemini Senpai borrows code and ideas from different places, such as:

- [Intelligent agents guided by LLMs](https://www.paepper.com/blog/posts/intelligent-agents-guided-by-llms/) (also, [code](https://github.com/mpaepper/llm_agents))
- [Function Calling with the Vertex AI Gemini API & Python SDK](https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/function-calling/intro_function_calling.ipynb)
- [How to implement a chatbot with ReAct prompting and function calling](https://medium.com/@joanboronatruiz/how-to-implement-a-chatbot-with-react-prompting-and-function-calling-6d9badb2fd3)


-----

<sub>Gemini Senpai is an experimental prototype (read weekend project). No guarantee whatsoever is provided. Use it cautiously after carefully reading the documentation and code.</sub>