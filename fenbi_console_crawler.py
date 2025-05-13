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


def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def create_headless_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # 使用新版无头模式
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--ignore-certificate-errors')  # 忽略证书错误
    chrome_options.add_argument('--ignore-ssl-errors')  # 忽略SSL错误

    chrome_options.set_capability('goog:loggingPrefs', {
        'browser': 'ALL',
        'performance': 'ALL'
    })

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')

    service = Service()
    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )
    return driver


def add_cookies(driver, cookie_string):
    # 首先访问目标域名，否则无法设置cookie
    driver.get('https://spa.fenbi.com')

    cookie_pairs = cookie_string.split(';')
    for pair in cookie_pairs:
        if '=' in pair:
            name, value = pair.strip().split('=', 1)
            driver.add_cookie({
                'name': name,
                'value': value,
                'domain': '.fenbi.com'
            })


def convert_json(original_json):
    try:
        last_question = original_json['questions'][-1]
        optimized_materials = [material['content'] for material in original_json['materials']]
        optimized_questions = [questions['content'] for questions in original_json['questions']]
        optimized_solutions = [solutions.get('reference', '') for solutions in original_json['solutions']]

        return {
            'name': last_question['source'].replace('（网友回忆版）', ''),
            'materials': optimized_materials,
            'questions': optimized_questions,
            'solutions': optimized_solutions,
            'last_question': last_question['accessories'][0]['title']
        }
    except Exception as e:
        logging.error(f"转换JSON时发生错误: {str(e)}")
        return None


async def process_article_data(labelId, simplified, article_data: dict):
    try:
        writer = SupabaseArticlesWriter()
        insert_data = {
            'labelId': labelId,
            'topic': simplified['topic'],
            'page_num': simplified['id'],
            'name': article_data['name'],
            'materials': article_data['materials'],
            'questions': article_data['questions'],
            'solutions': article_data['solutions'],
            'last_question': article_data['last_question'],
        }
        result = await writer.insert_article(insert_data)
        if result:
            logging.info(f"成功保存文章到数据库，ID: {result.get('id')}")
        return result
    except Exception as e:
        logging.error(f"保存文章到数据库时出错: {str(e)}")
        raise


def get_list(labelId):
    try:
        logger = setup_logger()
        driver = None
        all_papers = []  # 存储所有页面的试卷数据

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Cookie': 'sid=2324896; persistent=oMIwhl22q4RhXbaKYXdyqGkwB6WgmtWUWeqtSsRKUxhKCwdU2UxZCCM0u1+1GLoUbl+ntKmozzhE438rEEZsug==; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22191f8b69e487fe-0fc5b4d9b91081-15313374-2073600-191f8b69e498bd%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTkxZjhiNjllNDg3ZmUtMGZjNWI0ZDliOTEwODEtMTUzMTMzNzQtMjA3MzYwMC0xOTFmOGI2OWU0OThiZCJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%22191f8b69e487fe-0fc5b4d9b91081-15313374-2073600-191f8b69e498bd%22%7D; acw_tc=0b6e704217394347214193465eaf0e29dfb0a7c67910902258a65841e31560; sess=11qnYqL/5HBUzd/JWa4ZGvYdy+3nX81cAvxACdAbKnEYvdcd8wPN9PtXqPrUbAWva8x8OMqPOctAh2cIOcscQGwVL9hkkV2oUFk4yNFzd5Y=; userid=122460950',
                'Accept': 'application/json',
                'Referer': 'https://spa.fenbi.com/',
                'Origin': 'https://spa.fenbi.com'
            }

            first_page = 0
            first_page_url = f'https://tiku.fenbi.com/api/shenlun/papers?labelId={labelId}&toPage={first_page}&kav=100&av=100&hav=100&app=web'
            response = requests.get(first_page_url, headers=headers)
            response.raise_for_status()
            first_page_data = response.json()

            # total_pages = first_page_data['pageInfo']['totalPage']
            # 只取第一页的最新数据
            total_pages = 1
            logger.info(f"从第 {first_page + 1} 页开始，总页数: {total_pages}")

            # 处理所有页面的数据
            for page in range(first_page, total_pages):
                logger.info(f"正在获取第 {page + 1}/{total_pages} 页数据")

                if page == first_page:
                    page_data = first_page_data
                else:
                    page_url = f'https://tiku.fenbi.com/api/shenlun/papers?labelId={labelId}&toPage={page}&kav=100&av=100&hav=100&app=web'
                    response = requests.get(page_url, headers=headers)
                    response.raise_for_status()
                    page_data = response.json()

                # 提取当前页的试卷列表
                current_page_papers = [{
                    'topic': item['topic'],
                    'name': item['name'],
                    'id': item['id'],
                    'encodeCheckInfo': item['encodeCheckInfo']
                } for item in page_data['list']]

                all_papers.extend(current_page_papers)
                logger.info(f"第 {page + 1} 页获取到 {len(current_page_papers)} 份试卷")

                # 如果不是最后一页，等待一小段时间再请求下一页
                if page < total_pages - 1:
                    time.sleep(2)  # 添加2秒延迟，避免请求过于频繁

            logger.info(f"共获取到 {len(all_papers)} 份试卷信息")

            # 创建一个共享的浏览器实例
            driver = create_headless_driver()
            cookie_string = 'sid=2324896; persistent=oMIwhl22q4RhXbaKYXdyqGkwB6WgmtWUWeqtSsRKUxhKCwdU2UxZCCM0u1+1GLoUbl+ntKmozzhE438rEEZsug==; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22191f8b69e487fe-0fc5b4d9b91081-15313374-2073600-191f8b69e498bd%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTkxZjhiNjllNDg3ZmUtMGZjNWI0ZDliOTEwODEtMTUzMTMzNzQtMjA3MzYwMC0xOTFmOGI2OWU0OThiZCJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%22191f8b69e487fe-0fc5b4d9b91081-15313374-2073600-191f8b69e498bd%22%7D; acw_tc=0b6e704217394347214193465eaf0e29dfb0a7c67910902258a65841e31560; sess=11qnYqL/5HBUzd/JWa4ZGvYdy+3nX81cAvxACdAbKnEYvdcd8wPN9PtXqPrUbAWva8x8OMqPOctAh2cIOcscQGwVL9hkkV2oUFk4yNFzd5Y=; userid=122460950'
            add_cookies(driver, cookie_string)

            for index, simplified in enumerate(all_papers):
                try:
                    logger.info(f"正在处理第 {index + 1}/{len(all_papers)} 个试卷: {simplified['name']}")

                    target_url = f'https://spa.fenbi.com/shenlun/zhenti/shenlun/{simplified["id"]}?checkId={simplified["encodeCheckInfo"]}'
                    driver.get(target_url)

                    WebDriverWait(driver, 8).until(
                        lambda d: d.execute_script('return document.readyState') == 'complete'
                    )

                    driver.execute_script("""
                        console.defaultLog = console.log.bind(console);
                        console.logs = [];
                        console.log = function(){
                            console.defaultLog.apply(console, arguments);
                            if (arguments.length > 0 && Array.isArray(arguments[0])) {
                                console.logs.push(Array.from(arguments));
                            }
                        }
                    """)

                    # 等待一段时间以收集日志
                    time.sleep(5)

                    console_logs = driver.execute_script("return console.logs")
                    if console_logs:
                        for log in console_logs:
                            if log and len(log) > 0 and isinstance(log[0], list):
                                optimized_data = convert_json(log[0][0])
                                if optimized_data:
                                    formatted_json = json.dumps(optimized_data, ensure_ascii=False, indent=2)
                                    print(f"阅读所有materials ，根据last_question的要求作答\n{formatted_json}")
                                    asyncio.run(process_article_data(labelId, simplified, optimized_data))
                    else:
                        logger.info("没有发现控制台输出")

                    # 在每次循环结束后等待15秒
                    if index < len(all_papers) - 1:  # 如果不是最后一个元素
                        logger.info("等待15秒后处理下一个试卷...")
                        time.sleep(15)

                except Exception as e:
                    logger.error(f"处理试卷 {simplified['name']} 时发生错误: {str(e)}")
                    continue

            return all_papers

        except requests.RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"发生未知错误: {str(e)}")
            return None

    finally:
        if driver:
            logger.info("关闭浏览器...")
            driver.quit()


if __name__ == "__main__":
    province_strings = [
        # '101',  # 国考
        # '102',  # 安徽
        # '103',  # 北京
        # '104',  # 福建
        '105',  # 甘肃
        '106',  # 广东
        '107',  # 广西
        '108',  # 贵州
        '109',  # 海南
        '110',  # 河北
        '111',  # 河南
        '112',  # 黑龙江
        '113',  # 湖北
        '114',  # 湖南
        '115',  # 吉林
        '116',  # 江苏
        '117',  # 江西
        '118',  # 辽宁
        '119',  # 内蒙古
        '120',  # 宁夏
        '121',  # 青海
        '122',  # 山东
        '123',  # 山西
        '124',  # 陕西
        '125',  # 上海
        '126',  # 四川
        '127',  # 天津
        # '128',  # 西藏 (注意: 源 LABELS 数据中此项被注释)
        '129',  # 新疆
        '5244',  # 新疆兵团
        '130',  # 云南
        '131',  # 浙江
        '132',  # 重庆
        # '133',  # 广州
        '134',  # 深圳
        '3591',  # 选调生
        '2894'  # 公安
    ]
    for province_code in province_strings:
      get_list(province_code)
