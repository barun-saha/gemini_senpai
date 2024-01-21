# Gemini Senpai

*Build your software with AI assistant, collaboratively*



## Overview
Agents (autonomous agents or LLM agents) extend the capability of LLMs by equipping them with tools, which essentially are functions defined to achieve specific tasks. Google's Gemini has introduced support for function calling, much like OpenAI's GPT, allowing the Generative AI models support advanced workflows.

Gemini Senpai is a small, experimental AI assistant prototype built using Gemini's function calling. Currently, Gemini Senpai allows users to generate Python code and small Python applications spanning multiple modules.



## Usage

Gemini Senpai uses Google's [Vertex AI](https://cloud.google.com/vertex-ai?hl=en) to access the Gemini Pro LLM. You need to have a [Google Cloud account and Vertex AI setup](https://cloud.google.com/vertex-ai/docs/start/cloud-environment) together with authentication. Please have a look at the ["Quick Start"](https://pypi.org/project/google-cloud-aiplatform/) section and follow the steps. The use of Gemini via AI Studio (i.e., using API keys) is not yet supported.

You should verify from your terminal that Google Cloud authentication is working before proceeding further.

Get the source code of Gemini Senpai from GitHub:

```bash
git clone git@github.com:barun-saha/gemini_senpai.git
```

Install the requirements:

```bash
cd gemini_senpai
pip install -r requirements.txt
```

Run the assistant:

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