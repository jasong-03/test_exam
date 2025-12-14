# Code Standards and Implementation Guidelines

**Version**: 1.0.0
**Last Updated**: 2025-12-14
**Status**: Active Standards

---

## Overview

This document establishes coding standards, conventions, and best practices for the Exam Extractor project. These standards ensure consistency, maintainability, and quality across the codebase.

---

## Table of Contents

1. [Python Version and Environment](#python-version-and-environment)
2. [File Organization](#file-organization)
3. [Naming Conventions](#naming-conventions)
4. [Type Hints and Type Safety](#type-hints-and-type-safety)
5. [Dataclass Patterns](#dataclass-patterns)
6. [JSON Serialization](#json-serialization)
7. [Async/Await Patterns](#asyncawait-patterns)
8. [Error Handling](#error-handling)
9. [Logging Standards](#logging-standards)
10. [Testing Strategy](#testing-strategy)
11. [Documentation Standards](#documentation-standards)
12. [Code Review Checklist](#code-review-checklist)

---

## Python Version and Environment

### Minimum Version
- **Python**: 3.10 or higher
- **Reason**: Type hints, match statements, improved async support

### Virtual Environment
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dependencies Management
- **Lock File**: `requirements.txt` (pinned versions)
- **Update Process**: Review and test before updating
- **Security**: Run `pip audit` regularly

### Environment Configuration
```bash
# .env file format
GEMINI_API_KEY=your_api_key_here
LOG_LEVEL=INFO
OUTPUT_DIR=output
```

---

## File Organization

### Module Structure
```python
# Standard module header
"""Module description - single line overview.

Detailed description if needed.
Multi-line description of purpose and key classes.
"""

# Imports in this order:
# 1. Standard library
# 2. Third-party
# 3. Local imports

from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
from datetime import datetime

import google.generativeai as genai

from ..models import Question, Diagram
from .pdf_parser import PDFParserAgent
```

### File Naming
- **Modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`

### Directory Organization
```
exam_extractor/
├── agents/          # All agent classes
├── models/          # Data structures
├── tracking/        # Observability
├── utils/           # Utilities
├── docs/            # Documentation
└── tests/           # Unit tests (future)
```

---

## Naming Conventions

### Classes
```python
# Good
class QuestionExtractorAgent:
    pass

class ExamMetadata:
    pass

# Bad
class question_extractor:
    pass

class exam_metadata:
    pass
```

### Functions and Methods
```python
# Good - verb-first for actions
def extract_questions_from_page():
    pass

def parse_pdf():
    pass

# Good - descriptor for properties
def get_current_stats():
    pass

# Bad
def Questions_From_Page():
    pass

def pdf_parse():
    pass
```

### Variables
```python
# Good
page_content = PageContent(...)
question_list = [q1, q2, q3]
is_answer_key = True

# Bad
pageContent = PageContent(...)  # camelCase
QuestionList = [q1, q2, q3]    # PascalCase
isAnswerKey = True              # camelCase
```

### Constants
```python
# Module-level constants
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0.1
MAX_PAGES_PER_BATCH = 20

# Enum-like constants
RESPONSE_TYPES = {
    "MULTIPLE_CHOICE": 1,
    "SHORT_ANSWER": 2,
}
```

### Private Methods/Attributes
```python
class OrchestratorAgent:
    def __init__(self):
        self._logger = logging.getLogger(...)  # Private instance var
        self._cache = {}                        # Private storage

    def _detect_page_type(self):               # Private method
        pass

    async def process_pdf(self):               # Public method
        pass
```

---

## Type Hints and Type Safety

### Required Type Hints
All public methods must have complete type hints:

```python
# Good
async def extract_questions(
    self,
    page_image: str,
    page_text: str
) -> Tuple[List[Question], List[Dict[str, Any]]]:
    """Extract questions and diagram info from page."""
    ...

def link_diagrams_to_questions(
    self,
    questions: List[Question],
    diagrams: List[Diagram]
) -> List[Question]:
    """Link diagrams to corresponding questions."""
    ...

# Bad - missing return type
async def extract_questions(self, page_image, page_text):
    """Extract questions."""
    ...

# Bad - incomplete types
def link_diagrams(self, questions, diagrams):
    ...
```

### Optional Types
```python
# Good - use Optional for nullable values
def get_diagram(self, diagram_id: str) -> Optional[Diagram]:
    if diagram_exists:
        return diagram
    return None

# Good - use Union for multiple types
def parse_value(self, value: str | int | float) -> float:
    ...

# Bad - ambiguous None handling
def get_diagram(self, diagram_id):
    ...
```

### Generic Types
```python
# Good
def get_questions_by_type(
    self,
    response_type: ResponseType
) -> List[Question]:
    ...

def get_metrics(self) -> Dict[str, int]:
    return {
        "total_questions": 10,
        "total_diagrams": 5
    }

# Use Union for complex types
from typing import Union
ParseResult = Union[Question, Diagram, None]
```

---

## Dataclass Patterns

### Basic Dataclass Pattern
```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

@dataclass
class MyModel:
    """Model description."""

    # Required fields (no defaults)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str

    # Optional fields
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Auto-timestamp fields
    created_at: datetime = field(default_factory=datetime.now)
```

### Serialization Methods
Every dataclass must implement `to_dict()`:

```python
@dataclass
class Question:
    id: str
    question_number: str
    content: QuestionContent
    response_type: ResponseType
    subparts: List["Question"] = field(default_factory=list)
    answer_key: Optional[AnswerKey] = None

    def to_dict(self) -> Dict[str, Any]:
        """Recursive serialization to dict."""
        return {
            "id": self.id,
            "question_number": self.question_number,
            "content": self.content.to_dict(),
            "response_type": self.response_type.value,  # Enum to string
            "subparts": [s.to_dict() for s in self.subparts],
            "answer_key": self.answer_key.to_dict() if self.answer_key else None
        }
```

### Factory Methods
```python
@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "BoundingBox":
        """Create from dictionary (deserialization)."""
        return cls(
            x1=data["x1"],
            y1=data["y1"],
            x2=data["x2"],
            y2=data["y2"]
        )

    @classmethod
    def from_llm_response(cls, llm_bbox: Dict[str, int]) -> "BoundingBox":
        """Convert from LLM 0-1000 scale to 0-100% scale."""
        return cls(
            x1=llm_bbox["x_min"] / 10,
            y1=llm_bbox["y_min"] / 10,
            x2=llm_bbox["x_max"] / 10,
            y2=llm_bbox["y_max"] / 10
        )
```

### Frozen Dataclasses (for immutability)
```python
@dataclass(frozen=True)
class Subject:
    """Immutable subject identifier."""
    name: str
    code: str

    # Note: Cannot modify after creation
```

---

## JSON Serialization

### Export Pattern
```python
import json
from datetime import datetime

@dataclass
class ExamPaper:
    # ...fields...

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "questions": [q.to_dict() for q in self.questions],
            "extraction_metrics": self.extraction_metrics.to_dict()
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        data = self.to_dict()
        return json.dumps(data, indent=indent, ensure_ascii=False)

    def save_to_file(self, filepath: Path) -> None:
        """Write JSON to file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
```

### Enum Serialization
```python
from enum import Enum

class ResponseType(str, Enum):
    """Response type enum with string serialization."""
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    SHORT_ANSWER = "SHORT_ANSWER"
    LONG_ANSWER = "LONG_ANSWER"
    # ...

    # JSON serializes automatically to string value
    def to_dict(self):
        return self.value
```

### DateTime Serialization
```python
from datetime import datetime
import json

class DateTimeEncoder(json.JSONEncoder):
    """Custom encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # ISO 8601 format
        return super().default(obj)

# Usage:
json_str = json.dumps(data, cls=DateTimeEncoder, ensure_ascii=False)
```

---

## Async/Await Patterns

### Async Method Declaration
```python
class OrchestratorAgent:
    # Good - explicitly async
    async def process_pdf(
        self,
        pdf_path: str,
        extract_diagrams: bool = True
    ) -> ExamPaper:
        """Main extraction pipeline (async)."""
        # Await all async operations
        pages = await self.pdf_parser.parse_pdf(pdf_path)
        questions = await self.question_extractor.extract(pages)
        return await self._build_result(questions)

    # Supporting sync methods (non-blocking I/O)
    def _validate_input(self, pdf_path: str) -> bool:
        """Validate input without blocking."""
        return Path(pdf_path).exists()
```

### Running Async Code
```python
# In CLI/main.py
import asyncio

async def main():
    orchestrator = OrchestratorAgent()
    result = await orchestrator.process_pdf("exam.pdf")
    return result

# Run from synchronous context
if __name__ == "__main__":
    result = asyncio.run(main())
```

### Parallel Processing
```python
async def process_multiple_pdfs(
    self,
    pdf_paths: List[str]
) -> List[ExamPaper]:
    """Process multiple PDFs concurrently."""
    tasks = [
        self.process_pdf(path)
        for path in pdf_paths
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions in results
    papers = []
    for result in results:
        if isinstance(result, Exception):
            self._logger.error(f"Processing failed: {result}")
        else:
            papers.append(result)
    return papers
```

### Async Context Managers
```python
class ResourceManager:
    async def __aenter__(self):
        """Acquire resource."""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release resource."""
        await self.cleanup()

# Usage
async with ResourceManager() as rm:
    result = await rm.do_something()
```

---

## Error Handling

### Exception Hierarchy
```python
# Good - specific exceptions
class ExamExtractorException(Exception):
    """Base exception for exam extractor."""
    pass

class PDFParsingError(ExamExtractorException):
    """Error during PDF parsing."""
    pass

class ExtractionError(ExamExtractorException):
    """Error during content extraction."""
    pass

class ValidationError(ExamExtractorException):
    """Error during data validation."""
    pass

# Usage
try:
    parse_pdf()
except PDFParsingError as e:
    logger.error(f"PDF parsing failed: {e}")
    # Handle specifically
except ExamExtractorException as e:
    logger.error(f"Extraction error: {e}")
    # Handle generally
```

### Pipeline Resilience
```python
async def process_pdf(self, pdf_path: str) -> ExamPaper:
    """Process with graceful error handling."""
    run_id = self.cost_tracker.start_run(pdf_path)

    try:
        # Phase 1: Parse
        pages = await self.pdf_parser.parse_pdf(pdf_path)

        # Phase 2-5: Extract
        questions = []
        for i, page in enumerate(pages):
            try:
                page_questions = await self.extract_page(page)
                questions.extend(page_questions)
            except Exception as e:
                # Log but continue
                self.cost_tracker.log_error("Orchestrator", e, {"page": i})
                logger.warning(f"Failed to extract page {i}: {e}")

        return ExamPaper(questions=questions, ...)

    except Exception as e:
        # Log critical failure
        self.cost_tracker.log_error("Orchestrator", e)
        logger.error(f"Pipeline failed: {e}")
        raise

    finally:
        # Always finalize tracking
        metrics = self.cost_tracker.end_run()
        logger.info(f"Pipeline complete. Cost: ${metrics.total_cost:.4f}")
```

### Context and Error Information
```python
try:
    extract_something()
except ValueError as e:
    context = {
        "page": current_page,
        "question_id": question_id,
        "operation": "extract_questions",
        "timestamp": datetime.now().isoformat()
    }
    logger.error(
        f"Extraction failed: {str(e)}",
        extra={"context": context}
    )
    self.cost_tracker.log_error(
        agent="QuestionExtractor",
        error=e,
        context=context
    )
```

---

## Logging Standards

### Logger Initialization
```python
import logging

class MyAgent:
    def __init__(self):
        # One logger per class
        self._logger = logging.getLogger(self.__class__.__name__)
```

### Logging Levels
```python
# CRITICAL - System cannot continue
self._logger.critical("Database connection lost, shutting down")

# ERROR - Operation failed, but system continues
self._logger.error(f"Failed to extract page {i}: {e}")

# WARNING - Unexpected but recoverable
self._logger.warning(f"Low confidence extraction: {confidence}")

# INFO - Normal flow information
self._logger.info(f"Processing started for {pdf_path}")

# DEBUG - Detailed debugging information
self._logger.debug(f"Page type detected: {page_type}, confidence: {conf}")
```

### Structured Logging with Context
```python
# Good - include relevant context
self._logger.info(
    f"Extraction complete",
    extra={
        "questions": len(questions),
        "diagrams": len(diagrams),
        "processing_time_seconds": elapsed,
        "cost_usd": cost,
        "pdf_path": pdf_path
    }
)

# Bad - vague logging
self._logger.info("Done")
self._logger.info("Questions: " + str(questions))
```

### PipelineLogger Usage
```python
# Log LLM interactions
self.pipeline_logger.log_agent_prompt(
    agent="QuestionExtractor",
    operation="extract_questions",
    prompt="Extract questions from: ...",
    response='{"questions": [...]}',
    model="gemini-2.5-flash"
)

# Log errors with context
self.pipeline_logger.log_error(
    agent="DiagramExtractor",
    operation="extract_diagrams",
    error=e,
    context={"page": 3, "diagram_count": 5}
)

# Log extraction results
self.pipeline_logger.log_extraction_result(
    agent="QuestionExtractor",
    page_number=1,
    result={"questions": [...], "confidence": 0.95}
)
```

---

## Testing Strategy

### Test File Organization
```
tests/
├── test_pdf_parser.py
├── test_question_extractor.py
├── test_diagram_extractor.py
├── test_orchestrator.py
├── test_models.py
└── test_tracking.py
```

### Test Naming Convention
```python
# Good
def test_extract_questions_returns_list():
    pass

def test_extract_questions_with_empty_page_returns_empty_list():
    pass

def test_bounding_box_from_llm_converts_scale_correctly():
    pass

# Bad
def test_extraction():
    pass

def test_1():
    pass
```

### Unit Test Pattern
```python
import pytest
from pathlib import Path

class TestQuestionExtractor:
    """Tests for QuestionExtractorAgent."""

    @pytest.fixture
    def extractor(self):
        """Initialize extractor for tests."""
        return QuestionExtractorAgent(api_key="test_key")

    @pytest.fixture
    def sample_page(self):
        """Load sample page for testing."""
        return PageContent(
            text="Question 1: ...",
            image=Image.open("tests/fixtures/page.png")
        )

    def test_extract_returns_questions(self, extractor, sample_page):
        """Verify extraction returns question list."""
        questions, diagrams = extractor.extract(sample_page)
        assert isinstance(questions, list)
        assert len(questions) > 0

    def test_extract_preserves_question_number(self, extractor, sample_page):
        """Verify question numbers are preserved."""
        questions, _ = extractor.extract(sample_page)
        assert questions[0].question_number == "1"
```

---

## Documentation Standards

### Module Docstrings
```python
"""Module for PDF parsing and image rendering.

This module provides the PDFParserAgent class which handles:
- Extracting text from PDF files
- Rendering pages as high-quality images
- Preserving page order and structure

Example:
    >>> parser = PDFParserAgent()
    >>> pages = await parser.parse_pdf("exam.pdf")
    >>> for page in pages:
    ...     print(f"Page {page.page_number}: {len(page.text)} chars")
"""
```

### Function/Method Docstrings
```python
def extract_questions(
    self,
    page_image: str,
    page_text: str
) -> Tuple[List[Question], List[Dict[str, Any]]]:
    """Extract questions and diagram references from a page.

    Sends page image to Gemini API with optimized prompt to extract
    questions and diagram information in a single LLM call.

    Args:
        page_image: Base64-encoded PNG image of the page
        page_text: Extracted text content of the page

    Returns:
        Tuple containing:
        - List[Question]: Extracted questions with metadata
        - List[Dict]: Diagram specifications with bounding boxes

    Raises:
        ExtractionError: If LLM call fails or response is invalid
        ValueError: If inputs are empty or invalid format

    Example:
        >>> agent = QuestionExtractorAgent()
        >>> page_image = base64.b64encode(page_bytes)
        >>> page_text = "Question 1: ..."
        >>> questions, diagrams = await agent.extract_questions(
        ...     page_image, page_text
        ... )
        >>> print(f"Found {len(questions)} questions")
    """
```

### Inline Comments
```python
def _merge_answer_keys_to_questions(
    self,
    questions: List[Question],
    answer_keys: Dict[str, AnswerKey]
) -> int:
    """Merge answer keys to corresponding questions."""
    merged_count = 0

    for question in questions:
        # Normalize question number for matching
        # (e.g., "7a" matches "7(a)", "7. a", etc.)
        normalized_num = self._normalize_question_number(question.question_number)

        if normalized_num in answer_keys:
            # Attach the answer key
            question.answer_key = answer_keys[normalized_num]

            # For MCQ, mark the correct option
            if question.response_type == ResponseType.MULTIPLE_CHOICE:
                answer_text = answer_keys[normalized_num].final_answer
                for option in question.response_config.options:
                    option.is_correct = (option.label == answer_text)

            merged_count += 1

    return merged_count
```

---

## Code Review Checklist

### Before Submitting Code

- [ ] **Type Hints**: All public methods have complete type hints
- [ ] **Dataclasses**: All models implement `to_dict()` method
- [ ] **Naming**: Functions (snake_case), Classes (PascalCase), Constants (UPPER_CASE)
- [ ] **Docstrings**: All public methods documented with Args/Returns/Raises
- [ ] **Error Handling**: Exceptions caught and logged appropriately
- [ ] **Logging**: DEBUG, INFO, WARNING, ERROR used appropriately
- [ ] **Testing**: Unit tests written for new functionality
- [ ] **Async**: Async methods properly declared and awaited
- [ ] **Comments**: Inline comments explain "why" not "what"
- [ ] **Imports**: Organized (stdlib, third-party, local)
- [ ] **No Secrets**: No API keys or credentials in code
- [ ] **Linting**: Code passes flake8 or similar linter
- [ ] **Performance**: No obvious inefficiencies
- [ ] **Security**: Input validation on untrusted data
- [ ] **Compatibility**: Compatible with Python 3.10+

### Review Criteria for Reviewers

- [ ] Code follows established standards
- [ ] Logic is clear and maintainable
- [ ] Error cases are handled
- [ ] Performance is acceptable
- [ ] Tests provide good coverage
- [ ] Documentation is accurate and complete
- [ ] No security vulnerabilities introduced
- [ ] Changes align with project architecture

---

## Best Practices Summary

1. **Always Use Type Hints** - Make code self-documenting
2. **Implement to_dict()** - Enable JSON serialization
3. **Use Specific Exceptions** - Catch and handle appropriately
4. **Log with Context** - Include relevant details
5. **Document Public APIs** - Docstrings for all public methods
6. **Write Async Code Correctly** - Declare and await properly
7. **Validate Input** - Check data before processing
8. **Handle Errors Gracefully** - Continue when possible, fail fast when necessary
9. **Keep Functions Focused** - One responsibility per function
10. **Test Critical Paths** - At least 80% code coverage

---

**Version**: 1.0.0
**Last Updated**: 2025-12-14
**Status**: Active
**Review Cycle**: Annually
