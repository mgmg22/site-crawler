import asyncio
from supabase_articles_writer import SupabaseArticlesWriter
from logger_base import LoggerBase


async def main():
    logger = LoggerBase()
    try:
        writer = SupabaseArticlesWriter(logger=logger)
        results = await writer.get_all_materials_last_questions()

        print(f"\n返回的原始数据: {results}")

        if results:
            print("\n查询到的材料信息:")
            item = results[0]
            print("-" * 50)
            print(f"ID: {item['id']}")
            print(f"Materials: {item['materials']}")
            print(f"Last Question: {item['last_question']}")
        else:
            print("未找到任何带有 last_question 的材料。")

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
