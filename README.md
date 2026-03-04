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
| **Qwen3-1.7b** | [https://huggingface.co/Qwen/Qwen3-1.7B](https://huggingface.co/Qwen/Qwen3-1.7B) |
| **DeepSeek-v3.2** | [https://huggingface.co/deepseek-ai/DeepSeek-V3.2](https://huggingface.co/deepseek-ai/DeepSeek-V3.2) |
| **Kimi-k2-instruct-0905** | [https://huggingface.co/moonshotai/Kimi-K2-Instruct-0905](https://huggingface.co/moonshotai/Kimi-K2-Instruct-0905) |
| **Minimax-m2** | [https://huggingface.co/MiniMaxAI/MiniMax-M2](https://huggingface.co/MiniMaxAI/MiniMax-M2) |
| **Phi-4-multimodal-instruct** | [https://huggingface.co/microsoft/Phi-4-multimodal-instruct](https://huggingface.co/microsoft/Phi-4-multimodal-instruct) |
| **Gemma-3n-e4b-it** | [https://huggingface.co/google/gemma-3n-E4B-it](https://huggingface.co/google/gemma-3n-E4B-it) |

For conducting experiments on commercial LLMs like o1-preview, o3-mini, GPT-4o, GPT-3.5 and Claude3, we utilize the official API interfaces provided.

To standardize our experiments, for all open-source LLMs, we employ the API interfaces in the format of commercial LLMs. Instructions on deploying a commercial LLM form API interface can be found at https://github.com/xusenlinzy/api-for-open-llm.

## 3.Dataset
We conduct our experiments on the TutorCode dataset. For detailed information and access, please refer to: https://github.com/buaabarty/CREF.

## 4.Run
To facilitate experiment reproducibility, we have organized the main code into the share_rag directory. Replicating the experiments only requires attention to this folder.

- Navigate to the **share_rag** directory:

  **Sendpromt** is used to send requests to LLMs and collect results.

  - Within it, the function *send_prompt_openai_gpt* is used for sending requests to GPT. In this function, the *base_url* and *api_key* need to be changed to correspond to the requested link address and key, which can be obtained by purchasing credits on the official website.
  - The *send_prompt_openai_form* function is used for requests to open-source LLMs. Simply modify the request address to the API address of the aforementioned LLM. The key can be filled in arbitrarily.
  - <u>It is advisable to test the Sendpromt requests for successful validation before proceeding to the next step.</u>

*ReadJsonTest* function is utilized to extract the JSON fields from the results returned by the LLM.

*getTokenNumbers* function is employed to extract the token count of the prompt.

*AddLineNumber* is responsible for processing the source code by adding line numbers to each line.

utils1 is employed to implement the retrieval component of RAG.

------

TutorCode-send-gemini, TutorCode-send-glm, etc. are employed to dispatch requests for novice program fault localization in bulk to various LLMs, subsequently storing the resulting data in the 'data' repository. To switch models, simply modify the value of `experiment_model`.

Before execution, certain configurations pertaining to your setup necessitate adjustments. For illustrative purposes, let us consider the instance of *TutorCode-send-glm*:

- The *'prompt_location'* parameter serves to acquire prompts and can be altered to accommodate a custom prompt of your choice.
- The *'run_TutorCode'* function involves traversing the respective datasets once for data retrieval, with the *<u>'root_path'</u>* requiring adjustment to reflect the location where the dataset is stored.
- *'TutorCode_Filter_Data.pkl'* houses the program information filtered from our dataset.
## 5. Evaluate

Navigate to the *"Evaluate"* directory for the code responsible for evaluating the results of the data.

### Accuracy Count

Enter the "Evaluate" directory to calculate the accuracy of each LLM in the 'total_count' file and to assess the accuracy of SBFL and MBFL in the 'sbfl_mbfl_count' file. <u>*Remember to adjust the 'root_path' to the appropriate dataset location before executing*</u>. If utilizing the dataset sources from the previous sections, please be mindful that the dataset locations for open-source LLMs and GPT may differ, so ensure to modify the 'root_path' accordingly.


