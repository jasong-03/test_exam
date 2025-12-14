"""
Growtrics Exam Extractor - Multi-Agent System for extracting structured questions from exam PDFs.

This package provides a complete pipeline for:
- Parsing PDF exam papers
- Extracting questions with subparts
- Detecting and extracting diagrams using Gemini bounding box detection
- Extracting and linking answer keys
- Cost tracking and monitoring

Usage:
    from exam_extractor import ExamExtractor

    extractor = ExamExtractor(api_key="your-gemini-api-key")
    result = extractor.extract("path/to/exam.pdf")

    # Access extracted data
    for question in result.questions:
        print(f"Q{question.question_number}: {question.content.text}")
        for subpart in question.subparts:
            print(f"  {subpart.question_number}: {subpart.content.text}")
"""

from .models import (
    # Enums
    ResponseType,
    DiagramType,
    ContentSegmentType,
    Subject,
    ExtractionStatus,
    # Models
    BoundingBox,
    Question,
    QuestionContent,
    Diagram,
    AnswerKey,
    ExamPaper,
    ExamMetadata,
    ExtractionMetrics,
)

from .agents import (
    PDFParserAgent,
    QuestionExtractorAgent,
    DiagramExtractorAgent,
    AnswerKeyAgent,
    OrchestratorAgent,
    ExamExtractor,
)

from .tracking import (
    CostTracker,
    PipelineLogger,
)

__version__ = "0.1.0"
__author__ = "Growtrics"

__all__ = [
    # High-level API
    "ExamExtractor",
    # Agents
    "PDFParserAgent",
    "QuestionExtractorAgent",
    "DiagramExtractorAgent",
    "AnswerKeyAgent",
    "OrchestratorAgent",
    # Models
    "Question",
    "QuestionContent",
    "Diagram",
    "AnswerKey",
    "ExamPaper",
    "ExamMetadata",
    "ExtractionMetrics",
    "BoundingBox",
    # Enums
    "ResponseType",
    "DiagramType",
    "ContentSegmentType",
    "Subject",
    "ExtractionStatus",
    # Tracking
    "CostTracker",
    "PipelineLogger",
]
