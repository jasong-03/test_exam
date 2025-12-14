# System Architecture and Design

**Version**: 1.0.0
**Last Updated**: 2025-12-14
**Status**: Production Ready

---

## Architecture Overview

The Exam Extractor follows a **multi-agent orchestration architecture** with five distinct phases, enabling modular, testable, and maintainable code. The system leverages Google's Gemini API for vision-based extraction while optimizing for cost efficiency through intelligent task combination.

---

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACES                          │
├─────────────────────────────────────────────────────────────────┤
│ CLI (main.py)          │ Python API         │ Direct Orchestrator│
│ Single/batch/parallel  │ ExamExtractor      │ Async processing   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              OrchestratorAgent (Central Coordinator)             │
├─────────────────────────────────────────────────────────────────┤
│ • Manages 5-phase pipeline                                      │
│ • Coordinates all agents                                        │
│ • Handles error recovery and state management                   │
│ • Integrates tracking infrastructure                            │
└──────────┬────────────────┬────────────────┬─────────────┬──────┘
           │                │                │             │
      Phase 1           Phase 2           Phase 3       Phase 4
           │                │                │             │
           ▼                ▼                ▼             ▼
┌──────────────────┐ ┌─────────────┐ ┌──────────────┐ ┌─────────────┐
│ PDFParserAgent   │ │ Metadata    │ │ Question &   │ │ AnswerKey   │
│                  │ │ Extraction  │ │ Diagram      │ │ Agent       │
│ • PDF → Images   │ │             │ │ Extraction   │ │             │
│ • Text extraction│ │ • Filename  │ │             │ │ • Detect    │
│ • DPI rendering  │ │   parsing   │ │ • Combined   │ │   answer    │
│   (150 DPI)      │ │ • Heuristics│ │   LLM call   │ │   pages     │
└──────────────────┘ └─────────────┘ │             │ │ • Extract   │
                                     │ • Single    │ │   answers   │
                                     │   call/page │ │             │
                                     │ • 50% cost  │ │ • Link to   │
                                     │   reduction │ │   questions │
                                     └──────────────┘ └─────────────┘
                                            │
                                            ▼
                                    ┌──────────────────┐
                                    │ DiagramExtractor │
                                    │ (No LLM Cost)    │
                                    │                  │
                                    │ • Crop diagrams  │
                                    │ • Link questions │
                                    │ • Save PNG files │
                                    └──────────────────┘
           │                             │
           └──────────────────┬──────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Tracking Infrastructure                        │
├─────────────────────────────────────────────────────────────────┤
│ CostTracker              │ PipelineLogger                        │
│ • Token counting         │ • Event logging                       │
│ • Cost calculation       │ • LLM prompt/response pairs          │
│ • Usage by agent         │ • Error tracking                      │
│ • Metrics aggregation    │ • Audit trail                         │
└─────────────────────────────────────────────────────────────────┘
           │                                │
           ▼                                ▼
┌──────────────────────┐      ┌─────────────────────────────┐
│ Cost Metrics         │      │ Agent Event Logs            │
│ output/logs/costs/   │      │ output/logs/agents/         │
│ {run_id}.json        │      │ {run_id}/{agent}/*.json     │
└──────────────────────┘      └─────────────────────────────┘
```

---

## 5-Phase Pipeline Architecture

### Phase 1: PDF Parsing

**Purpose**: Convert PDF into structured page data

**Agent**: `PDFParserAgent`

**Flow**:
```
PDF File
  │
  ├─ Extract Text (PyMuPDF)
  │   └─ Preserve order, formatting metadata
  │
  ├─ Render Images (PyMuPDF → PIL)
  │   ├─ DPI: 150 (balance quality/size)
  │   ├─ Format: PNG
  │   └─ Save to output/pages/
  │
  └─ Build PageContent Objects
      └─ text: str (extracted text)
      └─ image: PIL.Image (rendered page)
      └─ page_number: int (0-based)
```

**Output**: `List[PageContent]`

**Characteristics**:
- Non-blocking I/O (async)
- No API calls
- Local processing only
- Preserves all content

---

### Phase 2: Metadata Extraction

**Purpose**: Detect exam information from filename and content

**Location**: `OrchestratorAgent._extract_metadata()`

**Processing**:
```
Filename: "P5_Maths_2023_SA2_HenryPark.pdf"
           │
           ├─ Grade Pattern: P5 → grade_level="P5"
           ├─ Subject: Maths → subject=Subject.MATHEMATICS
           ├─ Year: 2023 → year=2023
           ├─ Exam Type: SA2 → exam_type="SA2"
           └─ School: HenryPark → school="HenryPark"

Result: ExamMetadata object with all fields
```

**Heuristics**:
- Regex patterns for common naming conventions
- Fallback to manual input if auto-detection fails
- Confidence scoring based on match quality

**Output**: `ExamMetadata`

---

### Phase 3: Question & Diagram Extraction (OPTIMIZED)

**Purpose**: Extract questions and diagram references with minimal API cost

**Agent**: `QuestionExtractorAgent`

**Key Optimization**: Single LLM call per page (combined extraction)

```
Page Image + Text
      │
      ├─ Prepare Input
      │   ├─ Encode image as base64 PNG
      │   ├─ Include extracted text
      │   └─ Set JSON response format
      │
      ├─ Send to Gemini API
      │   └─ Prompt: QUESTION_EXTRACTION_PROMPT (optimized)
      │
      ├─ Parse Response
      │   ├─ Extract questions array
      │   ├─ Extract diagram specs array (SAME CALL)
      │   └─ Extract confidence scores
      │
      └─ Build Objects
          ├─ List[Question] with hierarchical structure
          │   ├─ Main questions (hierarchy_level=0)
          │   └─ Subparts (a, b, c - hierarchy_level=1+)
          │
          └─ List[Diagram Specs]
              ├─ type: DiagramType
              ├─ bounding_box: 0-1000 scale (LLM)
              └─ description: str
```

**Optimization Details**:

Original approach (2 calls/page):
1. Call 1: Extract questions only
2. Call 2: Extract diagrams only
3. Cost: 2x tokens, 2x API calls

Current approach (1 call/page):
1. Single call: Extract both in one response
2. Cost: 50% fewer tokens, 50% fewer API calls
3. Method: Modified prompt requests both in single JSON response

**Response Format**:
```json
{
  "questions": [{
    "question_number": "1",
    "question_text": "...",
    "response_type": "MULTIPLE_CHOICE",
    "marks": 5,
    "has_subparts": true,
    "subparts": [...],
    "confidence": 0.95
  }],
  "diagrams": [{
    "diagram_description": "...",
    "diagram_type": "GRAPH",
    "bounding_box": {"x_min": 50, "y_min": 200, ...},
    "associated_question": "1"
  }],
  "page_number": 1,
  "extraction_notes": ""
}
```

**Output**: `(List[Question], List[Diagram Specs])`

---

### Phase 3b: Diagram Extraction (No LLM Cost)

**Purpose**: Extract and link diagram images using bounding boxes

**Agent**: `DiagramExtractorAgent`

**Flow**:
```
Diagram Specs from Phase 3
      │
      ├─ Convert Bounding Box
      │   ├─ Input: 0-1000 scale (LLM format)
      │   ├─ Divide by 10
      │   └─ Output: 0-100% percentage (storage format)
      │
      ├─ Crop from Page Image
      │   ├─ Load page PNG
      │   ├─ Calculate pixel coordinates
      │   ├─ Extract region
      │   └─ Save as PNG to output/diagrams/
      │
      ├─ Link to Questions
      │   ├─ Spatial proximity matching
      │   ├─ Question number association
      │   └─ Handle shared diagrams (multiple questions)
      │
      └─ Build Diagram Objects
          ├─ id: UUID
          ├─ type: DiagramType (from Phase 3)
          ├─ bounding_box: normalized 0-100%
          ├─ source_page: int
          └─ extraction_confidence: float
```

**Key Characteristics**:
- Pure Python processing (PIL)
- NO LLM API calls
- Fast execution (1-2 seconds per page)
- Dependent on Phase 3 bounding boxes

**Bounding Box Conversion**:
```python
# LLM Response (0-1000 scale)
llm_bbox = {"x_min": 50, "y_min": 200, "x_max": 300, "y_max": 400}

# Conversion
stored_bbox = {
    "x1": 50 / 10 = 5.0,      # 5% of page width
    "y1": 200 / 10 = 20.0,    # 20% of page height
    "x2": 300 / 10 = 30.0,    # 30% of page width
    "y2": 400 / 10 = 40.0     # 40% of page height
}
```

**Output**: `List[Diagram]` (attached to questions)

---

### Phase 4: Answer Key Extraction (Optional)

**Purpose**: Extract answers and link to questions

**Agent**: `AnswerKeyAgent`

**Detection Process**:
```
All Pages
    │
    ├─ Classify Each Page
    │   ├─ Send page to LLM with LAYOUT_ANALYSIS_PROMPT
    │   ├─ Get page_type: "question" or "answer_key"
    │   └─ Separate answer key pages
    │
    ├─ Extract from Answer Pages
    │   ├─ Send answers page to LLM
    │   ├─ Extract: {question_ref: AnswerKey}
    │   └─ Capture: final_answer, steps, rubric
    │
    └─ Build AnswerKey Objects
        ├─ final_answer: str
        ├─ acceptable_answers: List[str]
        ├─ worked_solution: List[WorkedSolutionStep]
        └─ marking_rubric: List[MarkingCriterion]
```

**Optional**: Can be skipped with `extract_answers=False` flag

**Output**: `Dict[question_number, AnswerKey]`

---

### Phase 5: Result Finalization and Answer Merging

**Purpose**: Combine all components and prepare output

**Location**: `OrchestratorAgent._build_final_result()` and `_merge_answer_keys_to_questions()`

**Processing**:
```
Questions + Answer Keys
      │
      ├─ Merge Answers (Code Only, No LLM)
      │   ├─ Normalize question numbers for matching
      │   ├─ For MCQ: Mark correct option
      │   ├─ For all: Attach AnswerKey object
      │   └─ Track merge statistics
      │
      ├─ Build Metrics
      │   ├─ Collect cost_tracker.end_run() data
      │   ├─ Calculate processing_time_seconds
      │   ├─ Count pages_processed, questions, diagrams
      │   ├─ List agents_used
      │   └─ Compile errors list
      │
      ├─ Build ExamPaper (Root)
      │   ├─ metadata: ExamMetadata
      │   ├─ questions: List[Question]
      │   └─ extraction_metrics: ExtractionMetrics
      │
      ├─ Serialize to JSON
      │   ├─ Main: {pdf_name}_extracted.json
      │   ├─ Individual: {pdf_name}/q1.json, q2.json, ...
      │   └─ Answers: answer_keys/{pdf_name}_answer_keys.json
      │
      └─ Generate Reports
          ├─ Cost summary to costs/{run_id}.json
          └─ Agent logs to agents/{run_id}/*.json
```

**Answer Merging Example**:
```python
Question: "7a", marks: 3
AnswerKey: final_answer="x=5"

After Merge:
Question.answer_key = {
    "final_answer": "x=5",
    "acceptable_answers": ["x = 5", "5"],
    "worked_solution": [...],
    "marking_rubric": [...]
}

MCQ Case:
Question with options: [A: "Option A", B: "Option B", C: "Correct"]
Answer: "C"

After Merge:
options[0].is_correct = False
options[1].is_correct = False
options[2].is_correct = True
```

**Output**: `ExamPaper` object + JSON files

---

## Agent Interaction Diagram

```
                      OrchestratorAgent
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
    PDFParserAgent  QuestionExtractorAgent  DiagramExtractorAgent
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                        AnswerKeyAgent
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
    CostTracker                        PipelineLogger
    • Token logging                    • Event logging
    • Cost calculation                 • Debug prompts
    • Metrics aggregation              • Error tracking
```

---

## Data Model Hierarchy

```
ExamPaper (Root)
├── metadata: ExamMetadata
│   ├── id: str (UUID)
│   ├── subject: Subject (enum)
│   ├── grade_level: str (P5, S2, etc.)
│   ├── exam_type: str (SA1, SA2, Prelim, etc.)
│   ├── school: str
│   ├── year: int
│   ├── total_marks: int (optional)
│   └── extracted_at: datetime
│
├── questions: List[Question]
│   └── Question (Recursive Structure)
│       ├── id: str (UUID)
│       ├── question_number: str (1, 7a, 3(i), etc.)
│       ├── hierarchy_level: int (0=main, 1+=subpart)
│       ├── parent_question_id: str (optional)
│       ├── content: QuestionContent
│       │   ├── text: str (plain)
│       │   ├── text_latex: str (optional)
│       │   ├── text_html: str (optional)
│       │   └── segments: List[ContentSegment]
│       │       ├── type: ContentSegmentType
│       │       ├── content: str
│       │       └── latex: str (optional)
│       │
│       ├── response_type: ResponseType (enum)
│       │   └── Enum: MULTIPLE_CHOICE, SHORT_ANSWER, etc.
│       │
│       ├── response_config: ResponseConfig
│       │   ├── options: List[MCQOption] (for MCQ)
│       │   │   ├── label: str (A, B, C, D)
│       │   │   ├── text: str
│       │   │   └── is_correct: bool
│       │   ├── blanks: List[BlankAnswer] (for FILL_IN_BLANK)
│       │   ├── word_limit: int (for LONG_ANSWER)
│       │   └── matching_pairs: List[Dict] (for MATCHING)
│       │
│       ├── diagrams: List[Diagram]
│       │   ├── id: str (UUID)
│       │   ├── type: DiagramType (enum)
│       │   ├── bounding_box: BoundingBox (0-100%)
│       │   │   ├── x1, y1, x2, y2: float
│       │   │   └── Represents percentage of page
│       │   ├── source_page: int
│       │   └── extraction_confidence: float (0.0-1.0)
│       │
│       ├── answer_key: AnswerKey (optional)
│       │   ├── final_answer: str
│       │   ├── acceptable_answers: List[str]
│       │   ├── worked_solution: List[WorkedSolutionStep]
│       │   │   ├── step_number: int
│       │   │   ├── description: str
│       │   │   └── expression: str (optional)
│       │   └── marking_rubric: List[MarkingCriterion]
│       │       ├── criterion: str
│       │       └── marks: float
│       │
│       ├── subparts: List[Question] (recursive)
│       ├── marks: float (optional)
│       └── extraction_confidence: float (0.0-1.0)
│
└── extraction_metrics: ExtractionMetrics
    ├── total_tokens_used: int
    ├── total_cost_usd: float
    ├── processing_time_seconds: float
    ├── pages_processed: int
    ├── questions_extracted: int
    ├── diagrams_extracted: int
    ├── agents_used: List[str]
    └── errors: List[Dict]
```

---

## Data Flow Diagram

```
Input: PDF File
         │
         ▼
    Phase 1: PDF Parsing
    ├─ Output: List[PageContent]
    └─ Contains: text + image per page
         │
         ▼
    Phase 2: Metadata Detection
    ├─ Output: ExamMetadata
    └─ Contains: subject, grade, year, exam_type
         │
         ▼
    Phase 3: Question Extraction
    ├─ Output: List[Question] + diagram_specs
    ├─ Processing: Single LLM call/page
    └─ Confidence: Extracted from LLM response
         │
         ▼
    Phase 3b: Diagram Extraction
    ├─ Output: List[Diagram]
    ├─ Processing: PIL cropping (no LLM)
    └─ Linking: Spatial association with questions
         │
         ▼
    Phase 4: Answer Key Extraction (Optional)
    ├─ Output: Dict[question_ref, AnswerKey]
    ├─ Detection: LLM page type classification
    └─ Merging: Question number matching
         │
         ▼
    Phase 5: Finalization
    ├─ Merge answers to questions
    ├─ Compile metrics
    ├─ Build ExamPaper object
    └─ Save JSON files
         │
         ▼
Output: ExamPaper + JSON Files + Diagrams
```

---

## Cost Optimization Strategy

### Original Approach (vs. Current)

**Original** (2 calls per page):
```
Page 1 → Call 1: Extract questions
      ↘ Call 2: Extract diagrams
      ═ 2 API calls × 36 pages = 72 total calls
      ═ Cost: ~$0.25-0.30 per exam
```

**Current** (1 call per page):
```
Page 1 → Single Call: Extract questions + diagrams (combined)
      ═ 1 API call × 36 pages = 36 total calls
      ═ Cost: ~$0.12-0.15 per exam
      ═ Savings: 50% cost reduction
```

### Cost Reduction Mechanisms

1. **Combined Extraction Prompt**
   - Single LLM call returns both questions and diagrams
   - Modified prompt structure: requests both in single JSON response
   - Eliminates redundant page analysis

2. **Diagram Cropping (No LLM)**
   - Bounding boxes from Phase 3 used for cropping
   - PIL-based extraction (local, fast, free)
   - No additional API calls

3. **Answer Merging (No LLM)**
   - Pure Python matching by question number
   - No additional API calls
   - Deterministic processing

4. **Model Selection**
   - Using `gemini-2.5-flash` (optimal cost-performance)
   - Input: $0.075/M tokens
   - Output: $0.30/M tokens

---

## Error Handling and Recovery

### Pipeline Resilience

```
PDF Processing
    │
    ├─ Phase 1: PDF Parsing
    │   ├─ Error: Continue on corrupt page
    │   └─ Log: Add to extraction_metrics.errors
    │
    ├─ Phase 2: Metadata Detection
    │   ├─ Error: Use defaults or prompt user
    │   └─ Log: Warning level
    │
    ├─ Phase 3: Question Extraction (Per Page)
    │   ├─ Error: Skip page, log error
    │   └─ Continue: Process next page
    │
    ├─ Phase 3b: Diagram Extraction
    │   ├─ Error: Skip diagram, continue
    │   └─ Log: Add to errors
    │
    ├─ Phase 4: Answer Key Extraction
    │   ├─ Error: Disable answer merging
    │   └─ Continue: Return questions without answers
    │
    └─ Phase 5: Finalization
        ├─ Error: Return partial ExamPaper
        └─ Log: Comprehensive error report
```

### Cost Tracking on Error

```
API Call 1 ✓ → Logged cost
API Call 2 ✓ → Logged cost
API Call 3 ✗ → Error occurs
     │
     ├─ Log error with context
     ├─ Finalize cost tracker
     └─ Return metrics for successful calls

Result: Accurate cost for completed work
```

---

## Scalability Considerations

### Single PDF Processing
- Linear time with page count
- Typical: 5-8 seconds per page
- Memory: ~100-200 MB per page

### Batch Processing

**Sequential Mode**:
```
PDF 1 → Process → Save
PDF 2 → Process → Save
PDF 3 → Process → Save
Total: sum of individual times
```

**Parallel Mode**:
```
PDF 1 ─┐
PDF 2 ─┼─ Concurrent Processing
PDF 3 ─┘
Total: max of individual times (3x faster)
```

### Implementation
```python
# Parallel processing via asyncio.gather()
tasks = [orchestrator.process_pdf(path) for path in pdf_paths]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

---

## API Integration Points

### Gemini API Calls

1. **Layout Analysis** (Page Type Detection)
   - Input: Page image
   - Prompt: `LAYOUT_ANALYSIS_PROMPT`
   - Output: `page_type` ("question" or "answer_key")

2. **Question Extraction** (Combined)
   - Input: Page image + text
   - Prompt: `QUESTION_EXTRACTION_PROMPT`
   - Output: Questions + diagram specs (JSON)

3. **Answer Key Extraction**
   - Input: Answer key page image
   - Prompt: `ANSWER_KEY_EXTRACTION_PROMPT`
   - Output: Answer dictionary (JSON)

### Response Format
All LLM calls configured for JSON response:
```python
response_config = {"response_mime_type": "application/json"}
```

---

## Output Directory Structure

```
output/
├── pages/
│   └── {pdf_name}_page_1.png
│   └── {pdf_name}_page_2.png
│   └── ...
│
├── diagrams/
│   └── page1_diag_abc123.png
│   └── page2_diag_def456.png
│   └── ...
│
├── questions/
│   ├── {pdf_name}_extracted.json          (Main ExamPaper)
│   ├── {pdf_name}/
│   │   ├── q1.json                        (Individual questions)
│   │   ├── q2.json
│   │   ├── q3a.json
│   │   └── ...
│   └── answer_keys/
│       └── {pdf_name}_answer_keys.json    (Separated answers)
│
└── logs/
    ├── costs/
    │   └── {run_id}.json                  (Cost metrics)
    │
    └── agents/
        └── {run_id}/
            ├── Orchestrator/
            │   └── *.json
            ├── QuestionExtractor/
            │   └── *.json
            ├── DiagramExtractor/
            │   └── *.json
            └── AnswerKeyAgent/
                └── *.json
```

---

## Performance Characteristics

### Token Usage Profile

**Per Page Estimate**:
- Page Type Detection: 1,000-2,000 input, 200-500 output
- Question Extraction: 8,000-15,000 input, 12,000-25,000 output
- Total/page: 9,000-17,000 input, 12,200-25,500 output

**10-Page Exam**:
- Total tokens: 200,000-400,000
- API calls: ~20-30
- Cost: $0.10-0.20 USD
- Time: 45-60 seconds

### Memory Profile

**Per Page**:
- Page image (PNG): 50-100 MB in memory
- Text extraction: 1-10 MB
- Question objects: 1-5 MB
- Total/page: ~100-200 MB

**Peak Usage**:
- Loading single page image
- Storing question/diagram data structures
- Typical max: 500 MB for large exams

### Network Profile

**API Calls**:
- Average: ~2-3 per page
- Round-trip: 2-5 seconds per call
- Total: 20-50 seconds per exam

---

## Future Architecture Considerations

### Potential Enhancements

1. **Question Deduplication**
   - Detect repeated questions across pages
   - Merge metadata

2. **Advanced Confidence Scoring**
   - Cross-validation between questions
   - Consistency checking

3. **Custom Diagram Processing**
   - ML-based type classification
   - Quality validation

4. **Database Integration**
   - Optional direct storage
   - Query interface

5. **Web Service**
   - REST API wrapper
   - Async job queue
   - WebSocket progress updates

---

**Document Version**: 1.0.0
**Last Updated**: 2025-12-14
**Status**: Production Ready
**Architecture Review**: Quarterly
