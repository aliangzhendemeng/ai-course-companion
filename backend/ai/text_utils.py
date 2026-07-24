"""BM25 中文分词工具。"""

import jieba


def tokenize_for_bm25(texts: list[str]) -> list[list[str]]:
    """对文本列表进行 jieba 分词，返回 token 列表。"""
    return [list(jieba.cut(text.strip())) for text in texts if text.strip()]
