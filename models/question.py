"""Data models for questions and related structures."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from .enums import ResponseType, DiagramType, ContentSegmentType, Subject


@dataclass
class BoundingBox:
    """Bounding box coordinates (0-100 percentage scale)."""
    x1: float
    y1: float
    x2: float
    y2: float

    def to_dict(self) -> Dict[str, float]:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "BoundingBox":
        return cls(x1=data["x1"], y1=data["y1"], x2=data["x2"], y2=data["y2"])


@dataclass
class ContentSegment:
    """A segment of content within a question."""
    type: ContentSegmentType
    content: str
    order: int
    latex: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "content": self.content,
            "order": self.order,
            "latex": self.latex
        }


@dataclass
class QuestionContent:
    """Content of a question with multiple format options."""
    text: str
    text_latex: Optional[str] = None
    text_html: Optional[str] = None
    segments: List[ContentSegment] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "text_latex": self.text_latex,
            "text_html": self.text_html,
            "segments": [s.to_dict() for s in self.segments]
        }


@dataclass
class MCQOption:
    """Multiple choice option."""
    label: str  # A, B, C, D
    text: str
    is_correct: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "text": self.text,
            "is_correct": self.is_correct
        }


@dataclass
class BlankAnswer:
    """Fill in the blank answer."""
    position: int
    expected_answer: str
    acceptable_answers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position,
            "expected_answer": self.expected_answer,
            "acceptable_answers": self.acceptable_answers
        }


@dataclass
class ResponseConfig:
    """Configuration for expected response type."""
    options: List[MCQOption] = field(default_factory=list)  # For MCQ
    blanks: List[BlankAnswer] = field(default_factory=list)  # For fill-in-blank
    word_limit: Optional[int] = None  # For long answer
    show_working: bool = False  # For working area
    matching_pairs: List[Dict[str, str]] = field(default_factory=list)  # For matching

    def to_dict(self) -> Dict[str, Any]:
        return {
            "options": [o.to_dict() for o in self.options],
            "blanks": [b.to_dict() for b in self.blanks],
            "word_limit": self.word_limit,
            "show_working": self.show_working,
            "matching_pairs": self.matching_pairs
        }


@dataclass
class WorkedSolutionStep:
    """A step in a worked solution."""
    step_number: int
    description: str
    expression: Optional[str] = None
    expression_latex: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "description": self.description,
            "expression": self.expression,
            "expression_latex": self.expression_latex
        }


@dataclass
class MarkingCriterion:
    """A marking criterion for rubric-based grading."""
    criterion: str
    marks: float

    def to_dict(self) -> Dict[str, Any]:
        return {"criterion": self.criterion, "marks": self.marks}


@dataclass
class AnswerKey:
    """Answer key for a question."""
    final_answer: str
    acceptable_answers: List[str] = field(default_factory=list)
    worked_solution: List[WorkedSolutionStep] = field(default_factory=list)
    marking_rubric: List[MarkingCriterion] = field(default_factory=list)
    explanation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_answer": self.final_answer,
            "acceptable_answers": self.acceptable_answers,
            "worked_solution": [s.to_dict() for s in self.worked_solution],
            "marking_rubric": [m.to_dict() for m in self.marking_rubric],
            "explanation": self.explanation
        }


@dataclass
class Diagram:
    """A diagram/figure extracted from the exam.
    
    Diagrams are stored as region references on the page image.
    The full page image is kept, and diagrams are referenced by bounding box.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: DiagramType = DiagramType.DIAGRAM
    alt_text: Optional[str] = None
    description: Optional[str] = None
    bounding_box: Optional[BoundingBox] = None
    source_page: int = 0
    is_shared: bool = False
    shared_with_questions: List[str] = field(default_factory=list)
    extraction_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert Diagram to dictionary. Diagrams are region references on page images."""
        return {
            "id": self.id,
            "type": self.type.value,
            "alt_text": self.alt_text,
            "description": self.description,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "source_page": self.source_page,
            "is_shared": self.is_shared,
            "shared_with_questions": self.shared_with_questions,
            "extraction_confidence": self.extraction_confidence
        }


@dataclass
class QuestionSource:
    """Source location of a question in the PDF."""
    page_number: int
    bounding_box: Optional[BoundingBox] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_number": self.page_number,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None
        }


@dataclass
class Question:
    """A question extracted from an exam paper."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_number: str = ""
    parent_question_id: Optional[str] = None
    hierarchy_level: int = 0  # 0=main, 1=part(a,b), 2=subpart(i,ii)
    content: Optional[QuestionContent] = None
    response_type: ResponseType = ResponseType.SHORT_ANSWER
    response_config: Optional[ResponseConfig] = None
    diagrams: List[Diagram] = field(default_factory=list)
    answer_key: Optional[AnswerKey] = None
    marks: Optional[float] = None
    subparts: List["Question"] = field(default_factory=list)
    source: Optional[QuestionSource] = None
    extraction_confidence: float = 0.0
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question_number": self.question_number,
            "parent_question_id": self.parent_question_id,
            "hierarchy_level": self.hierarchy_level,
            "content": self.content.to_dict() if self.content else None,
            "response_type": self.response_type.value,
            "response_config": self.response_config.to_dict() if self.response_config else None,
            "diagrams": [d.to_dict() for d in self.diagrams],
            "answer_key": self.answer_key.to_dict() if self.answer_key else None,
            "marks": self.marks,
            "subparts": [s.to_dict() for s in self.subparts],
            "source": self.source.to_dict() if self.source else None,
            "extraction_confidence": self.extraction_confidence
        }


@dataclass
class ExamMetadata:
    """Metadata about the exam paper."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_file: str = ""
    subject: Subject = Subject.OTHER
    grade_level: Optional[str] = None
    exam_type: Optional[str] = None
    school: Optional[str] = None
    year: Optional[int] = None
    total_marks: Optional[int] = None
    duration_minutes: Optional[int] = None
    extracted_at: datetime = field(default_factory=datetime.now)
    extraction_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_file": self.source_file,
            "subject": self.subject.value,
            "grade_level": self.grade_level,
            "exam_type": self.exam_type,
            "school": self.school,
            "year": self.year,
            "total_marks": self.total_marks,
            "duration_minutes": self.duration_minutes,
            "extracted_at": self.extracted_at.isoformat(),
            "extraction_confidence": self.extraction_confidence
        }


@dataclass
class ExtractionMetrics:
    """Metrics from the extraction process."""
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    processing_time_seconds: float = 0.0
    pages_processed: int = 0
    questions_extracted: int = 0
    diagrams_extracted: int = 0
    agents_used: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "processing_time_seconds": round(self.processing_time_seconds, 2),
            "pages_processed": self.pages_processed,
            "questions_extracted": self.questions_extracted,
            "diagrams_extracted": self.diagrams_extracted,
            "agents_used": self.agents_used,
            "errors": self.errors
        }


@dataclass
class ExamPaper:
    """Complete extracted exam paper."""
    metadata: ExamMetadata = field(default_factory=ExamMetadata)
    questions: List[Question] = field(default_factory=list)
    extraction_metrics: ExtractionMetrics = field(default_factory=ExtractionMetrics)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "questions": [q.to_dict() for q in self.questions],
            "extraction_metrics": self.extraction_metrics.to_dict()
        }

    def to_json(self, indent: int = 2) -> str:
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
