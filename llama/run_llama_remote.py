import requests, time, re, replicate
import pandas as pd

headers = {
    'Content-Type': 'text/plain'
}
replicate = replicate.Client(api_token='r8_8taKlPQzi3Liw2179bZKZZE7pbRlfS50dSisN')
POST_PATTERN = re.compile(r'Body="([^"]*)"')

def unscape_tags(match):
    output = []
    if match:
        tags_value = match.group(1)
        tags_unescaped = re.sub(r'&lt;', '<', re.sub(r'&gt;', '>', tags_value))
        output.append(tags_unescaped)
    return output

url = "https://www.llama2.ai/api"

def wrap_request_and_send(bugreport):
    match = POST_PATTERN.search(bugreport)
    unscapePost = unscape_tags(match)
    prompt = f"""Your duty is extract meaningful keywords related to GPU errors in the given input data. Input data:{unscapePost[0]}. 
    REMEMBER: Do not explain the bug, just extract some keywords. 
    REMEMBER: If you can not extract any keywords, just skip to answer. 
    Please generate the keywords as the following format: Keywords: Generated Keywords."""

    payload ="{\"prompt\":\"[INST] PROMPT [/INST]\\n\",\"model\":\"meta/llama-2-70b-chat\",\"systemPrompt\":\"You are a helpful assistant.\",\"temperature\":0.5,\"topP\":0.9,\"maxTokens\":500,\"image\":null,\"audio\":null}"
    payload = payload.replace("PROMPT",  prompt)

    # time.sleep(2)
    response = requests.request("POST", url, headers=headers, data=payload).text
    return response

def run_replicate():
    output = replicate.run(
    "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
    input={
        "prompt": "Can you write a poem about open source machine learning? Let's make it in the style of E. E. Cummings.",
        "system_prompt": "You are a helpful, respectful and honest assistant.",
    }
    )
    return output

def parser():
    data = pd.read_csv('output/posts/stage1/stage1_device.csv', sep=',', encoding='utf-8')
    for idx, row in data.iterrows():
        output = wrap_request_and_send(row.iloc[1])
        print(output)

if __name__ == '__main__':
    parser()

