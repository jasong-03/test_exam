"""Data models for exam extraction."""

from .enums import (
    ResponseType,
    DiagramType,
    ContentSegmentType,
    Subject,
    ExtractionStatus
)

from .question import (
    BoundingBox,
    ContentSegment,
    QuestionContent,
    MCQOption,
    BlankAnswer,
    ResponseConfig,
    WorkedSolutionStep,
    MarkingCriterion,
    AnswerKey,
    Diagram,
    QuestionSource,
    Question,
    ExamMetadata,
    ExtractionMetrics,
    ExamPaper
)

__all__ = [
    # Enums
    "ResponseType",
    "DiagramType",
    "ContentSegmentType",
    "Subject",
    "ExtractionStatus",
    # Models
    "BoundingBox",
    "ContentSegment",
    "QuestionContent",
    "MCQOption",
    "BlankAnswer",
    "ResponseConfig",
    "WorkedSolutionStep",
    "MarkingCriterion",
    "AnswerKey",
    "Diagram",
    "QuestionSource",
    "Question",
    "ExamMetadata",
    "ExtractionMetrics",
    "ExamPaper",
]
