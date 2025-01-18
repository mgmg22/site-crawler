import requests
import os
from dotenv import load_dotenv
import json
import time
import datetime
from pathlib import Path

load_dotenv()
TG_Bot_Token = os.getenv('TG_BOT_TOKEN')
TG_Chat_ID = os.getenv('TG_CHAT_ID')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
CLOUDFLARE_NAMESPACE_ID = os.getenv('CLOUDFLARE_NAMESPACE_ID')


def upload_file(file_path):
    file_path = Path(file_path).resolve()

    if not file_path.exists():
        return {'error': f'文件不存在: {file_path}'}
    if not TG_Chat_ID:
        return {'error': 'TG_Chat_ID 未设置'}
    with open(file_path, 'rb') as upload_file:
        file_extension = file_path.suffix.lower()
        telegram_files = {
            'photo': upload_file
        }
        telegram_data = {
            'chat_id': TG_Chat_ID
        }
        api_url = f'https://api.telegram.org/bot{TG_Bot_Token}/sendPhoto'
        response = requests.post(api_url, files=telegram_files, data=telegram_data)

    if response.status_code != 200:
        return {'error': response.json().get('description', '上传到 Telegram 失败')}

    response_data = response.json()
    file_id = get_file_id(response_data)
    if not file_id:
        return {'error': '获取文件 ID 失败'}
    return {'src': f'{file_id}{file_extension}'}


def get_file_id(response):
    if not response.get('ok') or not response.get('result'):
        return None
    if 'photo' in response['result']:
        return max(response['result']['photo'], key=lambda x: x['file_size'])['file_id']
    return None


def write_to_cloudflare_kv(key, value):
    api_url = f'https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/storage/kv/namespaces/{CLOUDFLARE_NAMESPACE_ID}/values/{key}'
    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
    }
    metadata = {
        "CurrentDateTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Label": "None",
        "ListType": "None",
        "TimeStamp": int(time.time() * 1000),
        "liked": True
    }
    files = {
        'value': (None, value),
        'metadata': json.dumps(metadata)
    }
    try:
        response = requests.put(api_url, headers=headers, files=files)
        print(response.json())
        response.raise_for_status()
        return {'success': True}
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to write to Cloudflare KV: {e}'}


def read_kv_keys():
    api_url = f'https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/storage/kv/namespaces/{CLOUDFLARE_NAMESPACE_ID}/keys'
    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
    }
    try:
        response = requests.get(api_url, headers=headers)
        data = response.json()
        for item in data["result"]:
            print(f"Name: {item['name']}, Metadata: {item.get('metadata', 'No metadata')}")
        response.raise_for_status()
        return {'success': True}
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to write to Cloudflare KV: {e}'}
