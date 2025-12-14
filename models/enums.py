"""Enums for exam extraction system."""

from enum import Enum


class ResponseType(str, Enum):
    """Types of expected responses for questions."""
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    SHORT_ANSWER = "SHORT_ANSWER"
    LONG_ANSWER = "LONG_ANSWER"
    WORKING_AREA = "WORKING_AREA"
    FILL_IN_BLANK = "FILL_IN_BLANK"
    TRUE_FALSE = "TRUE_FALSE"
    MATCHING = "MATCHING"
    DIAGRAM_LABEL = "DIAGRAM_LABEL"


class DiagramType(str, Enum):
    """Types of diagrams found in exams."""
    GRAPH = "GRAPH"
    GEOMETRIC_FIGURE = "GEOMETRIC_FIGURE"
    CHART = "CHART"
    ILLUSTRATION = "ILLUSTRATION"
    TABLE = "TABLE"
    CIRCUIT = "CIRCUIT"
    DIAGRAM = "DIAGRAM"
    MAP = "MAP"
    SCIENTIFIC = "SCIENTIFIC"


class ContentSegmentType(str, Enum):
    """Types of content segments within a question."""
    TEXT = "TEXT"
    EQUATION = "EQUATION"
    DIAGRAM_REF = "DIAGRAM_REF"
    TABLE = "TABLE"
    CODE = "CODE"
    CHEMICAL_FORMULA = "CHEMICAL_FORMULA"
    LIST = "LIST"


class Subject(str, Enum):
    """Subject types for exams."""
    MATHEMATICS = "MATHEMATICS"
    SCIENCE = "SCIENCE"
    PHYSICS = "PHYSICS"
    CHEMISTRY = "CHEMISTRY"
    BIOLOGY = "BIOLOGY"
    ENGLISH = "ENGLISH"
    OTHER = "OTHER"


class ExtractionStatus(str, Enum):
    """Status of extraction process."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
