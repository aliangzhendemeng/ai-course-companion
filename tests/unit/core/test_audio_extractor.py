"""音频提取模块测试。"""

import pytest

from backend.core.audio_extractor import AudioExtractor


def test_audio_extractor_init():
    extractor = AudioExtractor()
    assert extractor.sample_rate == 16000


def test_audio_extractor_custom_sample_rate():
    extractor = AudioExtractor(sample_rate=22050)
    assert extractor.sample_rate == 22050
