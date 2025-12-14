"""Prompt templates for all extraction agents."""

# =============================================================================
# PDF LAYOUT ANALYSIS PROMPTS
# =============================================================================

LAYOUT_ANALYSIS_PROMPT = """You are classifying exam paper pages by type. This is CRITICAL for routing pages to the correct extraction agent.

Analyze this page and determine its PRIMARY type:

**Page Types:**
- **question**: Contains exam questions (with question numbers like "1", "2", "Q1", etc.)
- **answer_key**: Contains answers/solutions (may have "Answer Key", "Answers", "Solutions" header, or answer patterns like "1. A", "1. 42")
- **instruction**: Contains exam instructions, rules, or guidelines
- **cover**: Cover page with exam title, subject, date
- **mixed**: Contains both questions and answers (rare, but possible)

**CRITICAL RULES:**
- If page has question numbers (1, 2, 3, Q1, Q2, etc.) → "question"
- If page has answer patterns (1. A, 2. B, or "Answer: 42") → "answer_key"
- If page has both → "mixed" (but prefer "answer_key" if answers are primary content)
- Be decisive - choose the PRIMARY purpose of the page

Return JSON:
{
    "page_type": "question|answer_key|instruction|cover|mixed",
    "confidence": 0.95,
    "reasoning": "Brief explanation of classification"
}

Focus ONLY on classification. Do NOT extract content."""


# =============================================================================
# QUESTION EXTRACTION PROMPTS
# =============================================================================

QUESTION_EXTRACTION_PROMPT = """You are extracting exam questions from a page. Extract ALL questions with complete structure AND detect/describe any diagrams.

For each question found, extract:

1. **Question Number**: The exact number/label (e.g., "7", "7a", "7(a)", "7.a.i")
2. **Question Text**: The complete question text
   - Preserve mathematical notation using LaTeX (e.g., $x^2 + 5x = 12$)
   - Preserve chemical formulas (e.g., H₂O, CO₂)
   - Keep any special formatting
   - **If there is a diagram associated with this question, describe it in detail within the question text**
3. **Subparts**: If the question has parts (a), (b), (c) or (i), (ii), (iii)
4. **Response Type**: What type of answer is expected?
   - MULTIPLE_CHOICE: Has options A, B, C, D or 1, 2, 3, 4
   - SHORT_ANSWER: Single word, number, or phrase
   - LONG_ANSWER: Paragraph or essay response
   - WORKING_AREA: Mathematical working required (show steps)
   - FILL_IN_BLANK: Blanks to fill in
   - TRUE_FALSE: True or false question
   - DIAGRAM_LABEL: Label parts of a diagram

**CRITICAL RULE FOR MULTIPLE-CHOICE QUESTIONS:**
- If response_type is MULTIPLE_CHOICE, you MUST extract ALL answer options.
- Options are REQUIRED and cannot be omitted.
- Options may appear:
  • immediately after the question text
  • AFTER a diagram or figure
  • separated by line breaks or spacing
  • on the same line or different lines
- Options are typically labeled (1)-(4), A-D, (A)-(D), or similar formats.
- If options are missing or unclear, still extract the best possible option list and LOWER the confidence score.
- A MULTIPLE_CHOICE question WITHOUT options is considered an INVALID extraction.

5. **MCQ Options** (REQUIRED for MULTIPLE_CHOICE): Extract ALL options with their labels
   - Format: [{"label": "A", "text": "option text"}, ...]
   - Include ALL options even if they appear after diagrams
6. **Marks/Points**: If shown (e.g., "[2 marks]", "(3)")
7. **Diagrams**: For each diagram/visual element associated with this question:
   - **diagram_description**: Detailed text description of what the diagram shows
   - **diagram_type**: Type of diagram (graph, table, figure, chart, illustration, formula, etc.)
   - **bounding_box**: Approximate position on page in 0-1000 scale: {"x_min": 0-1000, "y_min": 0-1000, "x_max": 0-1000, "y_max": 0-1000}
   - **associated_question**: Question number this diagram belongs to

Return JSON array:
{
    "questions": [
        {
            "question_number": "1",
            "question_text": "Which one of the following is sixty-three thousand and forty in numerals?",
            "question_text_latex": "Which one of the following is sixty-three thousand and forty in numerals?",
            "response_type": "MULTIPLE_CHOICE",
            "options": [
                {"label": "1", "text": "6340"},
                {"label": "2", "text": "63 040"},
                {"label": "3", "text": "63 400"},
                {"label": "4", "text": "630 040"}
            ],
            "marks": 1,
            "diagrams": [],
            "confidence": 0.95
        },
        {
            "question_number": "7",
            "question_text": "A rectangle has length (2x + 3) cm and width (x - 1) cm. [Diagram: A rectangle is shown with labeled sides]",
            "question_text_latex": "A rectangle has length $(2x + 3)$ cm and width $(x - 1)$ cm.",
            "response_type": "WORKING_AREA",
            "marks": 8,
            "has_subparts": true,
            "subparts": [
                {
                    "part_label": "a",
                    "question_text": "Write an expression for the perimeter of the rectangle.",
                    "response_type": "WORKING_AREA",
                    "marks": 2
                }
            ],
            "diagrams": [
                {
                    "diagram_description": "A rectangle diagram showing length (2x + 3) cm on the longer side and width (x - 1) cm on the shorter side. The sides are clearly labeled.",
                    "diagram_type": "figure",
                    "bounding_box": {"x_min": 50, "y_min": 200, "x_max": 300, "y_max": 400},
                    "associated_question": "7"
                }
            ],
            "confidence": 0.95
        }
    ],
    "page_number": 1,
    "extraction_notes": "Any issues or ambiguities encountered"
}

IMPORTANT:
- Extract EVERY question on the page, even partial ones
- Preserve exact wording
- Use LaTeX for all mathematical expressions
- **If a question has a diagram, include a detailed description in the question_text AND provide diagram info in the diagrams array**
- **Describe diagrams in natural language so the content is self-contained**
- **CRITICAL: MULTIPLE_CHOICE questions MUST include options array - this is REQUIRED, not optional**
- Note if a question continues from previous page or to next page"""


# =============================================================================
# MCQ EXTRACTION PROMPT
# =============================================================================

MCQ_EXTRACTION_PROMPT = """Extract multiple choice questions with all options.

For each MCQ, extract:
1. Question number
2. Question stem (the question text)
3. All options with their labels (A, B, C, D or 1, 2, 3, 4)
4. The correct answer if indicated

Return JSON:
{
    "questions": [
        {
            "question_number": "15",
            "stem": "What is the value of x in the equation 2x + 5 = 15?",
            "stem_latex": "What is the value of $x$ in the equation $2x + 5 = 15$?",
            "options": [
                {"label": "A", "text": "3"},
                {"label": "B", "text": "5"},
                {"label": "C", "text": "7"},
                {"label": "D", "text": "10"}
            ],
            "correct_answer": "B",
            "marks": 1
        }
    ]
}"""


# =============================================================================
# DIAGRAM DETECTION PROMPTS
# =============================================================================

DIAGRAM_DETECTION_PROMPT = """Identify ALL visual elements in this exam page that are diagrams, figures, graphs, charts, tables, or images.

For EACH visual element found, provide:
1. **Bounding Box**: Coordinates as percentages [x1, y1, x2, y2] where:
   - x1, y1 = top-left corner (0-1000 scale)
   - x2, y2 = bottom-right corner (0-1000 scale)
2. **Type**: GRAPH, GEOMETRIC_FIGURE, CHART, ILLUSTRATION, TABLE, CIRCUIT, MAP, SCIENTIFIC
3. **Associated Question**: Which question number this relates to (if identifiable)
4. **Description**: Brief description of what the diagram shows
5. **Is Shared**: True if used by multiple questions (e.g., "Use this diagram for questions 5-8")

Return JSON:
{
    "diagrams": [
        {
            "id": "diag_1",
            "bounding_box": {
                "x1": 100,
                "y1": 200,
                "x2": 400,
                "y2": 500
            },
            "type": "GEOMETRIC_FIGURE",
            "associated_question": "7",
            "description": "Right triangle with sides labeled a, b, c and a 90-degree angle marked",
            "is_shared": false,
            "labels_present": ["a", "b", "c", "90°"],
            "confidence": 0.92
        }
    ],
    "shared_diagram_instructions": [
        {
            "text": "Use the diagram above to answer questions 5-8",
            "diagram_id": "diag_1",
            "question_range": ["5", "6", "7", "8"]
        }
    ],
    "total_diagrams_found": 1
}

IMPORTANT:
- Be precise with bounding boxes - include a small margin around the diagram
- Identify ALL visual elements, not just obvious diagrams
- Tables with data should be identified as TABLE type
- Note any labels or text within the diagram"""


# =============================================================================
# ANSWER KEY EXTRACTION PROMPTS
# =============================================================================

ANSWER_KEY_EXTRACTION_PROMPT = """Extract answer keys from this content. This is an answer key page.

For each answer, extract:
1. **Question Reference**: The question number/identifier (e.g., "1", "7a", "Q3", "3(a)")
   - Use the EXACT format as shown in the answer key
   - This will be matched to questions later
2. **Answer Type**: MULTIPLE_CHOICE, SHORT_ANSWER, WORKING_AREA, etc.
3. **Final Answer**: The correct answer
   - For MCQ: the option label (A, B, C, D or 1, 2, 3, 4)
   - For others: the answer text
4. **Worked Solution**: Step-by-step solution if provided (especially for Math)
5. **Marking Scheme**: Any marking criteria or rubric points

Return JSON:
{
    "answers": [
        {
            "question_ref": "1",
            "answer_type": "MULTIPLE_CHOICE",
            "answer": "2",
            "final_answer": "2",
            "confidence": 0.95
        },
        {
            "question_ref": "7a",
            "answer_type": "WORKING_AREA",
            "answer": "6x + 4",
            "final_answer": "6x + 4",
            "final_answer_latex": "$6x + 4$",
            "worked_solution": [
                {
                    "step": 1,
                    "description": "Write perimeter formula",
                    "expression": "P = 2(l + w)",
                    "expression_latex": "$P = 2(l + w)$"
                },
                {
                    "step": 2,
                    "description": "Substitute values",
                    "expression": "P = 2((2x+3) + (x-1))",
                    "expression_latex": "$P = 2((2x+3) + (x-1))$"
                },
                {
                    "step": 3,
                    "description": "Simplify",
                    "expression": "P = 2(3x + 2) = 6x + 4",
                    "expression_latex": "$P = 2(3x + 2) = 6x + 4$"
                }
            ],
            "marks_breakdown": [
                {"criterion": "Correct formula", "marks": 1},
                {"criterion": "Correct simplification", "marks": 1}
            ],
            "total_marks": 2,
            "confidence": 0.92
        }
    ],
    "is_complete_answer_key": true,
    "answer_key_type": "worked_solutions|final_answers_only|marking_scheme"
}

IMPORTANT:
- Extract EVERY answer on the page
- Use question_ref (not question_number) - this is the reference used for matching
- For MCQ, extract the option label (A, B, C, D or 1, 2, 3, 4)
- Preserve exact question numbering format from the answer key"""


# =============================================================================
# METADATA EXTRACTION PROMPT
# =============================================================================

EXAM_METADATA_PROMPT = """Extract metadata from this exam paper cover page or header.

Extract:
1. **Subject**: Mathematics, Science, Physics, Chemistry, Biology, etc.
2. **Grade/Level**: P5, P6, Secondary 1, etc.
3. **Exam Type**: Prelim, SA1, SA2, Final, Mid-year, etc.
4. **School Name**: If visible
5. **Year**: Exam year
6. **Duration**: Time allowed
7. **Total Marks**: Maximum marks
8. **Instructions**: Any important instructions for students

Return JSON:
{
    "subject": "MATHEMATICS",
    "grade_level": "P5",
    "exam_type": "SA2",
    "school": "ACS Primary",
    "year": 2023,
    "duration_minutes": 90,
    "total_marks": 100,
    "instructions": [
        "Answer all questions",
        "Show all working",
        "Calculators are allowed"
    ],
    "sections": [
        {"name": "Section A", "marks": 40, "description": "Multiple Choice"},
        {"name": "Section B", "marks": 60, "description": "Structured Questions"}
    ],
    "confidence": 0.9
}"""


# =============================================================================
# SCIENCE-SPECIFIC PROMPTS
# =============================================================================

SCIENCE_QUESTION_PROMPT = """Extract science exam questions with special attention to:

1. **Scientific Diagrams**: Experiments, life cycles, food chains, etc.
2. **Data Tables**: Experimental results, observations
3. **Scientific Terms**: Proper terminology preservation
4. **Process Questions**: "Explain why...", "Describe how..."
5. **Diagram Labeling**: Questions asking to label parts

For diagrams, note:
- What the diagram shows (organism, experiment setup, etc.)
- Parts that need labeling
- Arrows or flow directions
- Scale or measurements if shown

Return same JSON structure as general questions but with additional:
{
    "scientific_context": {
        "topic": "Living Things|Forces|Matter|Energy|etc.",
        "requires_diagram_analysis": true,
        "key_concepts": ["photosynthesis", "chlorophyll", "sunlight"]
    }
}"""


# =============================================================================
# VALIDATION PROMPT
# =============================================================================

SCHEMA_VALIDATION_PROMPT = """Review and validate the extracted exam data for completeness and accuracy.

Check for:
1. **Completeness**: Are all questions extracted? Any missing parts?
2. **Consistency**: Do question numbers follow logical sequence?
3. **Accuracy**: Does the extracted text match the original?
4. **Links**: Are diagrams correctly linked to questions?
5. **Answers**: Are answer keys matched to correct questions?

Return validation report:
{
    "is_valid": true,
    "completeness_score": 0.95,
    "issues": [
        {
            "type": "missing_subpart",
            "question": "7",
            "description": "Question 7c appears to be missing"
        }
    ],
    "warnings": [
        {
            "type": "low_confidence",
            "question": "12",
            "description": "OCR confidence low for mathematical expressions"
        }
    ],
    "suggestions": [
        "Review question 7 for missing parts",
        "Verify diagram 3 is linked correctly"
    ]
}"""
