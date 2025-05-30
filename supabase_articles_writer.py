from typing import Dict, Any, Optional
from supabase import create_client, Client
import os
from datetime import datetime
from logger_base import LoggerBase
from dotenv import load_dotenv

load_dotenv()


class SupabaseArticlesWriter:
    """用于向 Supabase articles 表写入数据的工具类"""

    def __init__(self, logger: Optional[LoggerBase] = None):
        """
        初始化 SupabaseArticlesWriter

        Args:
            logger: 可选的日志记录器实例
        """
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("未设置 SUPABASE_URL 或 SUPABASE_KEY 环境变量")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.logger = logger or LoggerBase()

    async def check_article_exists(self, name: str) -> bool:
        """
        检查指定标题的文章是否已存在

        Args:
            name: 文章标题

        Returns:
            bool: 如果文章存在返回 True，否则返回 False
        """
        try:
            result = self.client.table('articles')\
                .select('id')\
                .eq('name', name)\
                .execute()

            return bool(result.data)
        except Exception as e:
            error_msg = f"检查文章是否存在时发生错误: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def insert_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        向 articles 表插入一条文章数据，如果标题不存在的话

        Args:
            article_data: 包含文章数据的字典

        Returns:
            插入成功后的文章数据，或者 None（如果文章已存在）

        Raises:
            Exception: 当插入操作失败时抛出
        """
        try:
            name = article_data.get('name')
            if not name:
                raise ValueError("文章数据中缺少标题")

            exists = await self.check_article_exists(name)
            if exists:
                self.logger.info(f"文章 '{name}' 已存在，跳过插入")
                return None

            article_data['created_at'] = datetime.utcnow().isoformat()

            # 执行插入操作
            result = self.client.table('articles').insert(article_data).execute()

            if not result.data:
                raise Exception("插入数据后未返回结果")
            return result.data[0]

        except Exception as e:
            error_msg = f"插入文章数据时发生错误: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def get_all_materials_last_questions(self, labelId: Optional[int] = None) -> list[Dict[str, Any]]:
        """
        从 articles 表中查询所有 think 为空的文章材料和最后一个问题，可选根据 label_id 过滤

        Args:
            labelId: 可选的标签ID，用于过滤特定标签的文章

        Returns:
            list[Dict[str, Any]]: 包含 materials、questions、last_question 和 id 的字典列表
        """
        try:
            query = self.client.table('articles')\
                .select('materials, questions, think, answer, page_num, thinks, id')\
                .is_('thinks', None)

            if labelId is not None:
                query = query.eq('labelId', labelId)

            response = query.execute()
            result = response.data

            if not result:
                log_message = "未找到符合条件的文章"
                if labelId is not None:
                    log_message += f" (labelId: {labelId})"
                self.logger.info(log_message)
                return []

            return result

        except Exception as e:
            error_msg = f"查询材料的 last_question 时发生错误: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def update_article_think_answer(self, article_id: str, think: str, answer: str) -> Dict[str, Any]:
        """
        根据文章ID更新think和answer字段

        Args:
            article_id: 文章ID (UUID格式)
            think: 思考内容
            answer: 回答内容

        Returns:
            Dict[str, Any]: 更新后的文章数据

        Raises:
            Exception: 当更新操作失败时抛出
        """
        try:
            if not article_id:
                raise ValueError("缺少文章ID")

            update_data = {
                'think': think,
                'answer': answer
            }

            result = self.client.table('articles')\
                .update(update_data)\
                .eq('id', article_id)\
                .execute()

            if not result.data:
                raise Exception(f"未找到ID为 {article_id} 的文章或更新失败")

            return result.data[0]

        except Exception as e:
            error_msg = f"更新文章think和answer时发生错误: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def get_article_by_page_num(self, page_num: int) -> Optional[Dict[str, Any]]:
        """
        根据 page_num 获取文章的详细信息

        Args:
            page_num: 页码

        Returns:
            Optional[Dict[str, Any]]: 包含文章详细信息的字典，如果未找到则返回 None

        Raises:
            Exception: 当查询操作失败时抛出
        """
        try:
            if not isinstance(page_num, int) or page_num < 0:
                raise ValueError("page_num 必须是非负整数")

            response = self.client.table('articles')\
                .select('''
                    page_num,
                    materials,
                    questions,
                    answer,
                    think
                ''')\
                .eq('page_num', page_num)\
                .execute()

            if not response.data or len(response.data) == 0:
                self.logger.info(f"未找到 page_num 为 {page_num} 的文章")
                return None

            article = response.data[0]

            # 格式化返回数据
            formatted_article = {
                'pageNum': article.get('page_num'),
                'materials': article.get('materials'),
                'questions': article.get('questions'),
                'answer': article.get('answer', '').replace('<h2>', '').replace('</h2>', '') if isinstance(article.get('answer'), str) else article.get('answer'),
                'think': article.get('think'),
            }

            return formatted_article

        except Exception as e:
            error_msg = f"根据 page_num 查询文章时发生错误: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def update_article_thinks_and_deep_answers(self, page_num: int, thinks: list, deep_answers: list) -> Dict[str, Any]:
        """
        根据 page_num 更新文章的 thinks 和 deep_answers 字段

        Returns:
            Dict[str, Any]: 更新后的文章数据

        Raises:
            Exception: 当更新操作失败时抛出
        """
        try:
            if not isinstance(page_num, int) or page_num < 0:
                raise ValueError("page_num 必须是非负整数")

            update_data = {
                'thinks': thinks,
                'deep_answers': deep_answers
            }

            result = self.client.table('articles')\
                .update(update_data)\
                .eq('page_num', page_num)\
                .execute()

            if not result.data:
                raise Exception(f"未找到 page_num 为 {page_num} 的文章或更新失败")

            return result.data[0]

        except Exception as e:
            error_msg = f"更新文章 thinks 和 deep_answers 时发生错误: {str(e)}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
