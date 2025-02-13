from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import time


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


def main():
    logger = setup_logger()
    logger.info("启动无头浏览器...")
    driver = None

    try:
        driver = create_headless_driver()

        # 访问百度首页
        logger.info("正在访问百度首页...")
        driver.get('https://www.baidu.com')

        # 等待页面加载完成
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

        # 执行JavaScript来获取控制台输出
        logger.info("注入控制台监听器...")
        driver.execute_script("""
            console.defaultLog = console.log.bind(console);
            console.logs = [];
            console.log = function(){
                console.defaultLog.apply(console, arguments);
                console.logs.push(Array.from(arguments));
            }
        """)

        # 等待一段时间以收集日志
        time.sleep(2)

        # 获取注入的日志
        logger.info("获取控制台日志...")
        console_logs = driver.execute_script("return console.logs")
        if console_logs:
            logger.info("控制台输出内容：")
            for log in console_logs:
                print(f"[LOG] {' '.join(map(str, log))}")
        else:
            logger.info("没有发现控制台输出")

        # 尝试获取浏览器原生日志
        browser_logs = get_console_logs(driver)
        if browser_logs:
            logger.info("浏览器原生日志：")
            for log in browser_logs:
                print(f"[{log.get('level', 'INFO')}] {log.get('message', '')}")

    except Exception as e:
        logger.error(f"发生错误: {str(e)}")

    finally:
        if driver:
            logger.info("关闭浏览器...")
            driver.quit()


if __name__ == "__main__":
    main()
