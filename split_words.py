import jieba.posseg as pseg
import re
import csv

# 定义硬编码的技术术语列表（避免重复定义）
TECH_TERMS = {
    "数据中台", "中台", "数据仓库", "数仓", "数据湖", "湖仓一体",
    "Flink", "Spark", "Hadoop", "Hive", "Kafka", "Doris", "Paimon",
    "实时计算", "流处理", "批处理", "ETL", "数据治理", "维度建模",
    "事实表", "维度表", "OLAP", "数据质量", "元数据", "数据血缘",
    "指标体系", "数据资产", "数据开发", "数据平台",
    "数据可视化", "数据倾斜", "离线数仓", "实时数仓"
}

# 面试相关关键字
INTERVIEW_KEYWORDS = {
    "面试", "面试题", "面试提问", "面经", "面试官", "面试真题",
    "面试必问", "面试系列", "面试八股文", "面试宝典", "面试经验"
}

# 词性过滤规则
POS_FILTER = {
    'a', 'ag', 'ad', 'an',  # 形容词
    'q',  # 量词
    'e', 'y', 'u', 'ug',  # 语气词/助词
    'r', 'c', 'p', 'f',  # 代词/连词/介词/方位词
    'v', 'vg', 'vd', 'vn',  # 动词
    'd'  # 副词
}

# 特殊词过滤列表
SPECIAL_FILTER = {
    "的", "了", "啊", "呢", "吧", "呀", "哦", "嗯", "哈",
    "你", "我", "他", "她", "它", "我们", "你们", "他们",
    "这", "那", "哪", "谁", "什么", "怎么", "为什么",
    "就", "都", "也", "还", "又", "再", "才", "却", "给",
    "滚", "要", "会", "能", "可以", "觉得", "认为", "想",
    "vs"
}


def extract_interview_keywords(text):
    """提取面试相关关键字"""
    found_keywords = []
    for keyword in INTERVIEW_KEYWORDS:
        if keyword in text and keyword not in found_keywords:
            found_keywords.append(keyword)
    return found_keywords


def auto_segment_and_filter(text):
    """自动化分词并过滤，保留技术专有名词"""
    # 使用 PaddleNLP 识别技术专有名词（如果模型可用）
    tech_terms = set()

    # 词性标注分词
    words = pseg.cut(text)

    # 过滤处理
    filtered_words = []
    for word_pair in words:
        word = word_pair.word
        pos = word_pair.flag

        # 跳过标点符号
        if re.match(r'[^\w\s]', word):
            continue

        # 保护技术专有名词（PaddleNLP 识别出的）
        if word in tech_terms:
            filtered_words.append(word)
            continue

        # 保护技术专有名词（硬编码列表）
        if word in TECH_TERMS:
            filtered_words.append(word)
            continue

        # 过滤特定词性和特殊词
        if pos not in POS_FILTER and word not in SPECIAL_FILTER:
            # 合并技术相关的单字词
            if len(word) == 1 and filtered_words and filtered_words[-1] + word in TECH_TERMS:
                filtered_words[-1] += word  # 如"中" + "台" -> "中台"
            else:
                filtered_words.append(word)

    # 后处理：合并技术专有名词
    final_result = []
    i = 0
    while i < len(filtered_words):
        # 检查可能的组合词（2-3个词）
        combined = None
        for length in [3, 2]:
            if i + length <= len(filtered_words):
                candidate = "".join(filtered_words[i:i + length])
                if candidate in tech_terms or candidate in TECH_TERMS:
                    combined = candidate
                    i += length - 1  # 跳过已合并的词
                    break

        if combined:
            final_result.append(combined)
        else:
            # 过滤单字非技术词
            if len(filtered_words[i]) > 1 or filtered_words[i] in TECH_TERMS:
                final_result.append(filtered_words[i])
        i += 1

    # 检查标题中是否包含TECH_TERMS中的关键字，确保都被包含在结果中
    for term in TECH_TERMS:
        if term in text and term not in final_result:
            final_result.append(term)

    # 检查是否包含面试关键字
    interview_keywords = extract_interview_keywords(text)
    if interview_keywords and "面试" not in final_result:
        final_result.append("面试")

    # 去重但保持顺序
    seen = set()
    deduplicated_result = []
    for item in final_result:
        if item not in seen:
            seen.add(item)
            deduplicated_result.append(item)

    return deduplicated_result


def process_csv(input_file, output_file):
    """处理CSV文件，读取标题列并添加分词结果"""
    processed_rows = []

    # 读取CSV文件
    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        # 只保留需要的列
        fieldnames = ['id', 'title', 'segmented_words']

        # 处理每一行
        for row in reader:
            title = row['title']
            segmented_words = auto_segment_and_filter(title)
            # 将分词结果转换为逗号分隔的字符串格式
            processed_row = {
                'id': row['id'],
                'title': row['title'],
                'segmented_words': ','.join(segmented_words)
            }
            processed_rows.append(processed_row)

    # 写入新的CSV文件
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_rows)

    print(f"处理完成，结果已保存到 {output_file}")


if __name__ == "__main__":
    # 根据你的输入文件路径进行修改
    input_file = "./words/articles_202508172026.csv"
    output_file = "./words/articles_segmented_result.csv"

    print("开始处理CSV文件...")
    process_csv(input_file, output_file)
    print("所有标题处理完成！")
