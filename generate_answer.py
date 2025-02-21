import asyncio
from supabase_articles_writer import SupabaseArticlesWriter
from logger_base import LoggerBase
from deepai import call_ai_api


async def generate_article(labelId):
    logger = LoggerBase()
    try:
        writer = SupabaseArticlesWriter(logger=logger)
        results = await writer.get_all_materials_last_questions(labelId=labelId)
        if results:
            for item in results:
                try:
                    ai_response = call_ai(item)
                    # print("AI 回复:", ai_response)

                    reasoning_content = ai_response.get('reasoning_content').strip('\n')
                    content = ai_response.get('content', '').lstrip('\n') if ai_response.get('content') else ''

                    if reasoning_content and content:
                        await writer.update_article_think_answer(item['id'], reasoning_content, content)
                    else:
                        print(f"跳过ID {item['id']}: AI响应缺少必要字段")
                        continue
                except Exception as e:
                    print(f"处理单个项目时出错 (ID: {item['id']}): {e}")
                    continue
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
    province_strings = [
        '101',
        '102', '103', '104', '105', '106',
        '107', '108', '109', '110', '111', '112',
        '113', '114', '115', '116',
        '117', '118', '119', '120', '121',
        '122', '123', '124', '125',
        '126', '127', '128', '129',
        '5244', '130',
        '131',
        '132', '133',
        '134', '3591', '2894'
    ]
    for province_code in province_strings:
        asyncio.run(generate_article(province_code))
