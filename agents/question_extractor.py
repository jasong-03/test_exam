"""Question Extractor Agent - Extracts structured questions from exam pages."""

import google.generativeai as genai
from typing import List, Optional, Dict, Any
import json
import logging
import re
from PIL import Image
import base64
import io

from ..models import (
    Question, QuestionContent, QuestionSource, ResponseType,
    MCQOption, ResponseConfig, BoundingBox
)
from ..tracking import CostTracker, PipelineLogger
from .prompts import QUESTION_EXTRACTION_PROMPT, MCQ_EXTRACTION_PROMPT
from .pdf_parser import PageContent


class QuestionExtractorAgent:
    """
    Extracts individual questions from exam pages using Gemini Vision.
    Handles question text, subparts, response types, and marks.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        cost_tracker: Optional[CostTracker] = None,
        pipeline_logger: Optional[PipelineLogger] = None,
        api_key: Optional[str] = None
    ):
        self.model_name = model_name
        self.cost_tracker = cost_tracker
        self.pipeline_logger = pipeline_logger
        self._logger = logging.getLogger("QuestionExtractor")

        if api_key:
            genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(model_name)

    async def extract_questions(
        self,
        page_content: PageContent,
        context: Optional[str] = None
    ) -> tuple[List[Question], List[dict]]:
        """
        Extract all questions from a page and detect diagrams.

        Args:
            page_content: PageContent object with text and image
            context: Optional context from previous pages

        Returns:
            Tuple of (List of Question objects, List of diagram info dicts)
        """
        self._logger.info(f"Extracting questions from page {page_content.page_number}")

        if self.pipeline_logger:
            self.pipeline_logger.log_agent_input("QuestionExtractor", "extract", {
                "page_number": page_content.page_number,
                "text_length": len(page_content.text),
                "has_image": page_content.image is not None
            })

        # Build the prompt
        prompt = self._build_extraction_prompt(page_content.text, context)

        # Prepare image for Gemini
        image_parts = []
        if page_content.image:
            image_parts = [self._image_to_part(page_content.image)]

        # Call Gemini
        try:
            if image_parts:
                response = await self.model.generate_content_async(
                    [prompt] + image_parts,
                    generation_config=genai.GenerationConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )
            else:
                response = await self.model.generate_content_async(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )

            # Track token usage
            if self.cost_tracker and hasattr(response, 'usage_metadata'):
                self.cost_tracker.log_usage(
                    agent="QuestionExtractor",
                    operation="extract_questions",
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.candidates_token_count,
                    model=self.model_name
                )

            # Parse response
            result = self._parse_response(response.text)
            questions = self._convert_to_questions(result, page_content.page_number)
            
            # Extract diagram info from LLM response
            diagram_info_list = self._extract_diagram_info(result, page_content.page_number)

            if self.pipeline_logger:
                self.pipeline_logger.log_agent_output("QuestionExtractor", "extract", {
                    "questions_found": len(questions),
                    "question_numbers": [q.question_number for q in questions],
                    "diagrams_detected": len(diagram_info_list)
                })

            if self.cost_tracker:
                self.cost_tracker.update_counts(questions=len(questions))

            self._logger.info(f"Extracted {len(questions)} questions and {len(diagram_info_list)} diagrams from page {page_content.page_number}")
            return questions, diagram_info_list

        except Exception as e:
            self._logger.error(f"Failed to extract questions: {e}")
            if self.pipeline_logger:
                self.pipeline_logger.log_error("QuestionExtractor", "extract", e, {
                    "page_number": page_content.page_number
                })
            return [], []  # Return empty lists for questions and diagram_info

    def extract_questions_sync(
        self,
        page_content: PageContent,
        context: Optional[str] = None
    ) -> List[Question]:
        """Synchronous version of extract_questions."""
        import asyncio
        return asyncio.run(self.extract_questions(page_content, context))

    def _build_extraction_prompt(self, page_text: str, context: Optional[str]) -> str:
        """Build the extraction prompt with page text and context."""
        prompt = QUESTION_EXTRACTION_PROMPT

        if context:
            prompt += f"\n\nContext from previous pages:\n{context}\n"

        prompt += f"\n\nPage text content:\n{page_text}\n"
        prompt += "\n\nAnalyze the image of this exam page and extract all questions. Return JSON."

        return prompt

    def _image_to_part(self, image: Image.Image) -> dict:
        """Convert PIL Image to Gemini part format."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        return {
            "mime_type": "image/png",
            "data": base64.b64encode(image_bytes).decode()
        }

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the JSON response from Gemini with robust error handling."""
        import re
        
        def fix_json_escapes(text: str) -> str:
            """
            Fix invalid escape sequences in JSON strings.
            Escapes backslashes that aren't part of valid escape sequences.
            """
            result = []
            i = 0
            in_string = False
            escape_next = False
            valid_escapes = {'n', 't', 'r', 'b', 'f', '"', "'", '\\', '/', 'u'}
            
            while i < len(text):
                char = text[i]
                
                if escape_next:
                    # We're processing the character after a backslash
                    if char in valid_escapes:
                        # Valid escape sequence - keep as is
                        result.append('\\' + char)
                        escape_next = False
                    elif char == 'u' and i + 4 < len(text):
                        # Unicode escape \uXXXX - keep as is
                        result.append('\\' + text[i:i+5])
                        i += 4  # Skip the 4 hex digits
                        escape_next = False
                    else:
                        # Invalid escape - escape the backslash itself
                        result.append('\\\\' + char)
                        escape_next = False
                elif char == '\\':
                    # Check if we're in a string
                    if in_string:
                        escape_next = True
                    else:
                        result.append(char)
                elif char == '"':
                    # Toggle string state (but check if it's escaped)
                    if i > 0 and text[i-1] == '\\' and (i < 2 or text[i-2] != '\\'):
                        # Escaped quote - still in string
                        result.append(char)
                    else:
                        # Quote that starts/ends a string
                        in_string = not in_string
                        result.append(char)
                else:
                    result.append(char)
                
                i += 1
            
            # Handle trailing backslash
            if escape_next:
                result.append('\\\\')
            
            return ''.join(result)
        
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()

            # Handle markdown code blocks
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.startswith("```json"):
                        in_json = True
                        continue
                    elif line.startswith("```"):
                        in_json = False
                        continue
                    if in_json:
                        json_lines.append(line)
                response_text = "\n".join(json_lines)

            # First attempt: direct parse
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                # Try to fix escape sequence issues
                self._logger.debug(f"Initial JSON parse failed: {e}, attempting fixes...")
                
                if "Invalid \\escape" in str(e) or "Invalid escape" in str(e):
                    # Fix all escape sequences in the entire JSON
                    fixed_text = fix_json_escapes(response_text)
                    
                    try:
                        return json.loads(fixed_text)
                    except json.JSONDecodeError as e2:
                        self._logger.debug(f"Escape fix attempt failed: {e2}")
                        
                        # Try fixing just the problematic area
                        error_str = str(e)
                        line_match = re.search(r'line (\d+)', error_str)
                        col_match = re.search(r'column (\d+)', error_str)
                        
                        if line_match and col_match:
                            error_line = int(line_match.group(1)) - 1
                            error_col = int(col_match.group(1)) - 1
                            
                            lines = response_text.split('\n')
                            if 0 <= error_line < len(lines):
                                # Fix the specific problematic line
                                problem_line = lines[error_line]
                                fixed_line = fix_json_escapes(problem_line)
                                lines[error_line] = fixed_line
                                fixed_text = '\n'.join(lines)
                                
                                try:
                                    return json.loads(fixed_text)
                                except json.JSONDecodeError:
                                    pass
                
                # Try to extract JSON object using balanced braces
                # Find the first { and match it with the last }
                brace_count = 0
                start_idx = response_text.find('{')
                if start_idx >= 0:
                    for i in range(start_idx, len(response_text)):
                        if response_text[i] == '{':
                            brace_count += 1
                        elif response_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                # Found matching brace
                                extracted = response_text[start_idx:i+1]
                                try:
                                    fixed_extracted = fix_json_escapes(extracted)
                                    return json.loads(fixed_extracted)
                                except json.JSONDecodeError:
                                    pass
                                break
                
                # Last resort: try regex extraction
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    try:
                        extracted = json_match.group(0)
                        fixed_extracted = fix_json_escapes(extracted)
                        return json.loads(fixed_extracted)
                    except json.JSONDecodeError:
                        pass
                
                # If all else fails, log detailed error
                self._logger.error(f"Failed to parse JSON after all fixes: {e}")
                # Log the problematic area
                error_str = str(e)
                line_match = re.search(r'line (\d+)', error_str)
                if line_match:
                    error_line = int(line_match.group(1)) - 1
                    lines = response_text.split('\n')
                    if 0 <= error_line < len(lines):
                        self._logger.debug(f"Problematic line {error_line + 1}: {lines[error_line][:200]}")
                
                self._logger.debug(f"Response text (first 1000 chars): {response_text[:1000]}")
                if len(response_text) > 1000:
                    self._logger.debug(f"Response text (last 500 chars): {response_text[-500:]}")
                
                return {"questions": [], "error": str(e), "raw_response_preview": response_text[:200]}
                    
        except Exception as e:
            self._logger.error(f"Unexpected error parsing JSON: {e}")
            import traceback
            self._logger.debug(traceback.format_exc())
            return {"questions": [], "error": str(e)}

    def _convert_to_questions(
        self,
        result: Dict[str, Any],
        page_number: int
    ) -> List[Question]:
        """Convert parsed JSON to Question objects."""
        questions = []

        for q_data in result.get("questions", []):
            try:
                question = self._create_question(q_data, page_number)
                questions.append(question)

                # Process subparts
                for subpart_data in q_data.get("subparts", []):
                    subpart = self._create_question(
                        subpart_data,
                        page_number,
                        parent_id=question.id,
                        parent_number=question.question_number,
                        hierarchy_level=1
                    )
                    question.subparts.append(subpart)

            except Exception as e:
                self._logger.warning(f"Failed to create question: {e}")
                continue

        return questions

    def _extract_diagram_info(
        self,
        result: Dict[str, Any],
        page_number: int
    ) -> List[dict]:
        """Extract diagram information from LLM response."""
        diagram_info_list = []
        
        for q_data in result.get("questions", []):
            diagrams = q_data.get("diagrams", [])
            for diag_data in diagrams:
                diagram_info = {
                    "question_number": q_data.get("question_number"),
                    "description": diag_data.get("diagram_description", ""),
                    "diagram_type": diag_data.get("diagram_type", "figure"),
                    "bounding_box": diag_data.get("bounding_box", {}),
                    "page_number": page_number,
                    "associated_question": diag_data.get("associated_question", q_data.get("question_number"))
                }
                diagram_info_list.append(diagram_info)
        
        return diagram_info_list

    def _create_question(
        self,
        q_data: Dict[str, Any],
        page_number: int,
        parent_id: Optional[str] = None,
        parent_number: Optional[str] = None,
        hierarchy_level: int = 0
    ) -> Question:
        """Create a Question object from parsed data."""
        # Determine question number
        q_num = q_data.get("question_number", "")
        if not q_num and q_data.get("part_label"):
            q_num = f"{parent_number}{q_data['part_label']}" if parent_number else q_data['part_label']

        # Create content
        content = QuestionContent(
            text=q_data.get("question_text", ""),
            text_latex=q_data.get("question_text_latex"),
            text_html=q_data.get("question_text_html")
        )

        # Determine response type
        response_type = self._map_response_type(q_data.get("response_type", "SHORT_ANSWER"))

        # Create response config for MCQ
        response_config = None
        if response_type == ResponseType.MULTIPLE_CHOICE:
            if "options" in q_data and q_data.get("options"):
                options = [
                    MCQOption(
                        label=opt.get("label", ""),
                        text=opt.get("text", ""),
                        is_correct=opt.get("is_correct", False)
                    )
                    for opt in q_data.get("options", [])
                ]
                response_config = ResponseConfig(options=options)
            else:
                # CRITICAL: MULTIPLE_CHOICE without options is invalid
                self._logger.warning(
                    f"MULTIPLE_CHOICE question {q_data.get('question_number', 'unknown')} "
                    f"on page {page_number} is missing options! This violates extraction rules."
                )

        # Create source reference
        source = QuestionSource(page_number=page_number)

        # Parse marks
        marks = q_data.get("marks")
        if isinstance(marks, str):
            try:
                marks = float(re.search(r'[\d.]+', marks).group())
            except:
                marks = None

        return Question(
            question_number=q_num,
            parent_question_id=parent_id,
            hierarchy_level=hierarchy_level,
            content=content,
            response_type=response_type,
            response_config=response_config,
            marks=marks,
            source=source,
            extraction_confidence=q_data.get("confidence", 0.8),
            raw_text=q_data.get("question_text", "")
        )

    def _map_response_type(self, type_str: str) -> ResponseType:
        """Map string response type to enum."""
        if not type_str:
            return ResponseType.SHORT_ANSWER
        type_map = {
            "MULTIPLE_CHOICE": ResponseType.MULTIPLE_CHOICE,
            "MCQ": ResponseType.MULTIPLE_CHOICE,
            "SHORT_ANSWER": ResponseType.SHORT_ANSWER,
            "LONG_ANSWER": ResponseType.LONG_ANSWER,
            "WORKING_AREA": ResponseType.WORKING_AREA,
            "FILL_IN_BLANK": ResponseType.FILL_IN_BLANK,
            "TRUE_FALSE": ResponseType.TRUE_FALSE,
            "MATCHING": ResponseType.MATCHING,
            "DIAGRAM_LABEL": ResponseType.DIAGRAM_LABEL
        }
        return type_map.get(type_str.upper(), ResponseType.SHORT_ANSWER)

    async def extract_mcq_batch(
        self,
        page_contents: List[PageContent]
    ) -> List[Question]:
        """Extract MCQ questions from multiple pages optimized for MCQ format."""
        all_questions = []

        for page in page_contents:
            prompt = MCQ_EXTRACTION_PROMPT + f"\n\nPage text:\n{page.text}"

            image_parts = []
            if page.image:
                image_parts = [self._image_to_part(page.image)]

            try:
                if image_parts:
                    response = await self.model.generate_content_async(
                        [prompt] + image_parts,
                        generation_config=genai.GenerationConfig(
                            temperature=0.1,
                            response_mime_type="application/json"
                        )
                    )
                else:
                    response = await self.model.generate_content_async(
                        prompt,
                        generation_config=genai.GenerationConfig(
                            temperature=0.1,
                            response_mime_type="application/json"
                        )
                    )

                if self.cost_tracker and hasattr(response, 'usage_metadata'):
                    self.cost_tracker.log_usage(
                        agent="QuestionExtractor",
                        operation="extract_mcq",
                        input_tokens=response.usage_metadata.prompt_token_count,
                        output_tokens=response.usage_metadata.candidates_token_count,
                        model=self.model_name
                    )

                result = self._parse_response(response.text)
                questions = self._convert_to_questions(result, page.page_number)
                all_questions.extend(questions)

            except Exception as e:
                self._logger.error(f"Failed to extract MCQ from page {page.page_number}: {e}")

        return all_questions
