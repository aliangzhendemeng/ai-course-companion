"""QuizService 单元测试：生成追加、清空重生成、选择/判断判分。"""

import json

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from backend.models import Course, Question, StudySet, StudySetCourse, Transcript
from backend.services.quiz_service import QuizService


@pytest.fixture
def db_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def sample_course(db_engine):
    with Session(db_engine) as session:
        course = Course(
            title="测试课程",
            video_path="/tmp/test.mp4",
            status="completed",
            progress_percent=100,
        )
        session.add(course)
        session.commit()
        session.refresh(course)
        # 加点字幕，保证全文非空
        session.add(Transcript(course_id=course.id, text="机器学习是人工智能的分支。", start_time=0.0, end_time=5.0))
        session.commit()
        return course.id


class FakeLLM:
    """返回固定题目 JSON。"""

    def __init__(self):
        self.calls = 0

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        self.calls += 1
        return json.dumps(
            [
                {"type": "choice", "question": "ML 属于？", "options": ["AI 分支", "操作系统", "数据库", "网络"], "answer": "A", "explanation": "ML 是 AI 分支"},
                {"type": "judge", "question": "ML 是 AI 的分支", "options": None, "answer": "正确"},
            ],
            ensure_ascii=False,
        )

    @property
    def model_identifier(self) -> str:
        return "fake"


@pytest.fixture
def quiz_service(db_engine, monkeypatch):
    monkeypatch.setattr("backend.services.quiz_service.engine", db_engine)
    return lambda: QuizService(session=Session(db_engine), llm=FakeLLM())


def _questions(db_engine) -> list[Question]:
    with Session(db_engine) as session:
        return list(session.exec(select(Question).order_by(Question.id)).all())


class TestGenerate:
    def test_generate_creates_questions(self, quiz_service, db_engine, sample_course):
        service = quiz_service()
        generated, total = service.generate(course_id=sample_course, count=2)
        assert generated == 2
        assert total == 2

        questions = _questions(db_engine)
        assert len(questions) == 2
        assert questions[0].course_id == sample_course
        assert questions[0].type == "choice"
        assert json.loads(questions[0].options)[0] == "AI 分支"
        assert questions[1].type == "judge"

    def test_generate_appends(self, quiz_service, db_engine, sample_course):
        service = quiz_service()
        service.generate(course_id=sample_course, count=2)
        generated, total = service.generate(course_id=sample_course, count=2)
        assert generated == 2
        assert total == 4  # 追加，不覆盖

    def test_generate_requires_completed_course(self, quiz_service, db_engine):
        with Session(db_engine) as session:
            course = Course(title="处理中", video_path="/tmp/p.mp4", status="processing")
            session.add(course)
            session.commit()
            session.refresh(course)
            cid = course.id
        with pytest.raises(ValueError, match="尚未处理完成"):
            quiz_service().generate(course_id=cid)

    def test_generate_requires_exactly_one_scope(self, quiz_service, sample_course):
        with pytest.raises(ValueError, match="必须且只能"):
            quiz_service().generate()  # 两个都没给
        with pytest.raises(ValueError, match="必须且只能"):
            quiz_service().generate(course_id=sample_course, study_set_id=1)  # 两个都给

    def test_generate_study_set_scope(self, quiz_service, db_engine, sample_course):
        with Session(db_engine) as session:
            ss = StudySet(name="数学")
            session.add(ss)
            session.commit()
            session.refresh(ss)
            session.add(StudySetCourse(study_set_id=ss.id, course_id=sample_course))
            session.commit()
            ssid = ss.id
        generated, total = quiz_service().generate(study_set_id=ssid, count=2)
        assert generated == 2
        questions = _questions(db_engine)
        assert all(q.study_set_id == ssid for q in questions)
        assert all(q.course_id is None for q in questions)
        # 学习集范围记录来源课程
        assert questions[0].source_course_id == sample_course


class TestGrading:
    def test_choice_correct(self, quiz_service, db_engine, sample_course):
        service = quiz_service()
        service.generate(course_id=sample_course, count=2)
        choice = [q for q in _questions(db_engine) if q.type == "choice"][0]

        q = service.submit_answer(choice.id, "A")
        assert QuizService.is_correct(q, "A") is True
        assert QuizService.is_correct(q, "a") is True  # 大小写容错
        assert QuizService.is_correct(q, "B") is False

    def test_judge_correct(self, quiz_service, db_engine, sample_course):
        service = quiz_service()
        service.generate(course_id=sample_course, count=2)
        judge = [q for q in _questions(db_engine) if q.type == "judge"][0]

        q = service.submit_answer(judge.id, "正确")
        assert QuizService.is_correct(q, "正确") is True
        assert QuizService.is_correct(q, "对") is True
        assert QuizService.is_correct(q, "错误") is False

    def test_submit_missing_question_raises(self, quiz_service):
        with pytest.raises(ValueError, match="题目不存在"):
            quiz_service().submit_answer(999, "A")


class TestClear:
    def test_clear_removes_scope_questions(self, quiz_service, db_engine, sample_course):
        service = quiz_service()
        service.generate(course_id=sample_course, count=2)
        n = service.clear(course_id=sample_course)
        assert n == 2
        assert _questions(db_engine) == []


class TestWrongBook:
    def test_submit_records_attempt_and_wrong_listed(self, quiz_service, db_engine, sample_course):
        service = quiz_service()
        service.generate(course_id=sample_course, count=2)
        questions = _questions(db_engine)
        choice = [q for q in questions if q.type == "choice"][0]
        judge = [q for q in questions if q.type == "judge"][0]

        # 选择题答错，判断题答对
        service.submit_answer(choice.id, "B")  # 正确是 A
        service.submit_answer(judge.id, "正确")

        wrong = service.get_wrong_questions(course_id=sample_course)
        assert [q.id for q in wrong] == [choice.id]

    def test_correct_after_wrong_removes_from_wrong_book(self, quiz_service, db_engine, sample_course):
        service = quiz_service()
        service.generate(course_id=sample_course, count=2)
        choice = [q for q in _questions(db_engine) if q.type == "choice"][0]

        service.submit_answer(choice.id, "B")  # 先答错
        assert len(service.get_wrong_questions(course_id=sample_course)) == 1

        service.submit_answer(choice.id, "A")  # 再答对
        assert service.get_wrong_questions(course_id=sample_course) == []

    def test_unanswered_not_in_wrong_book(self, quiz_service, db_engine, sample_course):
        service = quiz_service()
        service.generate(course_id=sample_course, count=2)
        assert service.get_wrong_questions(course_id=sample_course) == []

    def test_clear_removes_attempts(self, quiz_service, db_engine, sample_course):
        service = quiz_service()
        service.generate(course_id=sample_course, count=2)
        choice = [q for q in _questions(db_engine) if q.type == "choice"][0]
        service.submit_answer(choice.id, "B")

        service.clear(course_id=sample_course)
        with Session(db_engine) as session:
            from backend.models import QuestionAttempt
            remaining = list(session.exec(select(QuestionAttempt)).all())
        assert remaining == []


class TestProgressResume:
    def test_list_questions_attaches_latest_attempt(self, quiz_service, db_engine, sample_course):
        """已答题附带最近作答，未答题为 None，供前端断点续答。"""
        service = quiz_service()
        service.generate(course_id=sample_course, count=2)
        questions = _questions(db_engine)
        choice = [q for q in questions if q.type == "choice"][0]
        judge = [q for q in questions if q.type == "judge"][0]

        service.submit_answer(choice.id, "B")  # 答错

        listed = {q.id: (la, lc) for q, la, lc in service.list_questions(course_id=sample_course)}
        assert listed[choice.id] == ("B", False)
        # 未答的题没有进度
        assert listed[judge.id] == (None, None)

    def test_progress_reflects_latest_attempt(self, quiz_service, db_engine, sample_course):
        """多次作答，进度反映最近一次（重答答对后 last_correct=True）。"""
        service = quiz_service()
        service.generate(course_id=sample_course, count=2)
        choice = [q for q in _questions(db_engine) if q.type == "choice"][0]

        service.submit_answer(choice.id, "B")  # 先错
        service.submit_answer(choice.id, "A")  # 再对

        listed = {q.id: (la, lc) for q, la, lc in service.list_questions(course_id=sample_course)}
        assert listed[choice.id] == ("A", True)
