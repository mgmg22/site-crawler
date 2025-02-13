import logging


class LoggerBase:
    """基础日志记录器类"""

    def __init__(self):
        self.logger = self.setup_logger()

    def setup_logger(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def info(self, message: str):
        """记录信息级别的日志"""
        self.logger.info(message)

    def error(self, message: str):
        """记录错误级别的日志"""
        self.logger.error(message)
