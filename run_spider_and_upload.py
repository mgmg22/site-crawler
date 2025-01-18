import asyncio
from website_spider import scrape_main
from img_upload import upload_file
from img_upload import write_to_cloudflare_kv
from img_upload import read_kv_keys
from pathlib import Path


async def run(urls, output_dir='./siteshots'):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    scrape_main_results = await scrape_main(urls, str(output_path))
    print("抓取结果:", scrape_main_results)
    for result in scrape_main_results:
        if result and 'name' in result:
            site_name = result['name']
            file_path = output_path / f"{site_name}.png"
            if file_path.exists():
                print(f"正在上传文件: {file_path}")
                upload_result = upload_file(str(file_path))
                if "src" in upload_result:
                    key = upload_result["src"]
                    print(f"写入 KV: {key} -> {site_name}")
                    write_to_cloudflare_kv(key, site_name)
                    read_kv_keys()
                else:
                    print(f"上传失败: {upload_result.get('error', '未知错误')}")
            else:
                print(f"文件不存在: {file_path}")
                print(f"当前工作目录: {Path.cwd()}")
        else:
            print("结果数据无效，跳过上传")

if __name__ == '__main__':
    urls_to_scrape = ["https://chat01.ai/"]
    asyncio.run(run(urls_to_scrape))
