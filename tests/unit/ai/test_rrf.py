"""RRF 融合测试。"""

from backend.ai.rank_utils import rrf_fuse


def test_rrf_fuse_basic():
    """RRF 融合基本功能。"""
    list1 = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    list2 = [{"id": "b"}, {"id": "a"}, {"id": "d"}]

    result = rrf_fuse([list1, list2], k=60, top_n=2, key="id")

    assert len(result) == 2
    # a 和 b 都出现在两个列表中，得分应高于只出现一次的 c/d
    ids = [r["id"] for r in result]
    assert "a" in ids
    assert "b" in ids


def test_rrf_fuse_single_list():
    """单列表时直接返回原顺序。"""
    list1 = [{"id": "a"}, {"id": "b"}]
    result = rrf_fuse([list1], k=60, top_n=2, key="id")
    assert [r["id"] for r in result] == ["a", "b"]


def test_rrf_fuse_empty_lists():
    """空列表返回空。"""
    assert rrf_fuse([], k=60, top_n=5, key="id") == []
    assert rrf_fuse([[]], k=60, top_n=5, key="id") == []


def test_rrf_fuse_dedup():
    """重复文档应去重。"""
    list1 = [{"id": "a"}, {"id": "a"}, {"id": "b"}]
    list2 = [{"id": "a"}, {"id": "c"}]

    result = rrf_fuse([list1, list2], k=60, top_n=10, key="id")
    ids = [r["id"] for r in result]
    assert ids.count("a") == 1
