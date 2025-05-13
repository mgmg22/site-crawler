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


async def generate_answer(labelId):
    logger = LoggerBase()
    try:
        writer = SupabaseArticlesWriter(logger=logger)
        results = await writer.get_all_materials_last_questions(labelId=labelId)

        if not results:
            print(f"标签 {labelId} 没有找到相关数据。")
            return

        for article in results:
            try:
                page_num = article['page_num']
                if not article['questions']:
                    print(f"页面 {page_num} 没有问题，跳过处理。")
                    continue

                questions = article['questions'][:-1]  # 排除最后一个问题
                expected_length = len(questions)  # 期望的答案数量

                thinks = []
                deep_answers = []
                has_error = False

                for i, question in enumerate(questions):
                    try:
                        prompt_text = f'''根据Question的要求,阅读对应的Materials完成作答，不同作答要点可使用1.前缀和换行来区分，超过6个点考虑合并要点，不要使用Markdown加粗语法
Question: {question}
Materials: {article['materials']}
'''
                        ai_response = call_ai_api(prompt_text)

                        reasoning_content = ai_response.get('reasoning_content').strip('\n')
                        content = ai_response.get('content', '').lstrip('\n') if ai_response.get('content') else ''

                        # 检查响应内容是否为空或仅包含空白字符
                        if not reasoning_content.strip() or not content.strip():
                            print(f"页面 {page_num} 问题 {i + 1} 的AI响应内容为空")
                            has_error = True
                            break

                        thinks.append(reasoning_content)
                        deep_answers.append(content)
                        print(f"页面 {page_num} 问题 {i + 1}/{len(questions)} 处理完成")

                    except Exception as e:
                        print(f"处理页面 {page_num} 问题 {i + 1} 时出错: {e}")
                        has_error = True
                        break

                if not has_error and len(thinks) == expected_length and len(deep_answers) == expected_length:
                    thinks.append(article['think'].strip('\n'))
                    deep_answers.append(article['answer'])
                    try:
                        await writer.update_article_thinks_and_deep_answers(page_num, thinks, deep_answers)
                        print(f"页面 {page_num} 更新成功")
                    except Exception as e:
                        print(f"更新页面 {page_num} 数据库时发生错误: {e}")
                else:
                    print(
                        f"页面 {page_num} 由于处理过程中出现错误或答案数量不完整（期望：{expected_length}，实际：thinks={len(thinks)}, deep_answers={len(deep_answers)}），跳过数据库更新")

            except Exception as e:
                print(f"处理页面 {page_num} 时发生错误: {e}")
                continue

    except Exception as e:
        print(f"处理标签 {labelId} 时发生错误: {e}")


if __name__ == "__main__":
    province_strings = [
        '101',  # 国考
        # '102',  # 安徽
        # '103',  # 北京
        '104',  # 福建
        '105',  # 甘肃
        '106',  # 广东
        # '107',  # 广西
        # '108',  # 贵州
        # '109',  # 海南
        # '110',  # 河北
        '111',  # 河南
        # '112',  # 黑龙江
        # '113',  # 湖北
        # '114',  # 湖南
        # '115',  # 吉林
        '116',  # 江苏
        '117',  # 江西
        '118',  # 辽宁
        # '119',  # 内蒙古
        '120',  # 宁夏
        # '121',  # 青海
        '122',  # 山东
        '123',  # 山西
        # '124',  # 陕西
        '125',  # 上海
        '126',  # 四川
        '127',  # 天津
        # '128',  # 西藏 (注意: 源 LABELS 数据中此项被注释)
        '129',  # 新疆
        '5244',  # 新疆兵团
        # '130',  # 云南
        '131',  # 浙江
        # '132',  # 重庆
        # '133',  # 广州
        # '134',  # 深圳
        '3591',  # 选调生
        # '2894'  # 公安
    ]

    for province_code in province_strings:
        # 小题
        asyncio.run(generate_answer(province_code))
        # 大题
        # asyncio.run(generate_article(province_code))
