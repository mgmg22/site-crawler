import asyncio
from supabase_articles_writer import SupabaseArticlesWriter
from logger_base import LoggerBase
from deepai import call_ai_api


async def main():
    logger = LoggerBase()
    try:
        writer = SupabaseArticlesWriter(logger=logger)
        results = await writer.get_all_materials_last_questions()
        if results:
            print("\n查询到的材料信息:")
            item = results[0]
            print("-" * 50)
            print(f"Materials: {item['materials']}")
            print(f"Last Question: {item['last_question']}")
            call_ai(item)
        else:
            print("未找到任何带有 last_question 的材料。")

    except Exception as e:
        print(f"发生错误: {e}")


def call_ai(item):
    prompt_text = f'''阅读所有Materials ，根据Last Question的要求作答，使用Markdown语法，标题独占一行，正文一共5个段落，每个分论点的小标题加粗，其中源于材料的论据用如下划线之类的醒目样式
Materials: {item['materials']}
Last Question: {item['last_question']}
'''
    ai_response = call_ai_api(prompt_text)
    print("AI 回复:", ai_response)


if __name__ == "__main__":
    asyncio.run(main())
