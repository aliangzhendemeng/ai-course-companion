"""排序融合工具：RRF（Reciprocal Rank Fusion）。"""

from typing import Callable, TypeVar

T = TypeVar("T")


def rrf_fuse(
    ranked_lists: list[list[dict]],
    k: int = 60,
    top_n: int = 5,
    key: str = "id",
) -> list[dict]:
    """对多个排序列表做 RRF 融合。

    Args:
        ranked_lists: 多个排序结果列表，每个元素是 dict，必须包含 key 字段。
        k: RRF 常数，默认 60。
        top_n: 返回前 N 个结果。
        key: 用于去重和标识的字段名。

    Returns:
        融合后的列表，按 RRF 分数降序排列。
    """
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            item_key = str(item.get(key))
            if item_key in items:
                # 同一文档在多个列表中出现，取并集
                continue
            items[item_key] = item
            scores[item_key] = scores.get(item_key, 0.0) + 1.0 / (k + rank)

    sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [items[k] for k in sorted_keys[:top_n]]
