# Project Overview and Product Development Requirements

**Project Name**: Growtrics Exam Extractor
**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2025-12-14

---

## Executive Summary

The **Exam Extractor** is an intelligent, multi-agent system designed to automatically extract structured educational content from exam PDF files. It transforms unstructured PDF documents into machine-readable, hierarchically organized question datasets with associated diagrams and answer keys.

**Target Users**: Educational technology developers, curriculum management platforms, assessment systems, and learning analytics solutions.

**Core Value Proposition**: Reduce manual exam digitization time by 95% while maintaining 95%+ extraction accuracy through AI-powered vision processing.

---

## Project Vision and Goals

### Vision Statement
Enable educational institutions to rapidly digitize and structure exam content for integration into modern learning management and assessment systems.

### Strategic Goals
1. **Automation**: Replace manual transcription with intelligent extraction
2. **Accuracy**: Achieve 95%+ accuracy on question extraction
3. **Cost Efficiency**: Process exams at $0.10-0.20 USD per document
4. **Scalability**: Handle 100+ page exams with consistent performance
5. **Accessibility**: Provide both CLI and programmatic interfaces

---

## Product Scope

### What Exam Extractor Does

**Input**: PDF exam papers (typically 5-50 pages)

**Processing**:
- Analyzes page layouts and content types
- Detects and extracts individual questions
- Identifies and crops embedded diagrams
- Extracts answer keys and marking schemes
- Normalizes hierarchical question structures

**Output**: Structured JSON with:
- Question metadata (number, type, marks, subject)
- Question content (text, LaTeX, HTML alternatives)
- Associated diagrams (classified, bounded, extracted)
- Answer keys (final answers, working steps, marking rubrics)
- Extraction metrics (tokens, cost, confidence scores)

### What Exam Extractor Does NOT Do

- Edit or correct extracted content
- Handle handwritten answers
- Process non-PDF document formats
- Store data in databases (outputs JSON files only)
- Provide web UI (CLI and Python API only)

---

## Key Features

### 1. Multi-Agent Orchestration
- **6 Specialized Agents**: Each focused on a specific extraction task
- **Coordinated Pipeline**: 5-phase extraction process with error recovery
- **Async Processing**: Non-blocking I/O for responsive CLI

### 2. Vision-Based Question Extraction
- **Gemini API Integration**: State-of-the-art vision processing
- **Multi-Format Support**: Plain text, LaTeX, HTML alternatives
- **Hierarchical Structure**: Automatic detection of main questions and subparts
- **Confidence Scoring**: 0.0-1.0 confidence per extracted element

### 3. Diagram Detection and Extraction
- **Automatic Cropping**: PIL-based bounding box extraction (no LLM cost)
- **Type Classification**: 9 diagram categories (graphs, geometric figures, tables, etc.)
- **Spatial Linking**: Automatic association with relevant questions
- **Sharing Support**: Single diagram linked to multiple questions

### 4. Answer Key Management
- **Automatic Detection**: Identifies answer key pages within PDFs
- **Multi-Format Answers**: Supports MCQ options, short answers, working steps
- **Marking Rubrics**: Capture partial credit criteria
- **Answer Merging**: Automatic attachment to corresponding questions

### 5. Cost Tracking and Monitoring
- **Real-Time Token Counting**: Track input/output tokens per API call
- **Cost Calculation**: Automatic USD cost estimation
- **Agent Breakdown**: Token usage by agent and operation
- **Performance Metrics**: Processing time, page counts, extraction statistics

### 6. Structured Logging
- **Event Logging**: Detailed logs of agent activities
- **LLM Transparency**: Full prompt-response pairs for debugging
- **Error Tracking**: Comprehensive exception logging with context
- **Audit Trail**: Complete record for quality assurance

### 7. Flexible CLI Interface
- **Single PDF**: `python -m exam_extractor.main exam.pdf`
- **Batch Processing**: Glob patterns and directory scanning
- **Parallel Mode**: Concurrent PDF processing
- **Optional Modules**: Skip diagrams or answers as needed
- **Configuration**: Environment variables or CLI flags

---

## Technical Specifications

### Technology Stack

**Language**: Python 3.10+

**Core Dependencies**:
- `google-generativeai` - Gemini API client for vision processing
- `PyMuPDF` (fitz) - PDF parsing and page extraction
- `Pillow` (PIL) - Image cropping and manipulation
- `python-dotenv` - Environment variable management

**LLM Model**: Google Gemini 2.5 Flash
- **Input Cost**: $0.075 per 1M tokens
- **Output Cost**: $0.30 per 1M tokens
- **Temperature**: 0.1 (low randomness for consistent extraction)
- **Response Format**: Application/JSON (structured output)

**Image Processing**:
- **DPI**: 150 (balance between clarity and file size)
- **Format**: PNG for universal compatibility
- **Bounding Box System**: 0-100% percentage scale (normalized)

### System Architecture

**5-Phase Pipeline**:
1. **PDF Parsing**: Extract text and render pages as images
2. **Metadata Detection**: Parse filename for exam context
3. **Question & Diagram Extraction**: Combined LLM call for 50% cost reduction
4. **Diagram Cropping**: PIL-based extraction (no LLM cost)
5. **Answer Merging**: Code-only phase, no API calls

**Agent Architecture**:
- `PDFParserAgent` - PDF handling
- `QuestionExtractorAgent` - Question recognition
- `DiagramExtractorAgent` - Diagram processing
- `AnswerKeyAgent` - Answer detection
- `OrchestratorAgent` - Pipeline coordination

### Data Model

**Root Object**: `ExamPaper`
- Metadata (subject, grade, year, exam type)
- Questions array (hierarchical with subparts)
- Metrics (tokens, cost, processing time)

**Question Structure**:
- Text content (plain, LaTeX, HTML)
- Response type (MCQ, short answer, working area, etc.)
- Associated diagrams
- Optional answer key
- Hierarchical subparts

**Diagram Metadata**:
- Type classification (9 categories)
- Bounding box coordinates
- Source page reference
- Association with questions
- Base64 image data (optional)

---

## Functional Requirements

### FR-001: PDF Parsing
- **Requirement**: Extract all text and render all pages as images
- **Input**: PDF file path
- **Output**: PageContent objects with text and images
- **Performance**: Complete parsing in < 5 seconds for 30-page exam
- **Error Handling**: Continue on corrupt pages, log errors

### FR-002: Metadata Extraction
- **Requirement**: Detect exam metadata from filename and content
- **Detectable Fields**: Subject, grade level, year, exam type, school
- **Fallback**: Manual metadata input if auto-detection fails
- **Format**: Parsed into ExamMetadata structure

### FR-003: Question Extraction
- **Requirement**: Identify and extract individual questions
- **Response Types**: Support 8 question format types
- **Hierarchies**: Detect main questions and subparts (a, b, c, i, ii, etc.)
- **Confidence**: Assign extraction confidence score
- **Format**: JSON with structured fields

### FR-004: Diagram Extraction
- **Requirement**: Automatically detect, crop, and link diagrams
- **Types**: Classify into 9 diagram categories
- **Processing**: Bounding box extraction via PIL (no LLM cost)
- **Linking**: Spatial association with relevant questions
- **Output**: PNG files + metadata

### FR-005: Answer Key Extraction
- **Requirement**: Identify and extract answer key pages
- **Format Support**: MCQ answers, short answers, working steps, rubrics
- **Merging**: Automatic attachment to corresponding questions
- **Optional**: Can be skipped via `--no-answers` flag

### FR-006: Cost Tracking
- **Requirement**: Log all API usage and calculate costs
- **Tracking**: Input/output tokens per operation
- **Calculation**: Real-time cost estimation
- **Output**: JSON metrics file per run

### FR-007: CLI Interface
- **Requirement**: Command-line tool for processing
- **Single Mode**: Process one PDF at a time
- **Batch Mode**: Process multiple PDFs with glob patterns
- **Parallel Mode**: Concurrent processing for multiple files
- **Options**: Selectively enable/disable features

---

## Non-Functional Requirements

### NFR-001: Performance
- **Requirement**: Process 10-page exam in 45-60 seconds
- **Metric**: ~5-8 seconds per page on average
- **Target**: 99% uptime on Gemini API availability
- **Optimization**: Combined extraction achieves 50% cost reduction

### NFR-002: Accuracy
- **Requirement**: 95%+ extraction accuracy on standard exams
- **Measurement**: Manual review of confidence scores > 0.90
- **Confidence Reporting**: All elements include confidence metrics
- **Quality Assurance**: Detailed logging for error analysis

### NFR-003: Reliability
- **Requirement**: Graceful handling of errors and edge cases
- **Resilience**: Continue on page-level failures
- **Logging**: Comprehensive error tracking and context
- **Recovery**: Partial results on partial failures

### NFR-004: Scalability
- **Requirement**: Handle exams up to 100+ pages
- **Pagination**: Process pages in batches without memory overflow
- **Parallelization**: Support concurrent PDF processing
- **Cost Efficiency**: Linear cost scaling with content volume

### NFR-005: Maintainability
- **Requirement**: Clear, documented code structure
- **Modularity**: Agents are independently testable
- **Extensibility**: Easy to add new agents or data models
- **Documentation**: Comprehensive inline comments and guides

### NFR-006: Security
- **Requirement**: Safe handling of API keys and credentials
- **Method**: Environment variables via .env file
- **No Storage**: No persistent storage of sensitive data
- **Validation**: Input validation on all API calls

---

## Acceptance Criteria

### AC-001: Basic Extraction
- [ ] Extract all questions from standard exam PDF
- [ ] Assign confidence scores to extracted questions
- [ ] Maintain question hierarchy (main/subparts)
- [ ] Support all 8 response types

### AC-002: Diagram Processing
- [ ] Detect all diagrams on pages
- [ ] Classify diagrams into correct categories
- [ ] Crop and save diagram images
- [ ] Link diagrams to questions
- [ ] Handle shared diagrams (multiple questions)

### AC-003: Answer Key Processing
- [ ] Detect answer key pages
- [ ] Extract final answers
- [ ] Extract working steps (where present)
- [ ] Extract marking rubrics
- [ ] Merge answers to questions

### AC-004: Output Format
- [ ] Generate valid JSON output
- [ ] Include all metadata fields
- [ ] Include extraction metrics
- [ ] Save individual question files
- [ ] Create complete ExamPaper object

### AC-005: CLI Functionality
- [ ] Accept PDF file path as argument
- [ ] Support output directory option
- [ ] Support API key via environment or flag
- [ ] Support parallel processing flag
- [ ] Support feature toggle flags

### AC-006: Cost Transparency
- [ ] Track all API calls with token counts
- [ ] Calculate accurate USD cost
- [ ] Generate cost report per run
- [ ] Break down costs by agent
- [ ] Provide real-time cost estimation

### AC-007: Error Handling
- [ ] Log all errors with context
- [ ] Continue on non-critical failures
- [ ] Provide meaningful error messages
- [ ] Save partial results on failure
- [ ] Generate error reports

---

## Data Specifications

### Input
**Format**: PDF document
**Typical Characteristics**:
- Scanned or digital exam papers
- 5-50 pages
- Mix of text, printed text, and diagrams
- Standard letter or A4 size
- Various question formats

**Metadata from Filename** (examples):
- `P5_Maths_2023_SA2.pdf` → Grade P5, Math, Year 2023, SA2
- `S2_Physics_Prelim_Henry Park.pdf` → Grade S2, Physics, Prelim, Henry Park school

### Output
**Primary**: `{pdf_name}_extracted.json` (ExamPaper root)

**Secondary**:
- `{pdf_name}/q1.json`, `q2.json`, etc. (Individual questions)
- `{pdf_name}_answer_keys.json` (Separated answers)
- `{run_id}.json` (Cost metrics)
- `logs/agents/{run_id}/*.json` (Agent event logs)
- `pages/{pdf_name}_page_N.png` (Page images)
- `diagrams/pageN_diag_XXX.png` (Extracted diagrams)

**Format**: Valid JSON with Unicode support
**Schema**: Defined via Python dataclasses with to_dict() serialization

---

## Configuration

### Environment Variables
```bash
GEMINI_API_KEY=your_api_key_here
```

### CLI Configuration
```bash
# All options
python -m exam_extractor.main <pdf_path> \
  --output output/ \
  --api-key YOUR_KEY \
  --parallel \
  --no-diagrams \
  --no-answers \
  -v
```

### Programmatic Configuration
```python
orchestrator = OrchestratorAgent(
    model_name="gemini-2.5-flash",
    output_dir="output",
    api_key="YOUR_KEY",
    enable_logging=True
)
```

---

## Success Metrics

### Extraction Quality
- **Question Extraction Rate**: >95% of questions extracted
- **Accuracy Rate**: >95% of extracted questions correct
- **Confidence Distribution**: 80%+ of extractions with confidence > 0.90

### Diagram Processing
- **Detection Rate**: >90% of diagrams detected
- **Type Accuracy**: >85% correct diagram classification
- **Linking Accuracy**: >90% diagrams linked to correct questions

### Answer Key Processing
- **Detection Rate**: 100% of answer key pages detected
- **Answer Match Rate**: >95% of answers matched to questions
- **Rubric Capture**: 100% of marking rubrics extracted

### System Performance
- **Processing Speed**: 5-8 seconds per page
- **Cost Efficiency**: $0.10-0.20 per exam (10-30 pages)
- **Reliability**: <1% failure rate on valid inputs
- **Error Recovery**: >95% partial extraction on errors

### User Experience
- **CLI Usability**: Single command for basic operation
- **Documentation**: 100% method coverage in docs
- **Error Messages**: Clear, actionable error reporting
- **Configuration**: Easy setup with .env file

---

## Timeline and Milestones

### Version 1.0.0 (Current - Production Ready)
- Complete 5-phase pipeline
- All 6 agents fully functional
- Cost tracking and logging
- CLI and Python API interfaces
- Comprehensive documentation
- Sample test files and examples

### Version 1.1.0 (Planned)
- Custom confidence scoring algorithms
- Enhanced diagram type classification
- Support for additional question formats
- Webhook integration for batch processing

### Version 2.0.0 (Future)
- Web API interface
- Database storage option
- Advanced quality control features
- Multi-language support

---

## Risk Assessment

### Risk 1: PDF Format Variability
**Impact**: High | **Probability**: Medium
**Mitigation**: Comprehensive error handling, detailed logging, graceful degradation

### Risk 2: LLM Extraction Accuracy
**Impact**: High | **Probability**: Low
**Mitigation**: Confidence scoring, manual review workflows, quality assurance

### Risk 3: API Dependency
**Impact**: Medium | **Probability**: Low
**Mitigation**: Error handling, retry logic, cost tracking for transparency

### Risk 4: Scale Performance
**Impact**: Medium | **Probability**: Low
**Mitigation**: Async processing, parallel mode, pagination strategies

---

## Glossary and Terminology

| Term | Definition |
|------|-----------|
| **Exam Paper** | Complete extracted exam document (root object) |
| **Question** | Individual exam question with optional subparts |
| **Subpart** | Question part (a, b, c, etc.) hierarchically nested |
| **Response Type** | Format type expected for question answer |
| **Diagram** | Figure, chart, graph, or illustration in exam |
| **Bounding Box** | Rectangular region coordinates on page image |
| **Answer Key** | Solution including final answer and working steps |
| **Confidence Score** | ML-based confidence metric (0.0-1.0) |
| **Tokens** | LLM processing units for cost calculation |
| **Run ID** | Unique identifier for single extraction session |

---

## References and Related Documents

1. **Technical Overview**: See `codebase-summary.md`
2. **Architecture Details**: See `system-architecture.md`
3. **Code Standards**: See `code-standards.md`
4. **Pipeline Flow**: See `FLOW_OPTIMIZED.md` (original documentation)
5. **JSON Schemas**: See `JSON_EXAMPLES.md` (original documentation)

---

## Approval and Sign-Off

| Role | Name | Date |
|------|------|------|
| Product Manager | [Pending] | - |
| Technical Lead | [Pending] | - |
| QA Lead | [Pending] | - |

---

**Document Version**: 1.0.0
**Last Updated**: 2025-12-14
**Status**: Ready for Review
