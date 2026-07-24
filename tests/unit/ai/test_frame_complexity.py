"""帧复杂度分析测试。"""

from backend.ai.frame_complexity import FrameComplexityAnalyzer


def test_simple_text_frame_is_not_complex():
    """纯文字且较长的 OCR 结果应判定为不复杂。"""
    analyzer = FrameComplexityAnalyzer()
    text = "这是一段普通的课程讲解文字，内容比较长，没有公式代码。"
    assert analyzer.is_complex(text) is False


def test_short_text_is_not_complex():
    """非常短的文字也不触发视觉模型。"""
    analyzer = FrameComplexityAnalyzer()
    assert analyzer.is_complex("谢谢") is False


def test_code_symbols_make_complex():
    """包含代码符号的文本应判定为复杂。"""
    analyzer = FrameComplexityAnalyzer()
    text = "def hello():\n    return 'world'"
    assert analyzer.is_complex(text) is True


def test_formula_symbols_make_complex():
    """包含公式符号的文本应判定为复杂。"""
    analyzer = FrameComplexityAnalyzer()
    text = "E = mc^2"
    assert analyzer.is_complex(text) is True


def test_chart_keywords_make_complex():
    """包含图表关键词的文本应判定为复杂。"""
    analyzer = FrameComplexityAnalyzer()
    text = "如下图所示，架构图包含多个模块"
    assert analyzer.is_complex(text) is True


def test_empty_text_is_not_complex():
    """空文本不复杂。"""
    analyzer = FrameComplexityAnalyzer()
    assert analyzer.is_complex("") is False
    assert analyzer.is_complex("   ") is False
