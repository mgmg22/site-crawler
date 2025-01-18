import requests
import os
from dotenv import load_dotenv
import json
import time
import datetime

load_dotenv()
TG_Bot_Token = os.getenv('TG_BOT_TOKEN')
TG_Chat_ID = os.getenv('TG_CHAT_ID')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
CLOUDFLARE_NAMESPACE_ID = os.getenv('CLOUDFLARE_NAMESPACE_ID')


def upload_file(file_path):
    if not os.path.exists(file_path):
        return {'error': 'No file uploaded'}

    if not TG_Chat_ID:
        return {'error': 'TG_Chat_ID is empty'}
    with open(file_path, 'rb') as upload_file:
        file_extension = os.path.splitext(file_path)[1].lower()
        telegram_files = {
            'photo': upload_file
        }
        telegram_data = {
            'chat_id': TG_Chat_ID
        }
        api_url = f'https://api.telegram.org/bot{TG_Bot_Token}/sendPhoto'
        response = requests.post(api_url, files=telegram_files, data=telegram_data)

    if response.status_code != 200:
        return {'error': response.json().get('description', 'Upload to Telegram failed')}

    response_data = response.json()
    file_id = get_file_id(response_data)
    if not file_id:
        return {'error': 'Failed to get file ID'}
    return {'src': f'{file_id}{file_extension}'}


def get_file_id(response):
    if not response.get('ok') or not response.get('result'):
        return None
    if 'photo' in response['result']:
        return max(response['result']['photo'], key=lambda x: x['file_size'])['file_id']
    return None


def write_to_cloudflare_kv(key, value, metadata=None):
    api_url = f'https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/storage/kv/namespaces/{CLOUDFLARE_NAMESPACE_ID}/values/{key}'
    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
    }
    metadata_str = json.dumps(metadata) if metadata else None
    files = {
        'value': (None, value),
        'metadata': (None, metadata_str) if metadata_str else None
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


if __name__ == '__main__':
    site_name = "www-yeschat-ai"
    result = upload_file(f'screenshots/{site_name}.png')
    print(result)
    if "src" in result:
        key = result["src"]
        metadata = {
            "CurrentDateTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Label": "None",
            "ListType": "None",
            "TimeStamp": int(time.time() * 1000),
            "liked": True
        }
        write_to_cloudflare_kv(key, site_name, metadata)
        read_kv_keys()
    else:
        print("Error uploading image. Unable to write to KV")
