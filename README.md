# Overall


This repository contains the full implementation of **SHARE-RAG**, an adaptive, retrieval-augmented generation (RAG) framework designed to assist Large Language Models (LLMs) in accurately localizing logical and structural faults in novice-written programs. 

## 1.Requirements
Locate the requirements.txt file in the root directory and execute the following dependency command.
```bash
pip install -r requirements.txt
```
Should there be any additional dependencies missing, feel free to sequentially import them using pip based on the provided information.

## 2.LLMs
In this study, multiple different LLMs were used for experimentation, namely GPT-5.1, Gemini-2.5-Flash-Lite, Glm-4.7, Llama-3.3-70b-instruct, Qwen3-1.7b, DeepSeek-v3.2, Kimi-k2-instruct-0905, Minimax-m2, Phi-4-multimodal-instruct, and Gemma-3n-e4b-it.

Among these, Llama-3.3-70b-instruct, Qwen3-1.7b, DeepSeek-v3.2, Kimi-k2-instruct-0905, Minimax-m2, Phi-4-multimodal-instruct, and Gemma-3n-e4b-it are open-source LLMs that can be deployed following their respective official documentation. The versions used and their corresponding official website links are provided below:

| Model Name | URL |
| :--- | :--- |
| **Llama-3.3-70b-instruct** | [https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct) |
| **Qwen3-1.7b** | [https://huggingface.co/Qwen]([https://huggingface.co/Qwen](https://huggingface.co/Qwen/Qwen3-1.7B)) |
| **DeepSeek-v3.2** | [https://github.com/deepseek-ai/DeepSeek-V3]([https://github.com/deepseek-ai/DeepSeek-V3](https://huggingface.co/deepseek-ai/DeepSeek-V3.2)) |
| **Kimi-k2-instruct-0905** | [https://platform.moonshot.cn/]([https://platform.moonshot.cn/](https://huggingface.co/moonshotai/Kimi-K2-Instruct-0905)) |
| **Minimax-m2** | [https://huggingface.co/minimax]([https://huggingface.co/minimax](https://huggingface.co/MiniMaxAI/MiniMax-M2)) |
| **Phi-4-multimodal-instruct** | [https://huggingface.co/microsoft/phi-4]([https://huggingface.co/microsoft/phi-4](https://huggingface.co/microsoft/Phi-4-multimodal-instruct)) |
| **Gemma-3n-e4b-it** | [https://huggingface.co/google/gemma-3]([https://huggingface.co/google/gemma-3](https://huggingface.co/google/gemma-3n-E4B-it)) |
