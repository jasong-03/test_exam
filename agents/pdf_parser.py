"""PDF Parser Agent - Extracts raw content from PDF files."""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from PIL import Image
import io
import logging

from ..tracking import CostTracker, PipelineLogger


@dataclass
class PageContent:
    """Content extracted from a single PDF page."""
    page_number: int
    text: str
    image: Optional[Image.Image] = None
    image_path: Optional[str] = None
    width: int = 0
    height: int = 0
    has_images: bool = False
    embedded_images: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "page_number": self.page_number,
            "text_length": len(self.text),
            "has_image": self.image is not None,
            "width": self.width,
            "height": self.height,
            "has_embedded_images": self.has_images,
            "embedded_image_count": len(self.embedded_images)
        }


class PDFParserAgent:
    """
    Extracts raw content from PDF files using PyMuPDF.
    Handles both text-based and scanned PDFs.
    """

    def __init__(
        self,
        cost_tracker: Optional[CostTracker] = None,
        pipeline_logger: Optional[PipelineLogger] = None,
        output_dir: str = "output/pages"
    ):
        self.cost_tracker = cost_tracker
        self.logger = pipeline_logger
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger("PDFParserAgent")

    def parse(self, pdf_path: str, render_dpi: int = 150) -> List[PageContent]:
        """
        Parse a PDF file and extract content from all pages.

        Args:
            pdf_path: Path to the PDF file
            render_dpi: DPI for rendering pages as images (higher = better quality but larger)

        Returns:
            List of PageContent objects, one per page
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        self._logger.info(f"Parsing PDF: {pdf_path.name}")

        if self.logger:
            self.logger.log_agent_input("PDFParser", "parse", {
                "pdf_path": str(pdf_path),
                "render_dpi": render_dpi
            })

        pages = []
        doc = fitz.open(str(pdf_path))

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_content = self._extract_page_content(
                    page,
                    page_num + 1,  # 1-indexed
                    pdf_path.stem,
                    render_dpi
                )
                pages.append(page_content)
                self._logger.debug(f"Extracted page {page_num + 1}: {len(page_content.text)} chars")

        finally:
            doc.close()

        if self.logger:
            self.logger.log_agent_output("PDFParser", "parse", {
                "total_pages": len(pages),
                "pages": [p.to_dict() for p in pages]
            })

        if self.cost_tracker:
            self.cost_tracker.update_counts(pages=len(pages))

        self._logger.info(f"Parsed {len(pages)} pages from {pdf_path.name}")
        return pages

    def _extract_page_content(
        self,
        page: fitz.Page,
        page_number: int,
        pdf_name: str,
        render_dpi: int
    ) -> PageContent:
        """Extract content from a single page."""
        # Extract text with layout preservation
        text = page.get_text("text")

        # Get page dimensions
        rect = page.rect
        width = int(rect.width)
        height = int(rect.height)

        # Render page as image
        mat = fitz.Matrix(render_dpi / 72, render_dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))

        # Save the page image
        image_filename = f"{pdf_name}_page_{page_number}.png"
        image_path = self.output_dir / image_filename
        image.save(image_path)

        # Extract embedded images
        embedded_images = self._extract_embedded_images(page, page_number, pdf_name)

        return PageContent(
            page_number=page_number,
            text=text,
            image=image,
            image_path=str(image_path),
            width=width,
            height=height,
            has_images=len(embedded_images) > 0,
            embedded_images=embedded_images
        )

    def _extract_embedded_images(
        self,
        page: fitz.Page,
        page_number: int,
        pdf_name: str
    ) -> List[dict]:
        """Extract embedded images from a page."""
        images = []
        image_list = page.get_images()

        for img_idx, img_info in enumerate(image_list):
            try:
                xref = img_info[0]
                base_image = page.parent.extract_image(xref)

                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    # Save embedded image
                    img_filename = f"{pdf_name}_page_{page_number}_img_{img_idx}.{image_ext}"
                    img_path = self.output_dir / img_filename

                    with open(img_path, "wb") as f:
                        f.write(image_bytes)

                    # Get image position on page
                    img_rect = page.get_image_rects(xref)
                    bbox = None
                    if img_rect:
                        r = img_rect[0]
                        page_rect = page.rect
                        bbox = {
                            "x1": (r.x0 / page_rect.width) * 100,
                            "y1": (r.y0 / page_rect.height) * 100,
                            "x2": (r.x1 / page_rect.width) * 100,
                            "y2": (r.y1 / page_rect.height) * 100
                        }

                    images.append({
                        "index": img_idx,
                        "path": str(img_path),
                        "format": image_ext,
                        "width": base_image.get("width", 0),
                        "height": base_image.get("height", 0),
                        "bounding_box": bbox
                    })

            except Exception as e:
                self._logger.warning(f"Failed to extract image {img_idx} from page {page_number}: {e}")

        return images

    def get_page_count(self, pdf_path: str) -> int:
        """Get the number of pages in a PDF."""
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count

    def extract_text_only(self, pdf_path: str) -> str:
        """Extract all text from PDF without rendering images."""
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n\n"
        doc.close()
        return text

    def detect_if_scanned(self, pdf_path: str, min_text_ratio: float = 0.1) -> bool:
        """
        Detect if PDF is primarily scanned (images) vs native text.

        Args:
            pdf_path: Path to PDF
            min_text_ratio: Minimum ratio of text to page count to consider native

        Returns:
            True if PDF appears to be scanned (needs OCR)
        """
        doc = fitz.open(pdf_path)
        total_text_len = 0
        page_count = len(doc)

        for page in doc:
            total_text_len += len(page.get_text("text").strip())

        doc.close()

        # If very little text, likely scanned
        avg_text_per_page = total_text_len / max(page_count, 1)
        return avg_text_per_page < 100  # Less than 100 chars per page = likely scanned
