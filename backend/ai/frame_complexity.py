"""帧复杂度判断：决定是否需要调用视觉模型。"""

import re


class FrameComplexityAnalyzer:
    """基于 OCR 文本判断画面是否需要视觉模型理解。"""

    # 公式/代码常见符号
    COMPLEX_SYMBOLS = r"[=;\{\}\[\]\(\)\$\^\\\|\+\-\*/<>`~#%@]"

    # 图表/架构/复杂画面关键词
    CHART_KEYWORDS = [
        "图", "图表", "架构", "流程", "示意图", "结构图",
        "流程图", "时序图", "类图", "思维导图", "截屏",
        "diagram", "chart", "architecture", "flow", "schema",
        "graph", "figure", "image", "screenshot",
    ]

    # 短文本阈值：低于此长度通常信息不足，需要视觉模型补充
    # 中文字数按实际汉字计数，其他字符按空格分词后的 token 数估算
    MIN_TEXT_LENGTH = 15

    def is_complex(self, ocr_text: str | None) -> bool:
        """判断画面是否复杂到需要调用视觉模型。

        当前规则：
        - 包含公式/代码符号（如 = ; { } [ ] 等）→ 复杂
        - 包含图表/架构关键词 → 复杂
        - 其他情况（包括长短文本、空文本）→ 不复杂
        """
        if not ocr_text:
            return False

        text = ocr_text.strip()
        if not text:
            return False

        if re.search(self.COMPLEX_SYMBOLS, text):
            return True

        lowered = text.lower()
        for keyword in self.CHART_KEYWORDS:
            if keyword.lower() in lowered:
                return True

        return False
