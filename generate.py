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
            for item in results:
                ai_response = call_ai(item)
                print("AI 思考:", ai_response['reasoning_content'])
                # print("AI 回复:", ai_response['content'])
                await writer.update_article_think_answer(item['id'], ai_response['reasoning_content'], ai_response['content'].lstrip('\n'))
        else:
            print("无数据。")
    except Exception as e:
        print(f"发生错误: {e}")


def call_ai(item):
    prompt_text = f'''阅读所有Materials ，根据Question的要求作答，使用Markdown语法，第一行为文章标题，总分总结构（一个总起，三个分论点，一个总结，共五段。），分论点的小标题加粗但不换行，其中源于材料的论据用醒目的Markdown样式来展示
Materials: {item['materials']}
Question: {item['questions'][-1]}
'''
    return call_ai_api(prompt_text)


if __name__ == "__main__":
    asyncio.run(main())
