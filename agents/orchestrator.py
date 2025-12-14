"""Orchestrator Agent - Coordinates the entire extraction pipeline."""

import asyncio
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import logging
import json

import google.generativeai as genai

from ..models import (
    ExamPaper, ExamMetadata, ExtractionMetrics, Question, Diagram, Subject
)
from ..tracking import CostTracker, PipelineLogger, ConsoleProgressLogger
from .pdf_parser import PDFParserAgent, PageContent
from .question_extractor import QuestionExtractorAgent
from .diagram_extractor import DiagramExtractorAgent
from .answer_key_agent import AnswerKeyAgent
from .prompts import LAYOUT_ANALYSIS_PROMPT


class OrchestratorAgent:
    """
    Central coordinator for the exam extraction pipeline.
    Manages agent execution, state, and error recovery.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        output_dir: str = "output",
        api_key: Optional[str] = None,
        enable_logging: bool = True
    ):
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key
        self._logger = logging.getLogger("Orchestrator")

        # Initialize tracking
        self.cost_tracker = CostTracker(log_dir=str(self.output_dir / "logs" / "costs"))
        self.pipeline_logger = PipelineLogger(log_dir=str(self.output_dir / "logs" / "agents")) if enable_logging else None

        # Initialize agents
        self.pdf_parser = PDFParserAgent(
            cost_tracker=self.cost_tracker,
            pipeline_logger=self.pipeline_logger,
            output_dir=str(self.output_dir / "pages")
        )

        self.question_extractor = QuestionExtractorAgent(
            model_name=model_name,
            cost_tracker=self.cost_tracker,
            pipeline_logger=self.pipeline_logger,
            api_key=api_key
        )

        self.diagram_extractor = DiagramExtractorAgent(
            model_name=model_name,
            cost_tracker=self.cost_tracker,
            pipeline_logger=self.pipeline_logger,
            output_dir=str(self.output_dir / "diagrams"),
            api_key=api_key
        )

        self.answer_key_agent = AnswerKeyAgent(
            model_name=model_name,
            cost_tracker=self.cost_tracker,
            pipeline_logger=self.pipeline_logger,
            api_key=api_key
        )

        # Initialize Gemini model for page type detection
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def _detect_page_type(self, page: PageContent) -> Tuple[str, float]:
        """
        Detect page type using LLM classification.
        
        Returns:
            Tuple of (page_type, confidence)
        """
        try:
            # Prepare image
            image_parts = []
            if page.image:
                import base64
                import io
                from PIL import Image
                
                buffer = io.BytesIO()
                page.image.save(buffer, format="PNG")
                image_bytes = buffer.getvalue()
                image_parts = [{
                    "mime_type": "image/png",
                    "data": base64.b64encode(image_bytes).decode()
                }]

            # Build prompt
            prompt = LAYOUT_ANALYSIS_PROMPT + f"\n\nPage text preview:\n{page.text[:500]}"

            # Call Gemini
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
                    agent="Orchestrator",
                    operation="detect_page_type",
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.candidates_token_count,
                    model=self.model_name
                )

            # Parse response
            result = json.loads(response.text)
            page_type = result.get("page_type", "question").lower()
            confidence = result.get("confidence", 0.5)

            # Normalize page_type
            if page_type in ["answer_key", "answer", "answers", "solutions"]:
                page_type = "answer_key"
            elif page_type in ["question", "questions"]:
                page_type = "question"
            elif page_type in ["instruction", "instructions"]:
                page_type = "instruction"
            elif page_type in ["cover", "title"]:
                page_type = "cover"
            else:
                page_type = "question"  # Default

            return page_type, confidence

        except Exception as e:
            self._logger.warning(f"Failed to detect page type for page {page.page_number}: {e}")
            # Default to question if detection fails
            return "question", 0.5

    async def process_pdf(
        self,
        pdf_path: str,
        extract_diagrams: bool = True,
        extract_answers: bool = True,
        detect_metadata: bool = True
    ) -> ExamPaper:
        """
        Process a PDF file and extract all exam content.

        Args:
            pdf_path: Path to the PDF file
            extract_diagrams: Whether to extract diagrams
            extract_answers: Whether to extract answer keys
            detect_metadata: Whether to detect exam metadata

        Returns:
            ExamPaper object with all extracted content
        """
        pdf_path = Path(pdf_path)
        self._logger.info(f"Processing PDF: {pdf_path.name}")

        # Start tracking
        run_id = self.cost_tracker.start_run(str(pdf_path))
        if self.pipeline_logger:
            self.pipeline_logger.start_run(run_id)

        start_time = datetime.now()
        progress = ConsoleProgressLogger()

        try:
            # Phase 1: Parse PDF
            self._logger.info("Phase 1: Parsing PDF")
            progress.update(0, "Parsing PDF...")
            pages = self.pdf_parser.parse(str(pdf_path))
            progress.total_pages = len(pages)

            # Phase 2: Detect metadata
            pdf_name = pdf_path.name if pdf_path.name else ""
            first_page_text = pages[0].text if pages and pages[0].text else ""
            metadata = ExamMetadata(
                source_file=pdf_name,
                subject=self._detect_subject(pdf_name, first_page_text)
            )

            if detect_metadata and pages:
                metadata = await self._extract_metadata(pages[0], pdf_path.name)

            # Phase 1: Page Type Classification (BẮT BUỘC)
            self._logger.info("Phase 1: Classifying page types")
            page_classifications = {}
            question_pages = []
            answer_key_pages = []
            
            for page in pages:
                progress.update(page.page_number, f"Classifying page {page.page_number}...")
                page_type, confidence = await self._detect_page_type(page)
                page_classifications[page.page_number] = {
                    "type": page_type,
                    "confidence": confidence
                }
                
                if page_type == "question":
                    question_pages.append(page)
                elif page_type == "answer_key":
                    answer_key_pages.append(page)
                
                self._logger.debug(f"Page {page.page_number}: {page_type} (confidence: {confidence:.2f})")

            self._logger.info(f"Classified {len(question_pages)} question pages, {len(answer_key_pages)} answer key pages")

            # Phase 2A: Extract questions from question pages only
            self._logger.info("Phase 2A: Extracting questions and diagrams")
            all_questions = []
            all_diagrams = []

            for page in question_pages:
                progress.update(page.page_number, f"Extracting questions from page {page.page_number}...")

                # Extract questions and detect diagrams in one LLM call
                questions, diagram_info_list = await self.question_extractor.extract_questions(page)
                all_questions.extend(questions)

                # Extract diagram images from bounding boxes (no additional LLM call needed)
                if extract_diagrams and diagram_info_list:
                    diagrams = self.diagram_extractor.extract_diagrams_from_info(
                        diagram_info_list, page
                    )
                    all_diagrams.extend(diagrams)

                    # Link diagrams to questions
                    self.diagram_extractor.link_diagrams_to_questions(
                        diagrams, questions, page.page_number
                    )

            # Phase 2B: Extract answer keys from answer_key pages only (output to separate file)
            all_answer_keys = {}  # Dict[str, AnswerKey] - question_ref -> AnswerKey
            
            if extract_answers and answer_key_pages:
                self._logger.info("Phase 2B: Extracting answer keys")
                progress.update(len(pages), "Extracting answer keys...")

                for page in answer_key_pages:
                    answers = await self.answer_key_agent.extract_answers(page)
                    all_answer_keys.update(answers)
                    self._logger.info(f"Extracted {len(answers)} answers from page {page.page_number}")

                # Save answer keys to separate file
                self._save_answer_keys(all_answer_keys, pdf_path.stem)

            # Phase 3: Merge answer keys to questions (CODE ONLY, NO LLM)
            if extract_answers and all_answer_keys:
                self._logger.info("Phase 3: Merging answer keys to questions")
                merged_count = self._merge_answer_keys_to_questions(all_questions, all_answer_keys)
                self._logger.info(f"Merged {merged_count} answer keys to questions")

            # Phase 5: Build final result
            progress.complete("Extraction complete")

            # End tracking
            metrics_data = self.cost_tracker.end_run()

            # Build extraction metrics
            extraction_metrics = ExtractionMetrics(
                total_tokens_used=metrics_data.total_tokens,
                total_cost_usd=metrics_data.total_cost,
                processing_time_seconds=(datetime.now() - start_time).total_seconds(),
                pages_processed=len(pages),
                questions_extracted=len(all_questions),
                diagrams_extracted=len(all_diagrams),
                agents_used=["PDFParser", "QuestionExtractor", "DiagramExtractor", "AnswerKeyAgent"],
                errors=[e for e in metrics_data.errors]
            )

            # Create exam paper
            exam_paper = ExamPaper(
                metadata=metadata,
                questions=all_questions,
                extraction_metrics=extraction_metrics
            )

            # Save results
            self._save_results(exam_paper, pdf_path.stem)

            # Print summary
            self._print_summary(exam_paper)

            return exam_paper

        except Exception as e:
            self._logger.error(f"Pipeline failed: {e}")
            if self.cost_tracker.current_run:
                self.cost_tracker.log_error("Orchestrator", e)
                self.cost_tracker.end_run()
            raise

    def process_pdf_sync(
        self,
        pdf_path: str,
        extract_diagrams: bool = True,
        extract_answers: bool = True,
        detect_metadata: bool = True
    ) -> ExamPaper:
        """Synchronous version of process_pdf."""
        return asyncio.run(self.process_pdf(
            pdf_path, extract_diagrams, extract_answers, detect_metadata
        ))

    async def process_multiple_pdfs(
        self,
        pdf_paths: List[str],
        parallel: bool = False
    ) -> List[ExamPaper]:
        """
        Process multiple PDF files.

        Args:
            pdf_paths: List of PDF file paths
            parallel: Whether to process in parallel (uses more API quota)

        Returns:
            List of ExamPaper objects
        """
        results = []

        if parallel:
            tasks = [self.process_pdf(path) for path in pdf_paths]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Filter out exceptions
            results = [r for r in results if not isinstance(r, Exception)]
        else:
            for path in pdf_paths:
                try:
                    result = await self.process_pdf(path)
                    results.append(result)
                except Exception as e:
                    self._logger.error(f"Failed to process {path}: {e}")

        return results

    async def _extract_metadata(
        self,
        first_page: PageContent,
        filename: str
    ) -> ExamMetadata:
        """Extract exam metadata from the first page."""
        # Use heuristics and filename parsing
        # Handle None values safely
        filename = filename or ""
        page_text = first_page.text if first_page.text else ""
        
        metadata = ExamMetadata(source_file=filename)

        # Parse filename for info
        filename_lower = filename.lower()

        # Detect subject
        metadata.subject = self._detect_subject(filename, page_text)

        # Detect year
        import re
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            metadata.year = int(year_match.group())

        # Detect grade level
        grade_patterns = [
            (r'p[1-6]', lambda m: m.group().upper()),
            (r'primary\s*[1-6]', lambda m: f"P{m.group()[-1]}"),
            (r'sec(?:ondary)?\s*[1-5]', lambda m: f"S{m.group()[-1]}"),
        ]
        for pattern, extractor in grade_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                metadata.grade_level = extractor(match)
                break

        # Detect exam type
        exam_types = {
            'sa1': 'SA1',
            'sa2': 'SA2',
            'prelim': 'Preliminary Exam',
            'mid-year': 'Mid-Year',
            'final': 'Final Exam',
            'mock': 'Mock Exam'
        }
        for key, value in exam_types.items():
            if key in filename_lower:
                metadata.exam_type = value
                break

        # Detect school from filename
        school_match = re.search(r'[-_]([A-Za-z\s]+)(?:primary|school)?\.pdf', filename, re.IGNORECASE)
        if school_match:
            metadata.school = school_match.group(1).strip()

        return metadata

    def _detect_subject(self, filename: str, text: str) -> Subject:
        """Detect subject from filename and content."""
        # Handle None values safely
        filename = filename or ""
        text = text or ""
        combined = (filename + " " + text[:500]).lower()

        if 'math' in combined:
            return Subject.MATHEMATICS
        elif 'science' in combined:
            return Subject.SCIENCE
        elif 'physics' in combined:
            return Subject.PHYSICS
        elif 'chemistry' in combined:
            return Subject.CHEMISTRY
        elif 'biology' in combined:
            return Subject.BIOLOGY
        else:
            return Subject.OTHER

    def _save_results(self, exam_paper: ExamPaper, pdf_name: str) -> None:
        """Save extraction results to files."""
        # Save JSON output
        questions_dir = self.output_dir / "questions"
        questions_dir.mkdir(exist_ok=True)

        output_file = questions_dir / f"{pdf_name}_extracted.json"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(exam_paper.to_json(indent=2))

        self._logger.info(f"Saved results to {output_file}")

        # Save individual questions for easier access
        individual_dir = questions_dir / pdf_name
        individual_dir.mkdir(exist_ok=True)

        for i, question in enumerate(exam_paper.questions):
            q_file = individual_dir / f"q{question.question_number or i+1}.json"
            with open(q_file, "w", encoding="utf-8") as f:
                json.dump(question.to_dict(), f, indent=2, ensure_ascii=False)

    def _save_answer_keys(
        self,
        answer_keys: Dict[str, Any],
        pdf_name: str
    ) -> None:
        """
        Save answer keys to a separate JSON file.
        
        Args:
            answer_keys: Dictionary mapping question_ref to AnswerKey objects
            pdf_name: PDF filename (without extension)
        """
        answer_keys_dir = self.output_dir / "answer_keys"
        answer_keys_dir.mkdir(exist_ok=True)

        # Convert AnswerKey objects to dict
        answer_keys_data = {
            "source_pdf": pdf_name,
            "extracted_at": datetime.now().isoformat(),
            "answers": []
        }

        for question_ref, answer_key in answer_keys.items():
            if hasattr(answer_key, 'to_dict'):
                answer_data = answer_key.to_dict()
            else:
                answer_data = answer_key
            
            answer_data["question_ref"] = question_ref
            answer_keys_data["answers"].append(answer_data)

        # Save to JSON
        output_file = answer_keys_dir / f"{pdf_name}_answer_keys.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(answer_keys_data, f, indent=2, ensure_ascii=False)

        self._logger.info(f"Saved {len(answer_keys)} answer keys to {output_file}")

    def _merge_answer_keys_to_questions(
        self,
        questions: List[Question],
        answer_keys: Dict[str, Any]
    ) -> int:
        """
        Merge answer keys to questions (CODE ONLY, NO LLM).
        
        Logic:
        - Normalize question_ref from answer_keys
        - Match with question.question_number
        - For MCQ: set is_correct = true on matching option
        - For non-MCQ: attach answer_key object
        
        Args:
            questions: List of Question objects
            answer_keys: Dictionary mapping question_ref to AnswerKey objects
            
        Returns:
            Number of successful merges
        """
        import re
        
        def normalize_question_number(q_num: str) -> str:
            """Normalize question number for matching."""
            if not q_num:
                return ""
            # Remove parentheses, spaces, dots, convert to lowercase
            normalized = re.sub(r'[().\s]', '', q_num.lower())
            return normalized

        merged_count = 0

        for question in questions:
            # Try exact match
            if question.question_number in answer_keys:
                answer_key = answer_keys[question.question_number]
                self._attach_answer_to_question(question, answer_key)
                merged_count += 1
                continue

            # Try normalized match
            q_normalized = normalize_question_number(question.question_number)
            for question_ref, answer_key in answer_keys.items():
                ref_normalized = normalize_question_number(question_ref)
                if ref_normalized == q_normalized:
                    self._attach_answer_to_question(question, answer_key)
                    merged_count += 1
                    break

            # Handle subparts
            for subpart in question.subparts:
                if subpart.question_number in answer_keys:
                    answer_key = answer_keys[subpart.question_number]
                    self._attach_answer_to_question(subpart, answer_key)
                    merged_count += 1
                    continue

                # Try normalized match for subpart
                subpart_normalized = normalize_question_number(subpart.question_number)
                for question_ref, answer_key in answer_keys.items():
                    ref_normalized = normalize_question_number(question_ref)
                    if ref_normalized == subpart_normalized:
                        self._attach_answer_to_question(subpart, answer_key)
                        merged_count += 1
                        break

        return merged_count

    def _attach_answer_to_question(
        self,
        question: Question,
        answer_key: Any
    ) -> None:
        """
        Attach answer key to question.
        For MCQ: set is_correct = true on matching option.
        For non-MCQ: attach answer_key object.
        """
        # Handle AnswerKey object
        if hasattr(answer_key, 'final_answer'):
            final_answer = answer_key.final_answer
        elif isinstance(answer_key, dict):
            final_answer = answer_key.get("final_answer", answer_key.get("answer", ""))
        else:
            final_answer = str(answer_key)

        # For MCQ: set is_correct on matching option
        if question.response_type.value == "MULTIPLE_CHOICE" and question.response_config:
            if question.response_config.options:
                # Try to match answer with option label or text
                for option in question.response_config.options:
                    # Match by label (A, B, C, D or 1, 2, 3, 4)
                    if option.label.upper() == final_answer.upper():
                        option.is_correct = True
                        break
                    # Match by text
                    if option.text and final_answer.lower() in option.text.lower():
                        option.is_correct = True
                        break
                    # Match exact text
                    if option.text and option.text.strip() == final_answer.strip():
                        option.is_correct = True
                        break

        # Attach answer_key object (for all question types)
        if hasattr(answer_key, 'to_dict'):
            # It's an AnswerKey object
            question.answer_key = answer_key
        elif isinstance(answer_key, dict):
            # Convert dict to AnswerKey object
            from ..models import AnswerKey, WorkedSolutionStep, MarkingCriterion
            
            worked_solution = []
            for step_data in answer_key.get("worked_solution", []):
                step = WorkedSolutionStep(
                    step_number=step_data.get("step", step_data.get("step_number", 0)),
                    description=step_data.get("description", ""),
                    expression=step_data.get("expression"),
                    expression_latex=step_data.get("expression_latex")
                )
                worked_solution.append(step)
            
            marking_rubric = []
            for rubric_data in answer_key.get("marking_rubric", answer_key.get("marks_breakdown", [])):
                criterion = MarkingCriterion(
                    criterion=rubric_data.get("criterion", ""),
                    marks=rubric_data.get("marks", 0)
                )
                marking_rubric.append(criterion)
            
            question.answer_key = AnswerKey(
                final_answer=final_answer,
                worked_solution=worked_solution,
                marking_rubric=marking_rubric,
                explanation=answer_key.get("explanation")
            )
        else:
            # Simple string answer
            from ..models import AnswerKey
            question.answer_key = AnswerKey(final_answer=final_answer)

    def _print_summary(self, exam_paper: ExamPaper) -> None:
        """Print extraction summary."""
        print("\n" + "=" * 60)
        print("EXTRACTION SUMMARY")
        print("=" * 60)
        print(f"Source:          {exam_paper.metadata.source_file}")
        print(f"Subject:         {exam_paper.metadata.subject.value}")
        print(f"Grade:           {exam_paper.metadata.grade_level or 'Unknown'}")
        print(f"Year:            {exam_paper.metadata.year or 'Unknown'}")
        print("-" * 60)
        print(f"Pages Processed: {exam_paper.extraction_metrics.pages_processed}")
        print(f"Questions:       {exam_paper.extraction_metrics.questions_extracted}")
        print(f"Diagrams:        {exam_paper.extraction_metrics.diagrams_extracted}")
        print("-" * 60)
        print(f"Total Tokens:    {exam_paper.extraction_metrics.total_tokens_used:,}")
        print(f"Total Cost:      ${exam_paper.extraction_metrics.total_cost_usd:.4f}")
        print(f"Processing Time: {exam_paper.extraction_metrics.processing_time_seconds:.1f}s")
        print("=" * 60)

        # Question breakdown
        if exam_paper.questions:
            print("\nQUESTION BREAKDOWN:")
            for q in exam_paper.questions:
                has_answer = "+" if q.answer_key else "-"
                has_diagram = "D" if q.diagrams else " "
                subparts = f" ({len(q.subparts)} parts)" if q.subparts else ""
                print(f"  [{has_answer}][{has_diagram}] Q{q.question_number}: {q.response_type.value}{subparts}")

        print()

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary."""
        return self.cost_tracker.get_current_stats()


class ExamExtractor:
    """
    High-level API for exam extraction.
    Simple interface for common use cases.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        output_dir: str = "output"
    ):
        self.orchestrator = OrchestratorAgent(
            api_key=api_key,
            output_dir=output_dir
        )

    def extract(self, pdf_path: str) -> ExamPaper:
        """
        Extract questions from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ExamPaper object with all extracted content
        """
        return self.orchestrator.process_pdf_sync(pdf_path)

    def extract_questions_only(self, pdf_path: str) -> List[Question]:
        """
        Extract only questions (no diagrams or answers).

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of Question objects
        """
        result = self.orchestrator.process_pdf_sync(
            pdf_path,
            extract_diagrams=False,
            extract_answers=False
        )
        return result.questions

    def extract_to_json(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract and save to JSON file.

        Args:
            pdf_path: Path to the PDF file
            output_path: Optional output path (auto-generated if not provided)

        Returns:
            Path to the saved JSON file
        """
        result = self.extract(pdf_path)

        if not output_path:
            pdf_name = Path(pdf_path).stem
            output_path = f"{pdf_name}_extracted.json"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.to_json(indent=2))

        return output_path
