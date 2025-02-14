import requests
import os

API_KEY = os.getenv("DEEP_API_KEY")
BASE_URL = 'https://api.lkeap.cloud.tencent.com/v1/chat/completions'


def parse_response(response):
    """
    解析 API 的返回结果，移除首尾两行。
    """
    lines = response.strip().split('\n')
    if len(lines) > 2:
        lines.pop(0)  # 移除第一行
        lines.pop()  # 移除最后一行
    return '\n'.join(lines).strip()


def call_ai_api(prompt, model='deepseek-r1'):
    print("-" * 50)
    if not API_KEY:
        raise ValueError("DEEP_API_KEY 未配置")
    print("prompt:", prompt)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'stream': False
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()

        if not result.get('choices') or len(result['choices']) == 0:
            raise ValueError('AI 服务返回结果为空')

        # 打印 reasoning_content （如果存在）
        # reasoning_content = result['choices'][0]['message'].get('reasoning_content')
        # if reasoning_content:
        #     print("deepseek reasoning_content:", reasoning_content)

        # return result['choices'][0]['message']['content']
        return result['choices'][0]['message']

    except requests.exceptions.HTTPError as e:
        try:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', response.reason)
        except:
            error_message = response.reason
        raise Exception(f"腾讯云 API 错误: {response.status_code} - {error_message}") from e
    except Exception as e:
        print("调用 DeepAI 时发生错误:", e)
        raise
