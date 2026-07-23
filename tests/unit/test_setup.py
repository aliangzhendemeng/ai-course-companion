import pytest


def test_import_config():
    from backend.config import settings
    assert settings.vision_model == "deepseek"


def test_import_models():
    from backend.models import Course, Frame, Summary, Transcript
    assert Course is not None
    assert Frame is not None
    assert Summary is not None
    assert Transcript is not None
