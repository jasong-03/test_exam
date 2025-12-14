"""Answer Key Agent - Extracts and links answer keys to questions."""

import google.generativeai as genai
from typing import List, Optional, Dict, Any
import json
import logging
import re
from PIL import Image
import base64
import io

from ..models import (
    Question, AnswerKey, WorkedSolutionStep, MarkingCriterion
)
from ..tracking import CostTracker, PipelineLogger
from .prompts import ANSWER_KEY_EXTRACTION_PROMPT
from .pdf_parser import PageContent


class AnswerKeyAgent:
    """
    Extracts answer keys from exam papers and links them to questions.
    Handles both simple answers and worked solutions.
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
        self._logger = logging.getLogger("AnswerKeyAgent")

        if api_key:
            genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(model_name)

    async def extract_answers(
        self,
        page_content: PageContent
    ) -> Dict[str, AnswerKey]:
        """
        Extract answer keys from a page.

        Args:
            page_content: PageContent object (could be answer key page)

        Returns:
            Dictionary mapping question numbers to AnswerKey objects
        """
        self._logger.info(f"Extracting answers from page {page_content.page_number}")

        if self.pipeline_logger:
            self.pipeline_logger.log_agent_input("AnswerKeyAgent", "extract", {
                "page_number": page_content.page_number,
                "text_length": len(page_content.text)
            })

        # Build prompt
        prompt = ANSWER_KEY_EXTRACTION_PROMPT + f"\n\nContent:\n{page_content.text}"

        # Prepare image if available
        image_parts = []
        if page_content.image:
            image_parts = [self._image_to_part(page_content.image)]

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
                    agent="AnswerKeyAgent",
                    operation="extract_answers",
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.candidates_token_count,
                    model=self.model_name
                )

            # Parse response
            result = self._parse_response(response.text)
            answer_keys = self._convert_to_answer_keys(result)

            if self.pipeline_logger:
                self.pipeline_logger.log_agent_output("AnswerKeyAgent", "extract", {
                    "answers_found": len(answer_keys),
                    "question_numbers": list(answer_keys.keys())
                })

            self._logger.info(f"Extracted {len(answer_keys)} answers from page {page_content.page_number}")
            return answer_keys

        except Exception as e:
            self._logger.error(f"Failed to extract answers: {e}")
            if self.pipeline_logger:
                self.pipeline_logger.log_error("AnswerKeyAgent", "extract", e, {
                    "page_number": page_content.page_number
                })
            return {}

    def extract_answers_sync(self, page_content: PageContent) -> Dict[str, AnswerKey]:
        """Synchronous version of extract_answers."""
        import asyncio
        return asyncio.run(self.extract_answers(page_content))

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
        """Parse the JSON response from Gemini."""
        try:
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

            return json.loads(response_text)
        except json.JSONDecodeError as e:
            self._logger.error(f"Failed to parse JSON response: {e}")
            return {"answers": []}

    def _convert_to_answer_keys(
        self,
        result: Dict[str, Any]
    ) -> Dict[str, AnswerKey]:
        """Convert parsed JSON to AnswerKey objects.
        
        Returns:
            Dictionary mapping question_ref to AnswerKey objects
        """
        answer_keys = {}

        for ans_data in result.get("answers", []):
            try:
                # Use question_ref (new format) or question_number (backward compatibility)
                q_ref = ans_data.get("question_ref") or ans_data.get("question_number", "")
                if not q_ref:
                    continue

                # Create worked solution steps
                worked_solution = []
                for step_data in ans_data.get("worked_solution", []):
                    step = WorkedSolutionStep(
                        step_number=step_data.get("step", 0),
                        description=step_data.get("description", ""),
                        expression=step_data.get("expression"),
                        expression_latex=step_data.get("expression_latex")
                    )
                    worked_solution.append(step)

                # Create marking rubric
                marking_rubric = []
                for mark_data in ans_data.get("marks_breakdown", []):
                    criterion = MarkingCriterion(
                        criterion=mark_data.get("criterion", ""),
                        marks=mark_data.get("marks", 0)
                    )
                    marking_rubric.append(criterion)

                # Get final answer (prefer "answer" field, fallback to "final_answer")
                final_answer = ans_data.get("answer") or ans_data.get("final_answer", "")

                # Create answer key
                answer_key = AnswerKey(
                    final_answer=final_answer,
                    acceptable_answers=ans_data.get("acceptable_answers", []),
                    worked_solution=worked_solution,
                    marking_rubric=marking_rubric,
                    explanation=ans_data.get("explanation")
                )

                # Use question_ref as key for matching
                answer_keys[q_ref] = answer_key

            except Exception as e:
                self._logger.warning(f"Failed to create answer key: {e}")
                continue

        return answer_keys

    def link_answers_to_questions(
        self,
        questions: List[Question],
        answer_keys: Dict[str, AnswerKey]
    ) -> int:
        """
        Link extracted answer keys to their corresponding questions.

        Args:
            questions: List of Question objects
            answer_keys: Dictionary mapping question numbers to AnswerKey

        Returns:
            Number of successful links made
        """
        links_made = 0

        for question in questions:
            # Try exact match
            if question.question_number in answer_keys:
                question.answer_key = answer_keys[question.question_number]
                links_made += 1

            # Try normalized match (e.g., "7a" vs "7(a)")
            normalized = self._normalize_question_number(question.question_number)
            for key, answer in answer_keys.items():
                if self._normalize_question_number(key) == normalized:
                    question.answer_key = answer
                    links_made += 1
                    break

            # Link to subparts
            for subpart in question.subparts:
                subpart_num = subpart.question_number
                if subpart_num in answer_keys:
                    subpart.answer_key = answer_keys[subpart_num]
                    links_made += 1

                normalized_sub = self._normalize_question_number(subpart_num)
                for key, answer in answer_keys.items():
                    if self._normalize_question_number(key) == normalized_sub:
                        subpart.answer_key = answer
                        links_made += 1
                        break

        self._logger.info(f"Linked {links_made} answers to questions")
        return links_made

    def _normalize_question_number(self, q_num: str) -> str:
        """Normalize question number for matching."""
        if not q_num:
            return ""
        # Remove parentheses, spaces, dots
        normalized = re.sub(r'[().\s]', '', q_num.lower())
        return normalized

    async def detect_answer_key_pages(
        self,
        pages: List[PageContent]
    ) -> List[int]:
        """
        Detect which pages contain answer keys.

        Args:
            pages: List of PageContent objects

        Returns:
            List of page numbers that contain answer keys
        """
        answer_key_pages = []

        for page in pages:
            # Quick heuristic check first
            text_lower = (page.text or "").lower()
            indicators = [
                "answer key",
                "answers",
                "marking scheme",
                "mark scheme",
                "solution",
                "worked solution",
                "suggested answers"
            ]

            if any(ind in text_lower for ind in indicators):
                answer_key_pages.append(page.page_number)
                continue

            # Check for answer patterns (e.g., "1. A", "1. 42")
            answer_pattern = r'^\s*\d+\.\s*[A-Da-d]?\s*[\d\w]'
            if re.search(answer_pattern, page.text, re.MULTILINE):
                # Likely contains answers
                answer_key_pages.append(page.page_number)

        return answer_key_pages

    async def generate_answer_from_question(
        self,
        question: Question,
        include_working: bool = True
    ) -> Optional[AnswerKey]:
        """
        Generate an answer for a question using LLM (for validation/testing).
        Note: This should only be used for testing, not production answer key extraction.
        """
        if not question.content:
            return None

        prompt = f"""Solve this exam question and provide the answer:

Question {question.question_number}:
{question.content.text}

{"Provide step-by-step working." if include_working else "Provide the final answer only."}

Return JSON with:
- final_answer: The correct answer
- worked_solution: Array of steps (if working requested)
- explanation: Brief explanation
"""

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )

            if self.cost_tracker and hasattr(response, 'usage_metadata'):
                self.cost_tracker.log_usage(
                    agent="AnswerKeyAgent",
                    operation="generate_answer",
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.candidates_token_count,
                    model=self.model_name
                )

            result = self._parse_response(response.text)

            worked_solution = []
            for step_data in result.get("worked_solution", []):
                step = WorkedSolutionStep(
                    step_number=step_data.get("step", 0),
                    description=step_data.get("description", ""),
                    expression=step_data.get("expression"),
                    expression_latex=step_data.get("expression_latex")
                )
                worked_solution.append(step)

            return AnswerKey(
                final_answer=result.get("final_answer", ""),
                worked_solution=worked_solution,
                explanation=result.get("explanation")
            )

        except Exception as e:
            self._logger.error(f"Failed to generate answer: {e}")
            return None
