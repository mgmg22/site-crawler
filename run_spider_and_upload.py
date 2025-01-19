#!/bin/env python3
# -*- coding: utf-8 -*
"""
cron: 2 0 0 * * 6 run_spider_and_upload.py
new Env('网站爬虫');
"""
import asyncio
from website_spider import scrape_main
from pathlib import Path
from img_upload import ImageUploader


async def run(urls, output_dir='./siteshots'):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    scrape_main_results = await scrape_main(urls, str(output_path))
    print("抓取结果:", scrape_main_results)
    for result in scrape_main_results:
        if result and 'name' in result:
            img_name = result['name']
            uploader = ImageUploader(str(output_path), img_name)
            upload_result = uploader.upload_and_maybe_write_kv(write_kv=True)
            if "src" in upload_result:
                print(f"上传成功: {upload_result['src']}")
                kv_result = uploader.read_kv_keys()
                print("KV 存储中的键值对:")
                if "success" in kv_result:
                    for key in kv_result['keys']:
                        print(f"Name: {key['name']}, Metadata: {key['metadata']}")
            else:
                print(f"上传失败: {upload_result.get('error', '未知错误')} - 完整错误信息: {upload_result}")
        else:
            print("结果数据无效，跳过上传")

if __name__ == '__main__':
    urls_to_scrape = ["https://dunlin.ai/"]
    asyncio.run(run(urls_to_scrape))
