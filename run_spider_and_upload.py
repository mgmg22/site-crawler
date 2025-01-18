import asyncio
from website_spider import scrape_main
from img_upload import upload_file
import os


async def run(urls, output_dir='./siteshots'):
    results = await scrape_main(urls, output_dir)
    print("抓取结果:", results)
    # 上传生成的 PNG 文件
    for result in results:
        if result and 'name' in result:
            site_name = result['name']
            file_path = os.path.join(output_dir, f"{site_name}.png")
            upload_result = upload_file(file_path)
            print(upload_result)

if __name__ == '__main__':
    urls_to_scrape = ["https://remaker.ai/"]
    asyncio.run(run(urls_to_scrape))
