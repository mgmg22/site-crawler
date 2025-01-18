import asyncio
import logging
import os
import random
import time
from pathlib import Path
import platform

from bs4 import BeautifulSoup
from pyppeteer import launch
from common_util import CommonUtil

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

global_agent_headers = [
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
    'Opera/9.25 (Windows NT 5.1; U; en)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
    'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
    "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 "
]
# 构建 Chromium 可执行文件路径 (Windows 和 Linux)
if platform.system() == "Windows":
    chromium_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chrome-win", "chrome.exe")
else:
    chromium_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chrome-linux", "chrome")


async def scrape_website(url, browser, output_dir='./screenshots'):
    start_time = int(time.time())
    page = None
    try:
        logger.info("正在处理：" + url)
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url

        page = await browser.newPage()
        await page.setUserAgent(random.choice(global_agent_headers))
        width = 1920
        height = 1080
        await page.setViewport({'width': width, 'height': height})
        await page.goto(url, {'timeout': 60000, 'waitUntil': ['load', 'networkidle2']})

        origin_content = await page.content()
        soup = BeautifulSoup(origin_content, 'html.parser')
        title = soup.title.string.strip() if soup.title else ''
        name = CommonUtil.get_name_by_url(url)
        logger.info(f"生成的站点名称: {name}")

        description = ''
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description:
            description = meta_description['content'].strip()

        if not description:
            meta_description = soup.find('meta', attrs={'property': 'og:description'})
            description = meta_description['content'].strip() if meta_description else ''

        logger.info(f"url:{url}, title:{title},description:{description}")

        dimensions = await page.evaluate('''() => {
                       return {
                           width: document.body.scrollWidth,
                           height: document.body.scrollHeight,
                           deviceScaleFactor: window.devicePixelRatio
                       };
                   }''')

        actual_width = min(width, dimensions['width'])
        actual_height = min(height, dimensions['height'])

        # 使用相对路径
        output_path = Path(output_dir)
        screenshot_path = output_path / f"{name}.png"

        # 确保输出目录存在
        output_path.mkdir(parents=True, exist_ok=True)

        await page.screenshot({'path': str(screenshot_path), 'clip': {
            'x': 0,
            'y': 0,
            'width': actual_width,
            'height': actual_height,
        }})
        content = soup.get_text()
        print(content)
        logger.info(url + "站点处理成功")
        return {
            'name': name,
            'url': url,
            'title': title,
            'description': description,
        }
    except Exception as e:
        logger.error(f"处理 {url} 站点异常，错误信息: {str(e)}", exc_info=True)
        return None
    finally:
        if page:
            await page.close()
        execution_time = int(time.time()) - start_time
        logger.info(f"处理 {url} 用时：{execution_time} 秒")


async def scrape_main(urls, output_dir='./screenshots'):
    """
    主函数，用于管理浏览器实例，批量抓取网站信息
    """
    browser = None
    try:
        browser = await launch(
            headless=True,
            ignoreDefaultArgs=["--enable-automation"],
            ignoreHTTPSErrors=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu',
                  '--disable-software-rasterizer', '--disable-setuid-sandbox'],
            handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
            executablePath=chromium_path
        )
        tasks = [scrape_website(url, browser, output_dir) for url in urls]
        results = await asyncio.gather(*tasks)
        return results
    except Exception as e:
        logger.error("主程序异常: %s", e, exc_info=True)
    finally:
        if browser:
            await browser.close()
