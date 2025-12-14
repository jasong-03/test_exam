# Exam Extractor - Code Flow Documentation

## 📋 Execution Flow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAIN ENTRY POINT                              │
│              exam_extractor/main.py                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Parse CLI Arguments                                          │
│    - pdf_paths: PDF file(s) to process                          │
│    - output: Output directory                                   │
│    - api-key: Gemini API key                                    │
│    - parallel: Process multiple PDFs in parallel                │
│    - no-diagrams: Skip diagram extraction                       │
│    - no-answers: Skip answer key extraction                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Initialize OrchestratorAgent                                 │
│    - Creates all sub-agents:                                    │
│      • PDFParserAgent                                           │
│      • QuestionExtractorAgent                                   │
│      • DiagramExtractorAgent                                    │
│      • AnswerKeyAgent                                           │
│    - Initializes CostTracker & PipelineLogger                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. OrchestratorAgent.process_pdf()                         │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ PHASE 1: Parse PDF                                       │ │
│    │ ──────────────────────────────────────────────────────── │ │
│    │ PDFParserAgent.parse(pdf_path)                          │ │
│    │   ├─ Open PDF with PyMuPDF                              │ │
│    │   ├─ For each page:                                     │ │
│    │   │   ├─ Extract text (page.get_text())                 │ │
│    │   │   ├─ Render page as image (PIL Image)               │ │
│    │   │   ├─ Extract embedded images                        │ │
│    │   │   └─ Save page image to output/pages/               │ │
│    │   └─ Return List[PageContent]                          │ │
│    └─────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ PHASE 2: Detect Metadata                                │ │
│    │ ──────────────────────────────────────────────────────── │ │
│    │ _extract_metadata(first_page, filename)                 │ │
│    │   ├─ Parse filename for:                                │ │
│    │   │   ├─ Subject (math, science, etc.)                  │ │
│    │   │   ├─ Year (regex: 20\d{2})                          │ │
│    │   │   ├─ Grade level (P1-P6, S1-S5)                    │ │
│    │   │   ├─ Exam type (SA1, SA2, Prelim, etc.)            │ │
│    │   │   └─ School name                                    │ │
│    │   └─ Return ExamMetadata                                │ │
│    └─────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ PHASE 3: Extract Questions & Diagrams                  │ │
│    │ ──────────────────────────────────────────────────────── │ │
│    │ For each page in pages:                                 │ │
│    │                                                          │ │
│    │   ┌──────────────────────────────────────────────────┐  │ │
│    │   │ 3a. QuestionExtractorAgent.extract_questions()  │  │ │
│    │   │ ──────────────────────────────────────────────── │  │ │
│    │   │   ├─ Build extraction prompt                    │  │ │
│    │   │   ├─ Prepare page image for Gemini              │  │ │
│    │   │   ├─ Call Gemini API:                           │  │ │
│    │   │   │   model.generate_content_async(             │  │ │
│    │   │   │     [prompt] + image_parts,                 │  │ │
│    │   │   │     response_mime_type="application/json"   │  │ │
│    │   │   │   )                                         │  │ │
│    │   │   ├─ Parse JSON response                        │  │ │
│    │   │   ├─ Convert to Question objects                │  │ │
│    │   │   │   • Extract question number                 │  │ │
│    │   │   │   • Extract content (text, LaTeX)           │  │ │
│    │   │   │   • Extract response type                   │  │ │
│    │   │   │   • Extract marks                           │  │ │
│    │   │   │   • Extract subparts (recursive)            │  │ │
│    │   │   ├─ Track token usage & cost                   │  │ │
│    │   │   └─ Return List[Question]                      │  │ │
│    │   └──────────────────────────────────────────────────┘  │ │
│    │                                                          │ │
│    │   ┌──────────────────────────────────────────────────┐  │ │
│    │   │ 3b. DiagramExtractorAgent.extract_diagrams()      │  │ │
│    │   │ ──────────────────────────────────────────────── │  │ │
│    │   │   ├─ Call Gemini API with bounding box detection│  │ │
│    │   │   │   model.generate_content_async(             │  │ │
│    │   │   │     prompt + image,                          │  │ │
│    │   │   │     response_mime_type="application/json"   │  │ │
│    │   │   │   )                                         │  │ │
│    │   │   ├─ Parse bounding boxes (0-1000 scale)        │  │ │
│    │   │   ├─ Convert to pixel coordinates               │  │ │
│    │   │   ├─ Crop diagram images from page              │  │ │
│    │   │   ├─ Save to output/diagrams/                  │  │ │
│    │   │   ├─ Classify diagram type                      │  │ │
│    │   │   │   (graph, table, diagram, formula, etc.)    │  │ │
│    │   │   └─ Return List[Diagram]                       │  │ │
│    │   └──────────────────────────────────────────────────┘  │ │
│    │                                                          │ │
│    │   ┌──────────────────────────────────────────────────┐  │ │
│    │   │ 3c. Link Diagrams to Questions                    │  │ │
│    │   │ ──────────────────────────────────────────────── │  │ │
│    │   │   diagram_extractor.link_diagrams_to_questions()│  │ │
│    │   │   ├─ For each diagram:                          │  │ │
│    │   │   │   ├─ Find nearest question by position      │  │ │
│    │   │   │   └─ Assign diagram to question             │  │ │
│    │   │   └─ Update Question.diagrams                    │  │ │
│    │   └──────────────────────────────────────────────────┘  │ │
│    └─────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ PHASE 4: Extract Answer Keys (if enabled)               │ │
│    │ ──────────────────────────────────────────────────────── │ │
│    │ AnswerKeyAgent.detect_answer_key_pages(pages)           │ │
│    │   ├─ Analyze page content to find answer sections      │ │
│    │   ├─ Use heuristics (keywords, formatting)             │ │
│    │   └─ Return List[int] (page numbers)                   │ │
│    │                                                          │ │
│    │ For each answer page:                                   │ │
│    │   AnswerKeyAgent.extract_answers(page)                  │ │
│    │     ├─ Call Gemini API to extract answers              │ │
│    │     ├─ Parse answer format (A, B, C, D, etc.)          │ │
│    │     ├─ Extract question numbers                        │ │
│    │     └─ Return Dict[str, AnswerKey]                     │ │
│    │                                                          │ │
│    │ AnswerKeyAgent.link_answers_to_questions()              │ │
│    │   ├─ Match answer keys to questions by number         │ │
│    │   └─ Update Question.answer_key                        │ │
│    └─────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              ▼                                  │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ PHASE 5: Build Final Result                            │ │
│    │ ──────────────────────────────────────────────────────── │ │
│    │   ├─ Calculate extraction metrics:                     │ │
│    │   │   • Total tokens used                               │ │
│    │   │   • Total cost (USD)                               │ │
│    │   │   • Processing time                                │ │
│    │   │   • Pages processed                                │ │
│    │   │   • Questions extracted                            │ │
│    │   │   • Diagrams extracted                             │ │
│    │   │                                                      │ │
│    │   ├─ Create ExamPaper object:                          │ │
│    │   │   • metadata: ExamMetadata                          │ │
│    │   │   • questions: List[Question]                       │ │
│    │   │   • extraction_metrics: ExtractionMetrics          │ │
│    │   │                                                      │ │
│    │   ├─ Save results:                                     │ │
│    │   │   • JSON: output/questions/{pdf_name}_extracted.json│ │
│    │   │   • Individual: output/questions/{pdf_name}/q*.json│ │
│    │   │                                                      │ │
│    │   └─ Print summary                                     │ │
│    └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Return ExamPaper object
```

## 🔄 Detailed Agent Flows

### PDFParserAgent Flow
```python
parse(pdf_path) 
  → Open PDF with PyMuPDF
  → For each page:
      → Extract text: page.get_text("text")
      → Render image: page.get_pixmap() → PIL Image
      → Extract embedded images: page.get_images()
      → Save page image to disk
      → Create PageContent object
  → Return List[PageContent]
```

### QuestionExtractorAgent Flow
```python
extract_questions(page_content)
  → Build prompt with instructions
  → Convert page image to Gemini format
  → Call Gemini API (async):
      → Input: prompt + image
      → Config: temperature=0.1, JSON response
  → Parse JSON response
  → Convert to Question objects:
      → Extract question_number
      → Extract content (text, LaTeX)
      → Extract response_type
      → Extract marks
      → Extract subparts (recursive)
  → Track costs
  → Return List[Question]
```

### DiagramExtractorAgent Flow
```python
extract_diagrams(page_content)
  → Build prompt for bounding box detection
  → Call Gemini API (async):
      → Input: prompt + page image
      → Config: JSON response with bounding boxes
  → Parse bounding boxes (0-1000 scale)
  → Convert to pixel coordinates
  → Crop diagram images from page
  → Save to output/diagrams/
  → Classify diagram type
  → Return List[Diagram]

link_diagrams_to_questions(diagrams, questions, page_num)
  → For each diagram:
      → Find nearest question by position
      → Calculate distance
      → Assign diagram to question
  → Update Question.diagrams
```

### AnswerKeyAgent Flow
```python
detect_answer_key_pages(pages)
  → Analyze each page:
      → Check for keywords ("Answer", "Key", etc.)
      → Check formatting patterns
      → Use heuristics
  → Return List[int] (page numbers)

extract_answers(page)
  → Build extraction prompt
  → Call Gemini API (async)
  → Parse answer format
  → Extract question numbers
  → Return Dict[str, AnswerKey]

link_answers_to_questions(questions, answers)
  → For each question:
      → Match by question_number
      → Assign answer_key
  → Update Question.answer_key
```

## 📊 Data Structures

### PageContent
```python
@dataclass
class PageContent:
    page_number: int
    text: str
    image: Optional[Image.Image]
    image_path: Optional[str]
    width: int
    height: int
    has_images: bool
    embedded_images: List[dict]
```

### Question
```python
@dataclass
class Question:
    question_number: Optional[str]
    content: QuestionContent
    response_type: ResponseType
    marks: Optional[int]
    subparts: List[Question]  # Recursive
    diagrams: List[Diagram]
    answer_key: Optional[AnswerKey]
    hierarchy_level: int = 0
```

### ExamPaper
```python
@dataclass
class ExamPaper:
    metadata: ExamMetadata
    questions: List[Question]
    extraction_metrics: ExtractionMetrics
```

## 🔧 Key Configuration Points

1. **Model Name**: `"gemini-2.5-flash"` (hardcoded in each agent)
2. **Temperature**: `0.1` (for consistent extraction)
3. **Response Format**: `application/json` (structured output)
4. **Image DPI**: `150` (for page rendering)
5. **Output Directories**:
   - `output/pages/` - Page images
   - `output/diagrams/` - Extracted diagrams
   - `output/questions/` - JSON results
   - `output/logs/` - Cost and agent logs

## 🚀 Entry Points

### CLI (main.py)
```bash
python -m exam_extractor.main <pdf_path> [options]
```

### Python API
```python
from exam_extractor import ExamExtractor

extractor = ExamExtractor(api_key="...")
result = extractor.extract("exam.pdf")
```

### Direct Orchestrator
```python
from exam_extractor import OrchestratorAgent

orchestrator = OrchestratorAgent(api_key="...")
result = await orchestrator.process_pdf("exam.pdf")
```

## 📝 Error Handling

- All agents log errors to `CostTracker`
- Pipeline continues on individual page failures
- Errors tracked in `ExtractionMetrics.errors`
- Full exception traceback logged

## 💰 Cost Tracking

- Every API call tracked via `CostTracker.log_usage()`
- Token counts (input/output) recorded
- Cost calculated based on model pricing
- Summary saved to `output/logs/costs/`

