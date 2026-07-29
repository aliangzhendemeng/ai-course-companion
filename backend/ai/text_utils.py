"""BM25 中文分词工具。"""

import jieba


_SYNONYMS = {
    "什麼": "什么",
    "麼": "么",
    "數據": "数据",
    "學習": "学习",
    "課程": "课程",
    "問題": "问题",
    "處理": "处理",
    "關係": "关系",
}


def _to_simplified(text: str) -> str:
    """简单繁体转简体。"""
    for traditional, simplified in _SYNONYMS.items():
        text = text.replace(traditional, simplified)
    return text


def tokenize_for_bm25(texts: list[str]) -> list[list[str]]:
    """对文本列表进行 jieba 分词，返回 token 列表。"""
    results = []
    for text in texts:
        text = text.strip()
        if not text:
            continue
        text = _to_simplified(text)
        tokens = list(jieba.cut(text))
        # 加入 2-gram 提升短语匹配能力
        bigrams = [f"{tokens[i]}{tokens[i+1]}" for i in range(len(tokens) - 1)]
        results.append(tokens + bigrams)
    return results
