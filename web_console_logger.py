from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import logging
import time
import json
from supabase_articles_writer import SupabaseArticlesWriter
import asyncio
from logger_base import LoggerBase
import requests


class WebConsoleLogger(LoggerBase):
    """Web控制台日志记录器"""
    pass


def setup_logger():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def create_headless_driver():
    """创建无头浏览器驱动"""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # 使用新版无头模式
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
    chrome_options.add_argument('--ignore-ssl-errors')  # 忽略SSL错误

    # 设置日志首选项
    chrome_options.set_capability('goog:loggingPrefs', {
        'browser': 'ALL',
        'performance': 'ALL'
    })

    # 添加更多的请求头设置
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')

    # 创建服务对象
    service = Service()

    # 创建driver
    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )
    return driver


def get_console_logs(driver):
    """获取浏览器控制台日志"""
    try:
        return driver.get_log('browser')
    except Exception as e:
        logging.error(f"获取日志失败: {str(e)}")
        return []


def add_cookies(driver, cookie_string):
    """添加cookie到浏览器会话"""
    # 首先访问目标域名，否则无法设置cookie
    driver.get('https://spa.fenbi.com')

    # 解析cookie字符串
    cookie_pairs = cookie_string.split(';')
    for pair in cookie_pairs:
        if '=' in pair:
            name, value = pair.strip().split('=', 1)
            driver.add_cookie({
                'name': name,
                'value': value,
                'domain': '.fenbi.com'  # 设置cookie域名
            })


def convert_json(original_json):
    """转换并优化JSON数据结构"""
    try:
        # 获取最后一个问题
        last_question = original_json['questions'][-1]
        # 优化materials，只保留content字段
        optimized_materials = [material['content'] for material in original_json['materials']]
        optimized_questions = [questions['content'] for questions in original_json['questions']]

        return {
            'name': last_question['source'].replace('（网友回忆版）', ''),
            'materials': optimized_materials,
            'questions': optimized_questions,
            'last_question': last_question['accessories'][0]['title']
        }
    except Exception as e:
        logging.error(f"转换JSON时发生错误: {str(e)}")
        return None


async def process_article_data(article_data: dict):
    """处理并保存文章数据到 Supabase"""
    try:
        writer = SupabaseArticlesWriter()
        result = await writer.insert_article(article_data)
        if result:
            logging.info(f"成功保存文章到数据库，ID: {result.get('id')}")
        return result
    except Exception as e:
        logging.error(f"保存文章到数据库时出错: {str(e)}")
        raise


def get_console():
    logger = setup_logger()
    logger.info("启动无头浏览器...")
    driver = None

    try:
        driver = create_headless_driver()
        cookie_string = 'sid=2324896; persistent=oMIwhl22q4RhXbaKYXdyqGkwB6WgmtWUWeqtSsRKUxhKCwdU2UxZCCM0u1+1GLoUbl+ntKmozzhE438rEEZsug==; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22191f8b69e487fe-0fc5b4d9b91081-15313374-2073600-191f8b69e498bd%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTkxZjhiNjllNDg3ZmUtMGZjNWI0ZDliOTEwODEtMTUzMTMzNzQtMjA3MzYwMC0xOTFmOGI2OWU0OThiZCJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%22191f8b69e487fe-0fc5b4d9b91081-15313374-2073600-191f8b69e498bd%22%7D; acw_tc=0b6e704217394347214193465eaf0e29dfb0a7c67910902258a65841e31560; sess=11qnYqL/5HBUzd/JWa4ZGvYdy+3nX81cAvxACdAbKnEYvdcd8wPN9PtXqPrUbAWva8x8OMqPOctAh2cIOcscQGwVL9hkkV2oUFk4yNFzd5Y=; userid=122460950'

        # 添加cookie
        add_cookies(driver, cookie_string)

        # 访问目标页面
        logger.info("正在访问目标页面...")
        # target_url = 'https://spa.fenbi.com/shenlun/list/shenlun/1000'
        target_url = 'https://spa.fenbi.com/shenlun/zhenti/shenlun/7900381?checkId=CWIQ7FVhsw'
        driver.get(target_url)

        # 等待页面加载完成
        WebDriverWait(driver, 8).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

        # 执行JavaScript来获取控制台输出
        driver.execute_script("""
            console.defaultLog = console.log.bind(console);
            console.logs = [];
            console.log = function(){
                console.defaultLog.apply(console, arguments);
                // 只保存数组类型的日志
                if (arguments.length > 0 && Array.isArray(arguments[0])) {
                    console.logs.push(Array.from(arguments));
                }
            }
        """)

        # 等待一段时间以收集日志
        time.sleep(5)  # 增加等待时间确保页面完全加载

        # 获取注入的日志
        console_logs = driver.execute_script("return console.logs")
        if console_logs:
            logger.info("控制台输出内容：")
            for log in console_logs:
                if log and len(log) > 0 and isinstance(log[0], list):
                    optimized_data = convert_json(log[0][0])
                    if optimized_data:
                        formatted_json = json.dumps(optimized_data, ensure_ascii=False, indent=2)
                        print(f"阅读所有materials ，根据last_question的要求作答\n{formatted_json}")

                        # 使用异步函数保存数据
                        asyncio.run(process_article_data(optimized_data))
        else:
            logger.info("没有发现控制台输出")

    except Exception as e:
        logger.error(f"发生错误: {str(e)}")

    finally:
        if driver:
            logger.info("关闭浏览器...")
            driver.quit()


def get_list():
    try:
        logger = setup_logger()

        # API接口地址
        api_url = 'https://tiku.fenbi.com/api/shenlun/papers?labelId=131&toPage=0&kav=100&av=100&hav=100&app=web'

        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Cookie': 'sid=2324896; persistent=oMIwhl22q4RhXbaKYXdyqGkwB6WgmtWUWeqtSsRKUxhKCwdU2UxZCCM0u1+1GLoUbl+ntKmozzhE438rEEZsug==; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22191f8b69e487fe-0fc5b4d9b91081-15313374-2073600-191f8b69e498bd%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTkxZjhiNjllNDg3ZmUtMGZjNWI0ZDliOTEwODEtMTUzMTMzNzQtMjA3MzYwMC0xOTFmOGI2OWU0OThiZCJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%22191f8b69e487fe-0fc5b4d9b91081-15313374-2073600-191f8b69e498bd%22%7D; acw_tc=0b6e704217394347214193465eaf0e29dfb0a7c67910902258a65841e31560; sess=11qnYqL/5HBUzd/JWa4ZGvYdy+3nX81cAvxACdAbKnEYvdcd8wPN9PtXqPrUbAWva8x8OMqPOctAh2cIOcscQGwVL9hkkV2oUFk4yNFzd5Y=; userid=122460950',
            'Accept': 'application/json',
            'Referer': 'https://spa.fenbi.com/',
            'Origin': 'https://spa.fenbi.com'
        }

        response = requests.get(api_url, headers=headers)
        # 检查响应状态
        response.raise_for_status()
        # 解析JSON数据
        paper_data = response.json()
        # 构造新的列表
        simplified_list = [{
            'topic': item['topic'],
            'name': item['name'],
            'id': item['id'],
            'encodeCheckInfo': item['encodeCheckInfo']
        } for item in paper_data['list']]

        # 格式化输出
        formatted_json = json.dumps(simplified_list, ensure_ascii=False)
        print(f"试卷列表数据：\n{formatted_json}")

        return simplified_list

    except requests.RequestException as e:
        logger.error(f"请求失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"发生未知错误: {str(e)}")
        return None


if __name__ == "__main__":
    # get_console()
    get_list()
