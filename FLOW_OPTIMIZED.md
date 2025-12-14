# Exam Extractor - Optimized Code Flow Documentation

## 📋 Execution Flow Overview (After Optimization)

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
│ 3. OrchestratorAgent.process_pdf()                              │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ PHASE 1: Parse PDF                                       │ │
│    │ ──────────────────────────────────────────────────────── │ │
│    │ PDFParserAgent.parse(pdf_path)                          │ │
│    │   ├─ Open PDF with PyMuPDF                              │ │
│    │   ├─ For each page:                                     │ │
│    │   │   ├─ Extract text (page.get_text())                 │ │
│    │   │   ├─ Render page as image (PIL Image, 150 DPI)     │ │
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
│    │ PHASE 3: Extract Questions & Diagrams (OPTIMIZED) ⚡    │ │
│    │ ──────────────────────────────────────────────────────── │ │
│    │ For each page in pages:                                 │ │
│    │                                                          │ │
│    │   ┌──────────────────────────────────────────────────┐  │ │
│    │   │ 3a. QuestionExtractorAgent.extract_questions()   │  │ │
│    │   │ ⚡ SINGLE LLM CALL - Combined extraction         │  │ │
│    │   │ ──────────────────────────────────────────────── │  │ │
│    │   │   ├─ Build extraction prompt (with diagram req)  │  │ │
│    │   │   ├─ Prepare page image for Gemini              │  │ │
│    │   │   ├─ Call Gemini API ONCE:                       │  │ │
│    │   │   │   model.generate_content_async(               │  │ │
│    │   │   │     [prompt] + image_parts,                 │  │ │
│    │   │   │     response_mime_type="application/json"   │  │ │
│    │   │   │   )                                         │  │ │
│    │   │   ├─ Parse JSON response                        │  │ │
│    │   │   ├─ Extract questions:                         │  │ │
│    │   │   │   • question_number, content, subparts     │  │ │
│    │   │   │   • response_type, marks                   │  │ │
│    │   │   │   • diagram_description (in question_text)  │  │ │
│    │   │   ├─ Extract diagram info:                      │  │ │
│    │   │   │   • diagram_description                    │  │ │
│    │   │   │   • diagram_type                           │  │ │
│    │   │   │   • bounding_box (0-1000 scale)           │  │ │
│    │   │   │   • associated_question                   │  │ │
│    │   │   ├─ Track token usage & cost                   │  │ │
│    │   │   └─ Return (List[Question], List[diagram_info])│  │ │
│    │   └──────────────────────────────────────────────────┘  │ │
│    │                                                          │ │
│    │   ┌──────────────────────────────────────────────────┐  │ │
│    │   │ 3b. DiagramExtractorAgent.extract_diagrams_from_ │  │ │
│    │   │     info() ⚡ NO LLM CALL - Fast image cropping  │  │ │
│    │   │ ──────────────────────────────────────────────── │  │ │
│    │   │   ├─ For each diagram_info:                      │  │ │
│    │   │   │   ├─ Get bounding_box (0-1000 scale)       │  │ │
│    │   │   │   ├─ Convert to pixel coordinates          │  │ │
│    │   │   │   │   x = bbox.x_min / 1000 * img_width    │  │ │
│    │   │   │   │   y = bbox.y_min / 1000 * img_height   │  │ │
│    │   │   │   ├─ Crop diagram from page image          │  │ │
│    │   │   │   ├─ Save to output/diagrams/              │  │ │
│    │   │   │   ├─ Convert to base64                     │  │ │
│    │   │   │   └─ Create Diagram object                 │  │ │
│    │   │   └─ Return List[Diagram]                      │  │ │
│    │   └──────────────────────────────────────────────────┘  │ │
│    │                                                          │ │
│    │   ┌──────────────────────────────────────────────────┐  │ │
│    │   │ 3c. Link Diagrams to Questions                    │  │ │
│    │   │ ──────────────────────────────────────────────── │  │ │
│    │   │   diagram_extractor.link_diagrams_to_questions()│  │ │
│    │   │   ├─ Match by question_number                   │  │ │
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
│    │   └─ Return List[int] (page numbers)                   │ │
│    │                                                          │ │
│    │ For each answer page:                                   │ │
│    │   AnswerKeyAgent.extract_answers(page)                  │ │
│    │     ├─ Call Gemini API to extract answers              │ │
│    │     └─ Return Dict[str, AnswerKey]                     │ │
│    │                                                          │ │
│    │ AnswerKeyAgent.link_answers_to_questions()              │ │
│    │   └─ Update Question.answer_key                         │ │
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

## ⚡ Optimization Benefits

### Before Optimization:
- **Phase 3**: 2 LLM calls per page
  1. QuestionExtractor: Extract questions
  2. DiagramExtractor: Detect diagrams
- **Total**: ~2x API calls, ~2x tokens, ~2x cost

### After Optimization:
- **Phase 3**: 1 LLM call per page
  1. QuestionExtractor: Extract questions + detect diagrams (combined)
  2. DiagramExtractor: Extract images from bounding boxes (no LLM)
- **Total**: ~50% faster, ~50% cheaper, same quality

## 🔄 Detailed Agent Flows

### PDFParserAgent Flow
```python
parse(pdf_path) 
  → Open PDF with PyMuPDF
  → For each page:
      → Extract text: page.get_text("text")
      → Render image: page.get_pixmap(matrix) → PIL Image (150 DPI)
      → Extract embedded images: page.get_images()
      → Save page image to disk: output/pages/{pdf_name}_page_{num}.png
      → Create PageContent object
  → Return List[PageContent]
```

### QuestionExtractorAgent Flow (Optimized)
```python
extract_questions(page_content)
  → Build prompt (includes diagram detection requirement)
  → Convert page image to Gemini format
  → Call Gemini API ONCE (async):
      → Input: prompt + image
      → Config: temperature=0.1, JSON response
  → Parse JSON response:
      → Extract questions array
      → Extract diagrams array (from each question)
  → Convert to Question objects:
      → question_number, content (with diagram description)
      → response_type, marks, subparts
  → Extract diagram_info_list:
      → description, type, bounding_box, associated_question
  → Track costs
  → Return (List[Question], List[diagram_info])
```

### DiagramExtractorAgent Flow (Optimized)
```python
extract_diagrams_from_info(diagram_info_list, page_content)
  → For each diagram_info:
      → Get bounding_box (0-1000 scale)
      → Convert to pixels:
          x_min = bbox.x_min / 1000 * img_width
          y_min = bbox.y_min / 1000 * img_height
          x_max = bbox.x_max / 1000 * img_width
          y_max = bbox.y_max / 1000 * img_height
      → Add padding (5px)
      → Crop diagram: page_image.crop((x_min, y_min, x_max, y_max))
      → Save to: output/diagrams/page{num}_diag_{id}.png
      → Convert to base64
      → Create Diagram object
  → Return List[Diagram]

link_diagrams_to_questions(diagrams, questions, page_num)
  → For each diagram:
      → Match by associated_question number
      → Assign to Question.diagrams
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
```

## 📊 Data Structures

### PageContent
```python
@dataclass
class PageContent:
    page_number: int
    text: str
    image: Optional[Image.Image]  # PIL Image
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
    content: QuestionContent  # text, text_latex, text_html
    response_type: ResponseType
    marks: Optional[int]
    subparts: List[Question]  # Recursive
    diagrams: List[Diagram]  # Linked diagrams
    answer_key: Optional[AnswerKey]
    hierarchy_level: int = 0
```

### Diagram
```python
@dataclass
class Diagram:
    id: str
    type: DiagramType  # GRAPH, TABLE, FIGURE, etc.
    image_path: str
    image_base64: str
    alt_text: str
    description: str
    bounding_box: BoundingBox  # 0-100 percentage
    source_page: int
    is_shared: bool
    shared_with_questions: List[str]
    extraction_confidence: float
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
5. **Bounding Box Scale**: `0-1000` (from LLM) → `0-100%` (stored)
6. **Output Directories**:
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

