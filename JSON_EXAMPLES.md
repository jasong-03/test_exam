# Exam Extractor - JSON Structure Examples

## 📋 Overview

This document shows example JSON structures for all data models used in the exam extractor.

---

## 1. LLM Response Format (Question Extraction)

### Input to LLM:
- Page image (PNG, base64 encoded)
- Prompt: `QUESTION_EXTRACTION_PROMPT`

### Output from LLM:
```json
{
  "questions": [
    {
      "question_number": "7",
      "question_text": "A rectangle has length (2x + 3) cm and width (x - 1) cm. [Diagram: A rectangle is shown with labeled sides - length (2x + 3) cm and width (x - 1) cm]",
      "question_text_latex": "A rectangle has length $(2x + 3)$ cm and width $(x - 1)$ cm.",
      "response_type": "WORKING_AREA",
      "marks": 8,
      "has_subparts": true,
      "subparts": [
        {
          "part_label": "a",
          "question_text": "Write an expression for the perimeter of the rectangle.",
          "question_text_latex": "Write an expression for the perimeter of the rectangle.",
          "response_type": "WORKING_AREA",
          "marks": 2
        },
        {
          "part_label": "b",
          "question_text": "If the perimeter is 34 cm, find the value of x.",
          "question_text_latex": "If the perimeter is 34 cm, find the value of $x$.",
          "response_type": "WORKING_AREA",
          "marks": 3
        }
      ],
      "diagrams": [
        {
          "diagram_description": "A rectangle diagram showing length (2x + 3) cm on the longer side and width (x - 1) cm on the shorter side. The sides are clearly labeled with the algebraic expressions.",
          "diagram_type": "figure",
          "bounding_box": {
            "x_min": 50,
            "y_min": 200,
            "x_max": 300,
            "y_max": 400
          },
          "associated_question": "7"
        }
      ],
      "confidence": 0.95
    },
    {
      "question_number": "8",
      "question_text": "The graph shows the relationship between temperature and time. [Diagram: A line graph with temperature on y-axis (0-100°C) and time on x-axis (0-60 minutes). The line starts at 20°C and increases steadily to 80°C]",
      "question_text_latex": "The graph shows the relationship between temperature and time.",
      "response_type": "SHORT_ANSWER",
      "marks": 2,
      "has_subparts": false,
      "diagrams": [
        {
          "diagram_description": "A line graph plotting temperature against time. Y-axis: temperature (0-100°C), X-axis: time (0-60 minutes). The line starts at (0, 20) and increases linearly to (60, 80).",
          "diagram_type": "graph",
          "bounding_box": {
            "x_min": 350,
            "y_min": 150,
            "x_max": 550,
            "y_max": 450
          },
          "associated_question": "8"
        }
      ],
      "confidence": 0.92
    }
  ],
  "page_number": 1,
  "extraction_notes": "All questions extracted successfully. Diagrams detected and described."
}
```

### Key Points:
- **bounding_box**: Uses 0-1000 scale (0 = left/top, 1000 = right/bottom)
- **diagram_description**: Detailed text description included in question_text
- **diagrams array**: Contains diagram info for each question that has one

---

## 2. Question Object (Python → JSON)

```json
{
  "id": "q_7_abc123",
  "question_number": "7",
  "parent_question_id": null,
  "hierarchy_level": 0,
  "content": {
    "text": "A rectangle has length (2x + 3) cm and width (x - 1) cm. [Diagram: A rectangle is shown with labeled sides]",
    "text_latex": "A rectangle has length $(2x + 3)$ cm and width $(x - 1)$ cm.",
    "text_html": null,
    "segments": []
  },
  "response_type": "WORKING_AREA",
  "response_config": null,
  "marks": 8,
  "source": {
    "page_number": 1,
    "position_on_page": "top",
    "extraction_method": "llm_vision"
  },
  "subparts": [
    {
      "id": "q_7a_def456",
      "question_number": "7a",
      "parent_question_id": "q_7_abc123",
      "hierarchy_level": 1,
      "content": {
        "text": "Write an expression for the perimeter of the rectangle.",
        "text_latex": "Write an expression for the perimeter of the rectangle.",
        "text_html": null,
        "segments": []
      },
      "response_type": "WORKING_AREA",
      "response_config": null,
      "marks": 2,
      "source": {
        "page_number": 1,
        "position_on_page": "middle",
        "extraction_method": "llm_vision"
      },
      "subparts": [],
      "diagrams": [],
      "answer_key": null,
      "extraction_confidence": 0.95,
      "raw_text": "Write an expression for the perimeter of the rectangle."
    }
  ],
  "diagrams": [
    {
      "id": "diag_789xyz",
      "type": "GEOMETRIC_FIGURE",
      "image_path": "output/diagrams/page1_diag_789xyz.png",
      "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
      "alt_text": "A rectangle diagram showing length (2x + 3) cm on the longer side and width (x - 1) cm on the shorter side.",
      "description": "A rectangle diagram showing length (2x + 3) cm on the longer side and width (x - 1) cm on the shorter side. The sides are clearly labeled with the algebraic expressions.",
      "bounding_box": {
        "x1": 5.0,
        "y1": 20.0,
        "x2": 30.0,
        "y2": 40.0
      },
      "source_page": 1,
      "is_shared": false,
      "shared_with_questions": [],
      "extraction_confidence": 0.9
    }
  ],
  "answer_key": {
    "question_number": "7",
    "answer": "x = 3",
    "answer_type": "WORKING_AREA",
    "working_steps": [
      "Perimeter = 2(2x + 3) + 2(x - 1)",
      "Perimeter = 4x + 6 + 2x - 2",
      "Perimeter = 6x + 4",
      "34 = 6x + 4",
      "30 = 6x",
      "x = 5"
    ],
    "marks_awarded": 8,
    "confidence": 0.85
  },
  "extraction_confidence": 0.95,
  "raw_text": "A rectangle has length (2x + 3) cm and width (x - 1) cm."
}
```

---

## 3. Diagram Object

```json
{
  "id": "diag_789xyz",
  "type": "GEOMETRIC_FIGURE",
  "image_path": "output/diagrams/page1_diag_789xyz.png",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "alt_text": "A rectangle diagram showing length (2x + 3) cm on the longer side and width (x - 1) cm on the shorter side.",
  "description": "A rectangle diagram showing length (2x + 3) cm on the longer side and width (x - 1) cm on the shorter side. The sides are clearly labeled with the algebraic expressions.",
  "bounding_box": {
    "x1": 5.0,
    "y1": 20.0,
    "x2": 30.0,
    "y2": 40.0
  },
  "source_page": 1,
  "is_shared": false,
  "shared_with_questions": [],
  "extraction_confidence": 0.9
}
```

### Diagram Types:
- `GRAPH`
- `GEOMETRIC_FIGURE`
- `CHART`
- `ILLUSTRATION`
- `TABLE`
- `CIRCUIT`
- `MAP`
- `SCIENTIFIC`
- `DIAGRAM`

### Bounding Box:
- **Format**: Percentage (0-100)
- **x1, y1**: Top-left corner
- **x2, y2**: Bottom-right corner

---

## 4. Answer Key Object

```json
{
  "question_number": "7",
  "answer": "x = 5",
  "answer_type": "WORKING_AREA",
  "working_steps": [
    "Perimeter = 2(2x + 3) + 2(x - 1)",
    "Perimeter = 4x + 6 + 2x - 2",
    "Perimeter = 6x + 4",
    "34 = 6x + 4",
    "30 = 6x",
    "x = 5"
  ],
  "marks_awarded": 8,
  "confidence": 0.85
}
```

### MCQ Answer Example:
```json
{
  "question_number": "1",
  "answer": "B",
  "answer_type": "MULTIPLE_CHOICE",
  "working_steps": [],
  "marks_awarded": 1,
  "confidence": 0.95
}
```

---

## 5. ExamMetadata Object

```json
{
  "source_file": "P5_Maths_2023_SA2_acsprimary.pdf",
  "subject": "MATHEMATICS",
  "grade_level": "P5",
  "year": 2023,
  "exam_type": "SA2",
  "school": "acsprimary",
  "total_pages": 36,
  "extraction_date": "2025-01-13T17:30:00Z"
}
```

### Subject Types:
- `MATHEMATICS`
- `SCIENCE`
- `PHYSICS`
- `CHEMISTRY`
- `BIOLOGY`
- `OTHER`

---

## 6. ExtractionMetrics Object

```json
{
  "total_tokens_used": 83386,
  "total_cost_usd": 0.0114,
  "processing_time_seconds": 45.3,
  "pages_processed": 36,
  "questions_extracted": 50,
  "diagrams_extracted": 33,
  "agents_used": [
    "PDFParser",
    "QuestionExtractor",
    "DiagramExtractor",
    "AnswerKeyAgent"
  ],
  "errors": []
}
```

---

## 7. Complete ExamPaper Object

```json
{
  "metadata": {
    "source_file": "P5_Maths_2023_SA2_acsprimary.pdf",
    "subject": "MATHEMATICS",
    "grade_level": "P5",
    "year": 2023,
    "exam_type": "SA2",
    "school": "acsprimary",
    "total_pages": 36,
    "extraction_date": "2025-01-13T17:30:00Z"
  },
  "questions": [
    {
      "id": "q_7_abc123",
      "question_number": "7",
      "content": {
        "text": "A rectangle has length (2x + 3) cm and width (x - 1) cm. [Diagram: A rectangle is shown with labeled sides]",
        "text_latex": "A rectangle has length $(2x + 3)$ cm and width $(x - 1)$ cm.",
        "text_html": null,
        "segments": []
      },
      "response_type": "WORKING_AREA",
      "marks": 8,
      "subparts": [
        {
          "id": "q_7a_def456",
          "question_number": "7a",
          "content": {
            "text": "Write an expression for the perimeter of the rectangle.",
            "text_latex": "Write an expression for the perimeter of the rectangle.",
            "text_html": null,
            "segments": []
          },
          "response_type": "WORKING_AREA",
          "marks": 2,
          "subparts": [],
          "diagrams": [],
          "answer_key": null,
          "extraction_confidence": 0.95
        }
      ],
      "diagrams": [
        {
          "id": "diag_789xyz",
          "type": "GEOMETRIC_FIGURE",
          "image_path": "output/diagrams/page1_diag_789xyz.png",
          "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
          "alt_text": "A rectangle diagram",
          "description": "A rectangle diagram showing length (2x + 3) cm and width (x - 1) cm.",
          "bounding_box": {
            "x1": 5.0,
            "y1": 20.0,
            "x2": 30.0,
            "y2": 40.0
          },
          "source_page": 1,
          "is_shared": false,
          "shared_with_questions": [],
          "extraction_confidence": 0.9
        }
      ],
      "answer_key": {
        "question_number": "7",
        "answer": "x = 5",
        "answer_type": "WORKING_AREA",
        "working_steps": [
          "Perimeter = 2(2x + 3) + 2(x - 1)",
          "Perimeter = 4x + 6 + 2x - 2",
          "Perimeter = 6x + 4",
          "34 = 6x + 4",
          "30 = 6x",
          "x = 5"
        ],
        "marks_awarded": 8,
        "confidence": 0.85
      },
      "extraction_confidence": 0.95
    }
  ],
  "extraction_metrics": {
    "total_tokens_used": 83386,
    "total_cost_usd": 0.0114,
    "processing_time_seconds": 45.3,
    "pages_processed": 36,
    "questions_extracted": 50,
    "diagrams_extracted": 33,
    "agents_used": [
      "PDFParser",
      "QuestionExtractor",
      "DiagramExtractor",
      "AnswerKeyAgent"
    ],
    "errors": []
  }
}
```

---

## 8. MCQ Question Example

```json
{
  "id": "q_1_xyz789",
  "question_number": "1",
  "content": {
    "text": "What is 2 + 2?",
    "text_latex": "What is $2 + 2$?",
    "text_html": null,
    "segments": []
  },
  "response_type": "MULTIPLE_CHOICE",
  "response_config": {
    "options": [
      {
        "label": "A",
        "text": "3",
        "is_correct": false
      },
      {
        "label": "B",
        "text": "4",
        "is_correct": true
      },
      {
        "label": "C",
        "text": "5",
        "is_correct": false
      },
      {
        "label": "D",
        "text": "6",
        "is_correct": false
      }
    ],
    "blanks": [],
    "word_limit": null,
    "show_working": false,
    "matching_pairs": []
  },
  "marks": 1,
  "subparts": [],
  "diagrams": [],
  "answer_key": {
    "question_number": "1",
    "answer": "B",
    "answer_type": "MULTIPLE_CHOICE",
    "working_steps": [],
    "marks_awarded": 1,
    "confidence": 0.95
  },
  "extraction_confidence": 0.98
}
```

---

## 9. Diagram Info (Internal Structure)

This is the structure returned from `QuestionExtractor._extract_diagram_info()`:

```json
[
  {
    "question_number": "7",
    "description": "A rectangle diagram showing length (2x + 3) cm on the longer side and width (x - 1) cm on the shorter side. The sides are clearly labeled with the algebraic expressions.",
    "diagram_type": "figure",
    "bounding_box": {
      "x_min": 50,
      "y_min": 200,
      "x_max": 300,
      "y_max": 400
    },
    "page_number": 1,
    "associated_question": "7"
  }
]
```

### Key Points:
- **bounding_box**: Uses 0-1000 scale (from LLM)
- **diagram_type**: String (will be mapped to DiagramType enum)
- **description**: Full text description from LLM

---

## 10. Response Types

```json
{
  "MULTIPLE_CHOICE": "Has options A, B, C, D",
  "SHORT_ANSWER": "Single word, number, or phrase",
  "LONG_ANSWER": "Paragraph or essay response",
  "WORKING_AREA": "Mathematical working required (show steps)",
  "FILL_IN_BLANK": "Blanks to fill in",
  "TRUE_FALSE": "True or false question",
  "MATCHING": "Matching pairs",
  "DIAGRAM_LABEL": "Label parts of a diagram"
}
```

---

## 📝 Notes

1. **Bounding Box Conversion**:
   - LLM returns: `0-1000` scale
   - Stored as: `0-100` percentage
   - Conversion: `stored = llm_value / 10`

2. **Image Storage**:
   - Diagrams saved as PNG files
   - Base64 encoded in JSON for portability
   - Path: `output/diagrams/page{num}_diag_{id}.png`

3. **Question Text**:
   - Includes diagram description in natural language
   - Makes content self-contained (no need to reference images)

4. **Hierarchy**:
   - Main questions: `hierarchy_level = 0`
   - Subparts: `hierarchy_level = 1, 2, ...`
   - Parent-child relationship via `parent_question_id`

5. **Confidence Scores**:
   - `0.0 - 1.0` range
   - Higher = more confident extraction
   - Used for quality filtering

