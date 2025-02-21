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
                    prompt_text = f'''阅读所有Materials ，根据Question的要求作答，使用Markdown语法，第一行为文章标题，总分总结构（一个总起，三个分论点，一个总结，共五段。），分论点的小标题加粗但不换行，其中源于材料的论据用醒目的Markdown样式来展示
Materials: {item['materials']}
Question: {item['questions'][-1]}
'''
                    ai_response = call_ai_api(prompt_text)
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


async def generate_answer(page_num):
    logger = LoggerBase()
    try:
        writer = SupabaseArticlesWriter(logger=logger)
        article = await writer.get_article_by_page_num(page_num=page_num)

        if article:
            try:
                prompt_text = f'''根据Question的要求,阅读对应的Materials完成作答，不同作答要点可使用1.前缀和换行来区分，超过6个点考虑合并要点，不要使用Markdown加粗语法
Question: {article['questions'][0]}
Materials: {article['materials']}
'''
                ai_response = call_ai_api(prompt_text)

                reasoning_content = ai_response.get('reasoning_content').strip('\n')
                content = ai_response.get('content', '').lstrip('\n') if ai_response.get('content') else ''
                print("AI 回复reasoning_content:", reasoning_content)
                print("AI 回复content:", content)
            except Exception as e:
                print(f"处理文章时出错 (page_num: {page_num}): {e}")
        else:
            print("未找到文章。")
    except Exception as e:
        print(f"发生错误: {e}")


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
    # for province_code in province_strings:
    #     asyncio.run(generate_article(province_code))
    asyncio.run(generate_answer(7900381))
