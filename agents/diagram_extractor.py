"""Diagram Extractor Agent - Extracts diagrams using Gemini bounding box detection."""

import google.generativeai as genai
from typing import List, Optional, Dict, Any, Tuple
import json
import logging
import uuid
import re
from PIL import Image
import base64
import io
from pathlib import Path

from ..models import Diagram, DiagramType, BoundingBox
from ..tracking import CostTracker, PipelineLogger
from .prompts import DIAGRAM_DETECTION_PROMPT
from .pdf_parser import PageContent


class DiagramExtractorAgent:
    """
    Extracts diagrams from exam pages using Gemini's bounding box detection.
    Reference: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/bounding-box-detection
    """

    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        cost_tracker: Optional[CostTracker] = None,
        pipeline_logger: Optional[PipelineLogger] = None,
        output_dir: str = "output/diagrams",
        api_key: Optional[str] = None
    ):
        self.model_name = model_name
        self.cost_tracker = cost_tracker
        self.pipeline_logger = pipeline_logger
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger("DiagramExtractor")

        if api_key:
            genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel(model_name)

    async def extract_diagrams(
        self,
        page_content: PageContent,
        min_confidence: float = 0.5
    ) -> List[Diagram]:
        """
        Extract all diagrams from a page using bounding box detection.

        Args:
            page_content: PageContent object with page image
            min_confidence: Minimum confidence threshold for including diagrams

        Returns:
            List of Diagram objects with cropped images
        """
        if not page_content.image:
            self._logger.warning(f"No image for page {page_content.page_number}")
            return []

        self._logger.info(f"Extracting diagrams from page {page_content.page_number}")

        if self.pipeline_logger:
            self.pipeline_logger.log_agent_input("DiagramExtractor", "extract", {
                "page_number": page_content.page_number,
                "image_size": f"{page_content.image.width}x{page_content.image.height}"
            })

        # Prepare image
        image_part = self._image_to_part(page_content.image)

        # Build prompt for bounding box detection
        prompt = DIAGRAM_DETECTION_PROMPT

        try:
            response = await self.model.generate_content_async(
                [prompt, image_part],
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )

            # Track token usage
            if self.cost_tracker and hasattr(response, 'usage_metadata'):
                self.cost_tracker.log_usage(
                    agent="DiagramExtractor",
                    operation="detect_diagrams",
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.candidates_token_count,
                    model=self.model_name
                )

            # Parse response
            result = self._parse_response(response.text)

            # Extract and crop diagrams
            diagrams = []
            for diag_data in result.get("diagrams", []):
                confidence = diag_data.get("confidence", 0.8)
                if confidence < min_confidence:
                    continue

                diagram = self._create_diagram(
                    diag_data,
                    page_content.image,
                    page_content.page_number
                )
                if diagram:
                    diagrams.append(diagram)

            # Handle shared diagram instructions
            shared_instructions = result.get("shared_diagram_instructions", [])
            for instruction in shared_instructions:
                diag_id = instruction.get("diagram_id")
                questions = instruction.get("question_range", [])
                # Find and update the diagram
                for diag in diagrams:
                    if diag.id == diag_id or diag_id in str(diag.id):
                        diag.is_shared = True
                        diag.shared_with_questions = questions

            if self.pipeline_logger:
                self.pipeline_logger.log_agent_output("DiagramExtractor", "extract", {
                    "diagrams_found": len(diagrams),
                    "diagram_types": [d.type.value for d in diagrams]
                })

            if self.cost_tracker:
                self.cost_tracker.update_counts(diagrams=len(diagrams))

            self._logger.info(f"Extracted {len(diagrams)} diagrams from page {page_content.page_number}")
            return diagrams

        except Exception as e:
            self._logger.error(f"Failed to extract diagrams: {e}")
            if self.pipeline_logger:
                self.pipeline_logger.log_error("DiagramExtractor", "extract", e, {
                    "page_number": page_content.page_number
                })
            return []

    def extract_diagrams_sync(
        self,
        page_content: PageContent,
        min_confidence: float = 0.5
    ) -> List[Diagram]:
        """Synchronous version of extract_diagrams."""
        import asyncio
        return asyncio.run(self.extract_diagrams(page_content, min_confidence))

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
            return {"diagrams": []}

    def _create_diagram(
        self,
        diag_data: Dict[str, Any],
        page_image: Image.Image,
        page_number: int
    ) -> Optional[Diagram]:
        """
        Create a Diagram object from parsed data.
        Diagrams are stored as region references (no image cropping/saving).
        """
        try:
            # Parse bounding box (0-1000 scale from Gemini)
            bbox_data = diag_data.get("bounding_box", {})
            if not bbox_data:
                return None

            # Validate bounding box (0-1000 scale)
            x1 = bbox_data.get("x1", 0)
            y1 = bbox_data.get("y1", 0)
            x2 = bbox_data.get("x2", 0)
            y2 = bbox_data.get("y2", 0)

            if x2 <= x1 or y2 <= y1 or x1 < 0 or y1 < 0 or x2 > 1000 or y2 > 1000:
                self._logger.warning(f"Invalid bounding box: ({x1}, {y1}, {x2}, {y2})")
                return None

            # Generate unique ID
            diagram_id = str(uuid.uuid4())[:8]

            # Map diagram type
            diag_type = self._map_diagram_type(diag_data.get("type", "DIAGRAM"))

            # Create bounding box (as percentage 0-100 for storage)
            bounding_box = BoundingBox(
                x1=x1 / 10,  # Convert 0-1000 to 0-100
                y1=y1 / 10,
                x2=x2 / 10,
                y2=y2 / 10
            )

            # Create Diagram object (metadata only, no image storage)
            return Diagram(
                id=diagram_id,
                type=diag_type,
                alt_text=diag_data.get("description", ""),
                description=diag_data.get("description", ""),
                bounding_box=bounding_box,
                source_page=page_number,
                is_shared=diag_data.get("is_shared", False),
                shared_with_questions=diag_data.get("shared_with_questions", []),
                extraction_confidence=diag_data.get("confidence", 0.8)
            )

        except Exception as e:
            self._logger.error(f"Failed to create diagram: {e}")
            return None

    def _map_diagram_type(self, type_str: str) -> DiagramType:
        """Map string type to DiagramType enum."""
        type_map = {
            "GRAPH": DiagramType.GRAPH,
            "GEOMETRIC_FIGURE": DiagramType.GEOMETRIC_FIGURE,
            "CHART": DiagramType.CHART,
            "ILLUSTRATION": DiagramType.ILLUSTRATION,
            "TABLE": DiagramType.TABLE,
            "CIRCUIT": DiagramType.CIRCUIT,
            "MAP": DiagramType.MAP,
            "SCIENTIFIC": DiagramType.SCIENTIFIC,
            "DIAGRAM": DiagramType.DIAGRAM
        }
        return type_map.get(type_str.upper(), DiagramType.DIAGRAM)

    def extract_diagrams_from_info(
        self,
        diagram_info_list: List[dict],
        page_content: PageContent
    ) -> List[Diagram]:
        """
        Create Diagram objects from bounding boxes detected by LLM.
        Diagrams are stored as region references on the page image (no cropping/saving).
        
        Args:
            diagram_info_list: List of diagram info dicts from QuestionExtractor
            page_content: PageContent with page image (kept as full page)
            
        Returns:
            List of Diagram objects with metadata only
        """
        diagrams = []
        for diag_info in diagram_info_list:
            try:
                # Get bounding box (0-1000 scale from LLM)
                bbox = diag_info.get("bounding_box", {})
                if not bbox:
                    self._logger.warning(f"No bounding box for diagram: {diag_info}")
                    continue
                
                # Validate bounding box
                x_min = bbox.get("x_min", 0)
                y_min = bbox.get("y_min", 0)
                x_max = bbox.get("x_max", 1000)
                y_max = bbox.get("y_max", 1000)
                
                if x_max <= x_min or y_max <= y_min or x_min < 0 or y_min < 0 or x_max > 1000 or y_max > 1000:
                    self._logger.warning(f"Invalid bounding box for diagram: {bbox}")
                    continue
                
                # Generate unique ID
                diagram_id = str(uuid.uuid4())[:8]
                
                # Map diagram type
                diag_type = self._map_diagram_type(diag_info.get("diagram_type", "DIAGRAM"))
                
                # Create bounding box (as percentage 0-100 for storage)
                bounding_box = BoundingBox(
                    x1=x_min / 10,  # Convert 0-1000 to 0-100
                    y1=y_min / 10,
                    x2=x_max / 10,
                    y2=y_max / 10
                )
                
                # Create Diagram object (metadata only, no image storage)
                diagram = Diagram(
                    id=diagram_id,
                    type=diag_type,
                    alt_text=diag_info.get("description", ""),
                    description=diag_info.get("description", ""),
                    bounding_box=bounding_box,
                    source_page=page_content.page_number,
                    is_shared=False,
                    shared_with_questions=[],
                    extraction_confidence=0.9  # High confidence from LLM detection
                )
                
                diagrams.append(diagram)
                
            except Exception as e:
                self._logger.error(f"Failed to create diagram from info: {e}")
                continue
        
        if self.cost_tracker:
            self.cost_tracker.update_counts(diagrams=len(diagrams))
        
        self._logger.info(f"Created {len(diagrams)} diagram references from LLM detection on page {page_content.page_number}")
        return diagrams

    def link_diagrams_to_questions(
        self,
        diagrams: List[Diagram],
        questions: List[Any],
        page_number: int
    ) -> None:
        """
        Link extracted diagrams to their corresponding questions.
        Uses spatial proximity and question number references.
        """
        import re

        for diagram in diagrams:
            if diagram.source_page != page_number:
                continue

            # Method 1: Check if diagram has associated question from extraction
            if hasattr(diagram, '_associated_question') and diagram._associated_question:
                for q in questions:
                    if q.question_number == diagram._associated_question:
                        if diagram not in q.diagrams:
                            q.diagrams.append(diagram)
                        break

            # Method 2: Check question text for diagram references
            for q in questions:
                if q.source and q.source.page_number == page_number:
                    text = q.content.text.lower() if q.content else ""
                    if self._references_diagram(text):
                        if diagram not in q.diagrams:
                            q.diagrams.append(diagram)

            # Method 3: Handle shared diagrams
            if diagram.is_shared and diagram.shared_with_questions:
                for q_num in diagram.shared_with_questions:
                    for q in questions:
                        if q.question_number == q_num:
                            if diagram not in q.diagrams:
                                q.diagrams.append(diagram)

    def _references_diagram(self, text: str) -> bool:
        """Check if text references a diagram."""
        patterns = [
            r"see\s+(the\s+)?(figure|diagram|graph|chart|table)",
            r"(figure|diagram|graph|chart|table)\s*(above|below|shown|given)",
            r"use\s+(the\s+)?(figure|diagram|graph)",
            r"refer\s+to\s+(the\s+)?(figure|diagram|graph)",
            r"in\s+the\s+(figure|diagram|graph)",
            r"from\s+the\s+(figure|diagram|graph)",
            r"the\s+(figure|diagram|graph)\s+(shows|illustrates)"
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    async def analyze_diagram_content(
        self,
        diagram: Diagram,
        page_image: Image.Image,
        question_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a diagram's content in detail for better understanding.
        Useful for generating accessible descriptions.
        
        Args:
            diagram: Diagram object with bounding box
            page_image: Full page image to crop from
            question_context: Optional context about the question
        """
        if not diagram.bounding_box:
            return {}

        # Crop diagram region from page image using bounding box
        # Bounding box is stored as 0-100 percentage, convert to pixels
        img_width, img_height = page_image.size
        x1 = int(diagram.bounding_box.x1 / 100 * img_width)
        y1 = int(diagram.bounding_box.y1 / 100 * img_height)
        x2 = int(diagram.bounding_box.x2 / 100 * img_width)
        y2 = int(diagram.bounding_box.y2 / 100 * img_height)
        
        # Validate and crop
        if x2 <= x1 or y2 <= y1:
            return {}
        
        cropped = page_image.crop((x1, y1, x2, y2))
        image_part = self._image_to_part(cropped)

        prompt = f"""Analyze this diagram in detail:

1. What type of diagram is this?
2. What are the key elements/components?
3. Are there any labels or text?
4. What relationships or processes does it show?
5. What is the main purpose of this diagram?

{f"Question context: {question_context}" if question_context else ""}

Return a detailed JSON analysis."""

        try:
            response = await self.model.generate_content_async(
                [prompt, image_part],
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )

            if self.cost_tracker and hasattr(response, 'usage_metadata'):
                self.cost_tracker.log_usage(
                    agent="DiagramExtractor",
                    operation="analyze_diagram",
                    input_tokens=response.usage_metadata.prompt_token_count,
                    output_tokens=response.usage_metadata.candidates_token_count,
                    model=self.model_name
                )

            return self._parse_response(response.text)

        except Exception as e:
            self._logger.error(f"Failed to analyze diagram: {e}")
            return {"error": str(e)}
