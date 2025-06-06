import requests
import os

API_KEY = os.getenv("DEEP_API_KEY")
BASE_URL = 'https://api.siliconflow.cn/v1/chat/completions'


def call_ai_api(prompt, model='deepseek-ai/DeepSeek-R1'):
    print("-" * 50)
    if not API_KEY:
        raise ValueError("DEEP_API_KEY 未配置")
    # print("prompt:", prompt)
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
        # print("deepseek result:", result['choices'])
        return result['choices'][0]['message']

    except requests.exceptions.HTTPError as e:
        try:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', response.reason)
        except:
            error_message = response.reason
        raise Exception(f"大模型 API 错误: {response.status_code} - {error_message}") from e
    except Exception as e:
        print("调用 DeepAI 时发生错误:", e)
        raise
