import asyncio
from supabase_articles_writer import SupabaseArticlesWriter
from logger_base import LoggerBase
from deepai import call_ai_api


async def main():
    logger = LoggerBase()
    try:
        writer = SupabaseArticlesWriter(logger=logger)
        results = await writer.get_all_materials_last_questions(labelId=101)
        if results:
            item = results[0]
            call_ai(item)
        else:
            print("无数据。")
    except Exception as e:
        print(f"发生错误: {e}")


def call_ai(item):
    prompt_text = f'''阅读所有Materials ，根据Question的要求作答，使用Markdown语法，第一行为文章标题，总分总结构（一个总起，三个分论点，一个总结，共五段。），其中源于材料的论据用斜体样式
Materials: {item['materials']}
Question: {item['questions'][-1]}
作答格式参考：
##标题

总起

**分论点1**。论述

**分论点2**。论述

**分论点3**。论述

总结
'''
    ai_response = call_ai_api(prompt_text)
    print("AI 回复:", ai_response)


if __name__ == "__main__":
    asyncio.run(main())
