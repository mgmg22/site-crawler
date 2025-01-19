import requests
import os
from dotenv import load_dotenv
import json
import time
import datetime
from pathlib import Path
from typing import Dict, Optional

# 在文件顶部一次性加载所有环境变量
load_dotenv()
TG_Bot_Token = os.getenv('TG_BOT_TOKEN')
TG_Chat_ID = os.getenv('TG_CHAT_ID')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
CLOUDFLARE_NAMESPACE_ID = os.getenv('CLOUDFLARE_NAMESPACE_ID')

class ImageUploader:
    def __init__(self, output_path: str, img_name: str):
        self.file_path = Path(output_path) / f"{img_name}.png"
        self.img_name = img_name
        self.telegram_api_url = f'https://api.telegram.org/bot{TG_Bot_Token}/sendPhoto'
        self.cloudflare_kv_url = (
            f'https://api.cloudflare.com/client/v4/accounts/'
            f'{CLOUDFLARE_ACCOUNT_ID}/storage/kv/namespaces/'
            f'{CLOUDFLARE_NAMESPACE_ID}'
        )

    def _handle_error(self, message: str) -> Dict:
        """统一错误处理"""
        return {'error': message, 'timestamp': datetime.datetime.now().isoformat()}

    def _make_request(self, url: str, method: str = 'POST', **kwargs) -> Optional[Dict]:
        """统一请求处理"""
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return None

    def upload_file(self) -> Dict:
        """上传文件到Telegram"""
        if not self.file_path.exists():
            return self._handle_error(f'文件不存在: {self.file_path}')
        with open(self.file_path, 'rb') as upload_file:
            file_extension = self.file_path.suffix.lower()
            response = self._make_request(
                self.telegram_api_url,
                files={'photo': upload_file},
                data={'chat_id': TG_Chat_ID}
            )

            if not response:
                return self._handle_error('上传到 Telegram 失败')

            file_id = self.get_file_id(response)
            if not file_id:
                return self._handle_error('获取文件 ID 失败')

            return {'src': f'{file_id}{file_extension}'}

    def get_file_id(self, response):
        if not response.get('ok') or not response.get('result'):
            return None
        if 'photo' in response['result']:
            return max(response['result']['photo'], key=lambda x: x['file_size'])['file_id']
        return None

    def write_to_cloudflare_kv(self, key: str, value: str) -> Dict:
        """写入Cloudflare KV存储"""
        api_url = f'{self.cloudflare_kv_url}/values/{key}'
        metadata = {
            "CurrentDateTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Label": "None",
            "ListType": "None",
            "TimeStamp": int(time.time() * 1000),
            "liked": True
        }
        
        response = self._make_request(
            api_url,
            method='PUT',
            headers={'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}'},
            files={
                'value': (None, value),
                'metadata': json.dumps(metadata)
            }
        )
        
        return {'success': True} if response else self._handle_error('写入 Cloudflare KV 失败')

    def upload_and_write_kv(self, write_kv: bool = False) -> Dict:
        """上传文件并可选写入KV存储"""
        upload_result = self.upload_file()
        if "error" in upload_result:
            return upload_result
            
        if write_kv:
            key = upload_result["src"]
            kv_result = self.write_to_cloudflare_kv(key, self.img_name)
            if "error" in kv_result:
                return kv_result
                
        return upload_result

    def read_kv_keys(self) -> Dict:
        """读取Cloudflare KV存储的keys"""
        api_url = f'{self.cloudflare_kv_url}/keys'
        response = self._make_request(
            api_url,
            method='GET',
            headers={'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}'}
        )
        
        if not response:
            return self._handle_error('读取 Cloudflare KV 失败')
            
        kv_keys = [
            {'name': item['name'], 'metadata': item.get('metadata', 'No metadata')}
            for item in response.get("result", [])
        ]
        return {'success': True, 'keys': kv_keys}
