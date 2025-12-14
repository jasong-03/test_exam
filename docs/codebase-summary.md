# Exam Extractor - Codebase Summary

**Project**: Growtrics Exam Extractor
**Version**: 1.0.0
**Last Updated**: 2025-12-14
**Status**: Production-Ready

---

## Overview

The Exam Extractor is a multi-agent Python system that extracts structured questions, diagrams, and answer keys from exam PDF files. It leverages Google's Gemini API for vision-based extraction, with sophisticated post-processing for diagram handling and answer key merging.

**Key Statistics**:
- **Total Files**: 365 (including output files and assets)
- **Source Files**: 16 Python modules
- **Data Models**: 20+ dataclasses
- **Enums**: 5 classification types
- **Agents**: 6 specialized extraction agents
- **Lines of Code**: ~3,500 (source code only)

---

## Directory Structure

```
exam_extractor/
├── agents/                          # Multi-agent extraction system
│   ├── __init__.py                 # Agent package exports
│   ├── orchestrator.py             # Main pipeline coordinator
│   ├── pdf_parser.py               # PDF parsing and image rendering
│   ├── question_extractor.py       # Question extraction from pages
│   ├── diagram_extractor.py        # Diagram cropping and linking
│   ├── answer_key_agent.py         # Answer key extraction
│   └── prompts.py                  # LLM prompts for all agents
│
├── models/                          # Data structures
│   ├── __init__.py                 # Model package exports
│   ├── question.py                 # 12 primary dataclasses
│   └── enums.py                    # 5 classification enums
│
├── tracking/                        # Pipeline observability
│   ├── __init__.py                 # Tracking package exports
│   ├── cost_tracker.py             # Cost and token tracking
│   └── pipeline_logger.py          # Structured event logging
│
├── utils/                           # Utility functions
│   └── __init__.py                 # Utils package exports
│
├── __init__.py                      # Package root exports
├── main.py                          # CLI entry point
│
├── docs/                            # Documentation
│   ├── project-overview-pdr.md
│   ├── codebase-summary.md
│   ├── code-standards.md
│   ├── system-architecture.md
│   └── api-reference.md
│
├── FLOW.md                          # Original pipeline flow
├── FLOW_OPTIMIZED.md               # Optimized 50% cost reduction
└── JSON_EXAMPLES.md                # JSON schemas and examples
```

---

## Module Overview

### 1. Agents Module (`agents/`)

Core extraction logic organized into specialized agents:

#### **OrchestratorAgent** (`orchestrator.py`)
- **Responsibility**: Central pipeline coordinator
- **Key Methods**:
  - `process_pdf(pdf_path, extract_diagrams, extract_answers)` - Main entry point
  - `_detect_page_type(page)` - LLM-based page classification (question vs answer key)
  - `_extract_metadata(pdf_path)` - Filename parsing for exam metadata
  - `_merge_answer_keys_to_questions()` - Attach answer keys to questions
  - `_build_final_result()` - Compile ExamPaper object
- **Dependencies**: All other agents
- **Async**: Yes (async/await pattern)

#### **PDFParserAgent** (`pdf_parser.py`)
- **Responsibility**: PDF parsing and image rendering
- **Key Methods**:
  - `parse_pdf(pdf_path)` - Extract text and render pages
  - `render_pages_as_images(pdf_path, dpi=150)` - Convert pages to PNG
- **Output**: `PageContent` objects with text + image
- **DPI**: 150 (configurable)
- **Dependencies**: PyMuPDF, PIL

#### **QuestionExtractorAgent** (`question_extractor.py`)
- **Responsibility**: Extract questions and diagram references from pages
- **Key Methods**:
  - `extract_questions_from_page(page_image, page_text)` - Single LLM call per page
  - Returns: `(List[Question], List[diagram_info])`
- **LLM Prompt**: `QUESTION_EXTRACTION_PROMPT` (combined extraction, optimized)
- **Confidence**: Included in response (0.0-1.0)
- **Response Format**: JSON with questions array + diagram array

#### **DiagramExtractorAgent** (`diagram_extractor.py`)
- **Responsibility**: Extract diagram images and link to questions (no LLM cost)
- **Key Methods**:
  - `extract_diagrams(page_images, diagram_specs)` - PIL-based cropping
  - `link_diagrams_to_questions()` - Associate diagrams with questions
- **Processing**: Pure Python (PIL), no API calls
- **Bounding Box**: Converts 0-1000 scale (LLM) to 0-100% (storage)
- **Output**: PNG files saved to `output/diagrams/`

#### **AnswerKeyAgent** (`answer_key_agent.py`)
- **Responsibility**: Extract answer keys from designated answer key pages
- **Key Methods**:
  - `extract_answer_keys()` - LLM extraction from answer pages
  - Returns: `Dict[question_number, AnswerKey]`
- **Detection**: Identifies "answer key" pages via LLM classification
- **Optional**: Can be disabled with `extract_answers=False`

#### **Prompts Module** (`prompts.py`)
- **Purpose**: Centralized LLM prompts for all agents
- **Key Prompts**:
  - `LAYOUT_ANALYSIS_PROMPT` - Page type detection
  - `QUESTION_EXTRACTION_PROMPT` - Combined question + diagram extraction
  - `ANSWER_KEY_EXTRACTION_PROMPT` - Extract answers
- **Format**: Detailed instructions for Gemini API
- **JSON Response**: All prompts return JSON for structured parsing

---

### 2. Models Module (`models/`)

Type-safe data structures for exam representation:

#### **Enums** (`enums.py`)

**ResponseType** (8 values):
- `MULTIPLE_CHOICE`, `SHORT_ANSWER`, `LONG_ANSWER`, `WORKING_AREA`
- `FILL_IN_BLANK`, `TRUE_FALSE`, `MATCHING`, `DIAGRAM_LABEL`

**DiagramType** (9 values):
- `GRAPH`, `GEOMETRIC_FIGURE`, `CHART`, `ILLUSTRATION`, `TABLE`
- `CIRCUIT`, `MAP`, `SCIENTIFIC`, `DIAGRAM`

**ContentSegmentType** (7 values):
- `TEXT`, `EQUATION`, `DIAGRAM_REF`, `TABLE`, `CODE`, `CHEMICAL_FORMULA`, `LIST`

**Subject** (7 values):
- `MATHEMATICS`, `PHYSICS`, `CHEMISTRY`, `BIOLOGY`, `SCIENCE`, `ENGLISH`, `OTHER`

**ExtractionStatus** (5 values):
- `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `PARTIAL`

#### **Data Classes** (`question.py`)

**Core Models**:

| Class | Purpose | Key Fields |
|-------|---------|-----------|
| `BoundingBox` | Spatial region on page | x1, y1, x2, y2 (0-100%) |
| `ContentSegment` | Semantic content unit | type, content, order, latex |
| `QuestionContent` | Multi-format question text | text, text_latex, text_html, segments |
| `MCQOption` | Multiple choice option | label, text, is_correct |
| `BlankAnswer` | Fill-in-blank answer | position, expected_answer, acceptable_answers |
| `ResponseConfig` | Response type specifics | options, blanks, word_limit, matching_pairs |
| `WorkedSolutionStep` | Solution step | step_number, description, expression |
| `MarkingCriterion` | Grading rubric item | criterion, marks |
| `AnswerKey` | Complete answer | final_answer, acceptable_answers, worked_solution, marking_rubric |
| `Diagram` | Extracted diagram | id, type, bounding_box, source_page, extraction_confidence |
| `QuestionSource` | PDF location | page_number, bounding_box |
| `Question` | Complete exam question | id, question_number, content, response_type, response_config, diagrams, answer_key, subparts |
| `ExamMetadata` | Exam information | subject, grade_level, exam_type, school, year, total_marks |
| `ExtractionMetrics` | Pipeline metrics | total_tokens_used, total_cost_usd, processing_time_seconds |
| `ExamPaper` | Root object | metadata, questions, extraction_metrics |

**Serialization**:
- All models implement `to_dict()` for JSON serialization
- Recursive serialization for nested objects
- Enum values converted to strings
- Datetime formatted as ISO 8601

---

### 3. Tracking Module (`tracking/`)

Pipeline observability infrastructure:

#### **CostTracker** (`cost_tracker.py`)
- **Classes**: `TokenUsage`, `PipelineMetrics`, `CostTracker`
- **Purpose**: Log API calls, calculate costs, track tokens
- **Pricing Table**: Supports multiple Gemini models:
  - `gemini-2.5-flash`: $0.075 input / $0.30 output per 1M tokens
  - `gemini-2.0-flash`: $0.10 input / $0.40 output per 1M tokens
  - `gemini-1.5-flash`: $0.075 input / $0.30 output per 1M tokens
  - `gemini-1.5-pro`: $1.25 input / $5.00 output per 1M tokens
- **Key Methods**:
  - `start_run(pdf_path)` - Initialize tracking
  - `log_usage(agent, operation, input_tokens, output_tokens, model)` - Record API call
  - `log_error(agent, error, context)` - Record exception
  - `update_counts(questions, diagrams, pages)` - Update output metrics
  - `end_run()` - Finalize and save metrics
  - `print_summary()` - Display formatted stats
- **Output**: JSON files in `output/logs/costs/{run_id}.json`

#### **PipelineLogger** (`pipeline_logger.py`)
- **Classes**: `PipelineLogger`, `ConsoleProgressLogger`
- **Purpose**: Structured event logging and progress tracking
- **Logger Methods**:
  - `log_agent_input/output()` - Agent I/O events
  - `log_agent_prompt()` - Full LLM prompt-response pairs
  - `log_extraction_result()` - Page extraction results
  - `log_error()` - Exception tracking
  - `get_run_logs()` - Retrieve all logs for run
- **Output Structure**: `output/logs/agents/{run_id}/{agent}/*.json`
- **ConsoleProgressLogger**: Simple terminal progress display

---

### 4. Utils Module (`utils/`)

Utility functions (expandable):
- Currently minimal; designed for future helper functions
- Exported via `__init__.py`

---

## Key Classes and Responsibilities

### Class Hierarchy

```
OrchestratorAgent (main coordinator)
├── PDFParserAgent (PDF → images + text)
├── QuestionExtractorAgent (images → questions + diagrams)
├── DiagramExtractorAgent (bounding boxes → PNG files)
├── AnswerKeyAgent (images → answer keys)
└── Tracking Infrastructure
    ├── CostTracker (token counting and costs)
    └── PipelineLogger (event logging)

Data Models
├── ExamPaper (root)
│   ├── ExamMetadata (exam info)
│   ├── Question[] (extracted questions)
│   │   ├── QuestionContent (text + segments)
│   │   ├── ResponseConfig (type-specific options)
│   │   ├── Diagram[] (associated diagrams)
│   │   ├── AnswerKey (solution)
│   │   └── Question[] (subparts - recursive)
│   └── ExtractionMetrics (pipeline stats)
```

---

## Configuration and Constants

### LLM Configuration

```python
Model:              "gemini-2.5-flash"
Temperature:        0.1 (consistent extraction)
Response Format:    "application/json"
```

### Image Processing

```python
PDF DPI:            150 (page rendering resolution)
Bounding Box Scale: 0-1000 (LLM) → 0-100% (stored)
```

### File Organization

```
output/
├── pages/                    # PNG page images
│   └── {pdf_name}_page_N.png
├── diagrams/                 # Cropped diagram PNG files
│   └── pageN_diag_XXX.png
├── questions/                # JSON results
│   ├── {pdf_name}_extracted.json       # Main output
│   ├── answer_keys/
│   │   └── {pdf_name}_answer_keys.json  # Separated answers
│   └── {pdf_name}/
│       ├── q1.json          # Individual questions
│       └── ...
└── logs/
    ├── costs/
    │   └── {run_id}.json    # Cost tracking per run
    └── agents/
        └── {run_id}/{agent}/*.json  # Agent event logs
```

---

## Pipeline Phases (5-Phase Architecture)

### Phase 1: PDF Parsing
**Agent**: `PDFParserAgent`
- Extract text from PDF
- Render pages as PNG images (150 DPI)
- Preserve page order and structure
- **Output**: `List[PageContent]` (text + image per page)

### Phase 2: Metadata Extraction
**Location**: `OrchestratorAgent._extract_metadata()`
- Parse filename for subject, year, grade, exam type, school
- Regex patterns for common naming conventions
- Create `ExamMetadata` object
- **Output**: `ExamMetadata`

### Phase 3: Question & Diagram Extraction (OPTIMIZED)
**Agent**: `QuestionExtractorAgent`
- Single LLM call per page (COMBINED extraction)
- Extract questions AND diagram locations in one response
- Diagram cropping handled post-LLM (Phase 3b)
- **Optimization**: 50% fewer API calls vs original approach
- **Output**: `(List[Question], List[diagram_specs])`

### Phase 3b: Diagram Extraction (No LLM Cost)
**Agent**: `DiagramExtractorAgent`
- Crop diagrams using bounding boxes from Phase 3
- Link to questions spatially
- Save PNG files
- **Output**: `List[Diagram]` (attached to questions)

### Phase 4: Answer Key Extraction (Optional)
**Agent**: `AnswerKeyAgent`
- Detect answer key pages
- Extract answers, working steps, marking rubrics
- Store separately for traceability
- **Output**: `Dict[question_number, AnswerKey]`

### Phase 5: Result Finalization
**Location**: `OrchestratorAgent.process_pdf()`
- Merge answer keys to questions (code-only, no LLM)
- Calculate metrics
- Build `ExamPaper` root object
- Save all output files
- **Output**: `ExamPaper` object + JSON files

---

## Entry Points

### 1. CLI
```bash
python -m exam_extractor.main <pdf_path> [options]
```

**Options**:
- `-o, --output DIR` - Output directory (default: output)
- `-k, --api-key KEY` - Gemini API key
- `--parallel` - Process multiple PDFs concurrently
- `--no-diagrams` - Skip diagram extraction
- `--no-answers` - Skip answer key extraction
- `-v, --verbose` - Debug output

### 2. Python API (via ExamExtractor wrapper)
```python
from exam_extractor import ExamExtractor

extractor = ExamExtractor(api_key="...")
result = extractor.extract("exam.pdf")
```

### 3. Direct Orchestrator
```python
from exam_extractor import OrchestratorAgent

orchestrator = OrchestratorAgent(api_key="...")
result = await orchestrator.process_pdf("exam.pdf")
```

---

## Data Flow

```
PDF File
  ↓
[Phase 1: PDF Parsing]
  ↓ (PageContent list)
[Phase 2: Metadata Extraction]
  ↓ (ExamMetadata + pages)
[Phase 3: Question & Diagram Extraction]
  ↓ (Questions + diagram specs)
[Phase 3b: Diagram Cropping]
  ↓ (Diagrams linked to questions)
[Phase 4: Answer Key Extraction]
  ↓ (Answer keys dict)
[Phase 5: Merge & Finalize]
  ↓ (ExamPaper object)
JSON Output Files
```

---

## Error Handling

**Pipeline Resilience**:
- Errors logged to `ExtractionMetrics.errors`
- Pipeline continues on individual page failures
- Full exception traceback captured
- Non-fatal errors don't stop overall extraction

**Cost Tracking on Error**:
- All API calls logged before error occurs
- Partial metrics available even on failure
- Cost estimates accurate for completed work

---

## Performance Characteristics

**Typical Multi-Page Exam**:
- 10-page exam: ~45-60 seconds
- ~50-80 API calls (varies by question density)
- ~300-500K tokens total
- Cost: $0.10-0.20 USD

**Optimization Highlights**:
- Combined question + diagram extraction: 50% API cost reduction
- Diagram cropping via PIL: No additional LLM calls
- Answer key merging: Pure Python (no LLM)
- Parallelization: Process multiple PDFs concurrently

---

## Testing Capabilities

**Sample Files Included**:
- `sample_pdf/P5_Maths_2023_SA2_acsprimary.pdf` - Primary 5 Math exam
- Multiple test PDF sets in `output/` directory

**Output Validation**:
- JSON schema validation for all output files
- Confidence scores for extraction quality assessment
- Detailed metrics for performance analysis

---

## File Count and Statistics

**Source Code Files**: 16
- 6 agent files
- 2 model files
- 2 tracking files
- Main + init files

**Total Project Files**: 365+
- Includes output files, sample PDFs, generated JSON

**Lines of Code**: ~3,500 (source only)
- Agents: ~1,500 LOC
- Models: ~800 LOC
- Tracking: ~600 LOC
- CLI/Init: ~600 LOC

---

## Dependencies

**Core**:
- `google-generativeai` - Gemini API client
- `PyMuPDF` (fitz) - PDF parsing
- `Pillow` (PIL) - Image processing
- `python-dotenv` - Environment variables

**Testing** (optional):
- `pytest` - Unit testing framework

---

## Future Extensibility

**Planned Modules**:
- `utils/validators.py` - Data validation helpers
- `utils/converters.py` - Format conversion utilities
- Additional diagram type classifiers
- Custom confidence scoring strategies

---

## Document Hierarchy

This file provides a technical overview. For more information, see:

1. **project-overview-pdr.md** - Product requirements and business context
2. **system-architecture.md** - Detailed component interaction diagrams
3. **code-standards.md** - Coding conventions and patterns
4. **api-reference.md** - Complete method signatures and examples

---

**Last Generated**: 2025-12-14
**Repomix Token Count**: 194,052 tokens (full codebase)
**Status**: Production Ready
