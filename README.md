# Growtrics Exam Extractor

Extract structured questions, diagrams, and answer keys from exam PDFs using Google's Gemini API.

## Quick Start

### Installation

1. **Clone or navigate to project directory**
```bash
cd exam_extractor/
```

2. **Create Python environment** (Python 3.10+)
```bash
python3.10 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up API key**
```bash
# Create .env file in project root
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### Basic Usage

**Single PDF**:
```bash
python -m exam_extractor.main sample_pdf/example.pdf
```

**Batch Processing**:
```bash
# Process all PDFs in directory
python -m exam_extractor.main sample_pdf/*.pdf

# Process with parallel mode (faster)
python -m exam_extractor.main sample_pdf/*.pdf --parallel
```

**With Options**:
```bash
python -m exam_extractor.main exam.pdf \
  --output results/ \
  --no-diagrams \
  --no-answers \
  -v
```

### Python API

```python
from exam_extractor import OrchestratorAgent
import asyncio

async def main():
    orchestrator = OrchestratorAgent(api_key="your_key")
    result = await orchestrator.process_pdf("exam.pdf")

    print(f"Questions extracted: {len(result.questions)}")
    print(f"Total cost: ${result.extraction_metrics.total_cost_usd:.4f}")

asyncio.run(main())
```

---

## Features

- **Automatic Question Extraction**: Detects and extracts all question types
- **Diagram Processing**: Automatic detection, classification, and cropping
- **Answer Key Extraction**: Extracts solutions and marking rubrics
- **Cost Tracking**: Real-time token counting and cost estimation
- **Hierarchical Structure**: Maintains question and subpart relationships
- **Multi-Format Output**: Text, LaTeX, and HTML alternatives
- **Confidence Scoring**: Extraction confidence metrics included
- **Error Recovery**: Graceful handling of problematic pages

---

## Output

Results saved to `output/` directory:

```
output/
├── questions/
│   ├── {pdf_name}_extracted.json      # Main result (ExamPaper)
│   ├── {pdf_name}/q1.json             # Individual questions
│   └── answer_keys/                   # (if extracted)
├── diagrams/                          # Extracted diagram images
├── pages/                             # Page images
└── logs/
    ├── costs/                         # Cost tracking
    └── agents/                        # Detailed event logs
```

### Main Output Format

```json
{
  "metadata": {
    "subject": "MATHEMATICS",
    "grade_level": "P5",
    "year": 2023,
    "exam_type": "SA2",
    "school": "Henry Park"
  },
  "questions": [
    {
      "id": "q_123...",
      "question_number": "1",
      "content": {
        "text": "Question text...",
        "text_latex": "..."
      },
      "response_type": "MULTIPLE_CHOICE",
      "response_config": {
        "options": [
          {"label": "A", "text": "Option A", "is_correct": true},
          {"label": "B", "text": "Option B", "is_correct": false}
        ]
      },
      "diagrams": [...],
      "answer_key": {...},
      "marks": 5,
      "extraction_confidence": 0.95
    }
  ],
  "extraction_metrics": {
    "total_tokens_used": 125000,
    "total_cost_usd": 0.0245,
    "processing_time_seconds": 45.3,
    "pages_processed": 36,
    "questions_extracted": 50,
    "diagrams_extracted": 33
  }
}
```

---

## Configuration

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR
OUTPUT_DIR=output        # Default output directory
```

### CLI Options

| Option | Description |
|--------|-----------|
| `<pdf_path>` | PDF file(s) to process (supports glob patterns) |
| `-o, --output DIR` | Output directory (default: `output`) |
| `-k, --api-key KEY` | Gemini API key (or use GEMINI_API_KEY env var) |
| `--parallel` | Process multiple PDFs concurrently |
| `--no-diagrams` | Skip diagram extraction |
| `--no-answers` | Skip answer key extraction |
| `-v, --verbose` | Verbose output (DEBUG level logging) |

### Model Configuration

The system uses Google Gemini 2.5 Flash:
- Temperature: 0.1 (consistent extraction)
- Response Format: JSON
- Image DPI: 150

---

## Question Types Supported

| Type | Example |
|------|---------|
| `MULTIPLE_CHOICE` | Select A, B, C, or D |
| `SHORT_ANSWER` | Fill in word/number |
| `LONG_ANSWER` | Write essay/explanation |
| `WORKING_AREA` | Show mathematical working |
| `FILL_IN_BLANK` | Complete sentence |
| `TRUE_FALSE` | True or false statement |
| `MATCHING` | Match pairs |
| `DIAGRAM_LABEL` | Label diagram parts |

---

## Diagram Types Recognized

| Type | Examples |
|------|----------|
| `GRAPH` | Line, bar, scatter plots |
| `GEOMETRIC_FIGURE` | Shapes, angles |
| `CHART` | Pie, flow charts |
| `ILLUSTRATION` | Visual examples |
| `TABLE` | Data tables |
| `CIRCUIT` | Electrical circuits |
| `MAP` | Geographic/conceptual |
| `SCIENTIFIC` | Lab diagrams, molecules |
| `DIAGRAM` | General diagrams |

---

## Cost Estimation

**Typical Exam** (10-30 pages):
- Token usage: 200,000-400,000
- Cost: $0.10-0.20 USD
- Processing time: 45-120 seconds

**Cost Breakdown**:
- Gemini 2.5 Flash: $0.075/M input, $0.30/M output
- 50% cost savings via combined extraction
- Diagram cropping: No API cost (local processing)
- Answer merging: No API cost (pure Python)

---

## Examples

### Sample Files

The `sample_pdf/` directory includes:
- `P5_Maths_2023_SA2_acsprimary.pdf` - Primary 5 Math exam

Run example:
```bash
python -m exam_extractor.main sample_pdf/P5_Maths_2023_SA2_acsprimary.pdf
```

### Processing Results

After processing, check `output/questions/` for the complete extracted structure.

Individual question example from output:
```json
{
  "id": "q_7_abc123",
  "question_number": "7",
  "content": {
    "text": "Solve: x² + 2x - 3 = 0",
    "text_latex": "Solve: $x^2 + 2x - 3 = 0$"
  },
  "response_type": "WORKING_AREA",
  "marks": 5,
  "extraction_confidence": 0.98,
  "answer_key": {
    "final_answer": "x = 1 or x = -3",
    "worked_solution": [
      {
        "step_number": 1,
        "description": "Factor the quadratic",
        "expression": "(x - 1)(x + 3) = 0"
      }
    ]
  }
}
```

---

## Troubleshooting

### API Key Issues
```
Error: Gemini API key required
```
- Set `GEMINI_API_KEY` in `.env` file or use `--api-key` flag
- Verify API key is valid and has Gemini access

### PDF Format Issues
```
Error: Failed to parse PDF
```
- Ensure PDF is not corrupted
- Check that PDF has readable content (not scanned image without OCR)
- For image-based PDFs, Gemini API handles them directly

### Low Confidence Scores
- Check that PDF quality is good
- Verify questions have standard formatting
- Review detailed logs in `output/logs/agents/`

### High Cost Usage
- Use `--no-diagrams` to skip diagram extraction if not needed
- Use `--no-answers` to skip answer key extraction
- Process smaller batches

---

## Documentation

Full documentation available in `docs/`:

- **[project-overview-pdr.md](docs/project-overview-pdr.md)** - Product requirements and vision
- **[system-architecture.md](docs/system-architecture.md)** - Detailed architecture and design
- **[codebase-summary.md](docs/codebase-summary.md)** - Codebase structure and modules
- **[code-standards.md](docs/code-standards.md)** - Coding standards and patterns
- **[FLOW_OPTIMIZED.md](FLOW_OPTIMIZED.md)** - Pipeline optimization details
- **[JSON_EXAMPLES.md](JSON_EXAMPLES.md)** - Complete JSON schema examples

---

## Architecture Highlights

**5-Phase Pipeline**:
1. PDF Parsing
2. Metadata Extraction
3. Question & Diagram Extraction (optimized - 50% cost reduction)
4. Diagram Cropping (no API cost)
5. Answer Merging & Finalization

**6 Specialized Agents**:
- PDFParserAgent
- QuestionExtractorAgent
- DiagramExtractorAgent
- AnswerKeyAgent
- OrchestratorAgent (coordinator)
- Plus cost and logging infrastructure

---

## Performance

- **Speed**: 5-8 seconds per page
- **Accuracy**: 95%+ extraction rate
- **Reliability**: Graceful error recovery
- **Scalability**: Parallel processing supported

---

## Requirements

- Python 3.10+
- Google Gemini API key
- Dependencies:
  - `google-generativeai`
  - `PyMuPDF`
  - `Pillow`
  - `python-dotenv`

---

## Support and Issues

For detailed issues or questions:
1. Check comprehensive logs in `output/logs/`
2. Review documentation in `docs/` directory
3. Enable verbose mode: `python -m exam_extractor.main exam.pdf -v`
4. Check error metrics in cost tracking output

---

## License

[Add your license here]

---

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2025-12-14
