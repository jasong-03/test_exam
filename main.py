#!/usr/bin/env python3
"""
Growtrics Exam Extractor - CLI Entry Point

Usage:
    python -m exam_extractor.main <pdf_path> [options]

Examples:
    python -m exam_extractor.main sample_pdf/P5_Maths_2023_SA2_acsprimary.pdf
    python -m exam_extractor.main sample_pdf/*.pdf --parallel
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from exam_extractor import ExamExtractor, OrchestratorAgent


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    # Reduce noise from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def print_banner() -> None:
    """Print application banner."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║       GROWTRICS EXAM QUESTION EXTRACTOR                   ║
║       Multi-Agent System for PDF Extraction               ║
╚═══════════════════════════════════════════════════════════╝
    """)


def get_pdf_files(paths: List[str]) -> List[Path]:
    """Get list of PDF files from paths (supports glob patterns)."""
    pdf_files = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_file() and path.suffix.lower() == '.pdf':
            pdf_files.append(path)
        elif path.is_dir():
            pdf_files.extend(path.glob("*.pdf"))
        elif '*' in path_str:
            # Handle glob patterns
            parent = path.parent
            pattern = path.name
            pdf_files.extend(parent.glob(pattern))
    return pdf_files


async def process_pdfs(
    pdf_files: List[Path],
    output_dir: str,
    api_key: str,
    parallel: bool = False,
    extract_diagrams: bool = True,
    extract_answers: bool = True
) -> None:
    """Process PDF files."""
    orchestrator = OrchestratorAgent(
        output_dir=output_dir,
        api_key=api_key
    )

    if parallel and len(pdf_files) > 1:
        print(f"\nProcessing {len(pdf_files)} PDFs in parallel...")
        results = await orchestrator.process_multiple_pdfs(
            [str(p) for p in pdf_files],
            parallel=True
        )
        print(f"\nCompleted {len(results)} PDFs successfully")
    else:
        for pdf_file in pdf_files:
            print(f"\n{'='*60}")
            print(f"Processing: {pdf_file.name}")
            print('='*60)

            try:
                result = await orchestrator.process_pdf(
                    str(pdf_file),
                    extract_diagrams=extract_diagrams,
                    extract_answers=extract_answers
                )
                print(f"\nExtracted {len(result.questions)} questions")
            except Exception as e:
                logging.error(f"Failed to process {pdf_file.name}: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract structured questions from exam PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s exam.pdf
  %(prog)s *.pdf --parallel
  %(prog)s exam.pdf --no-diagrams --output results/
        """
    )

    parser.add_argument(
        "pdf_paths",
        nargs="+",
        help="PDF file(s) to process (supports glob patterns)"
    )

    parser.add_argument(
        "-o", "--output",
        default="output",
        help="Output directory (default: output)"
    )

    parser.add_argument(
        "-k", "--api-key",
        default=os.environ.get("GEMINI_API_KEY"),
        help="Gemini API key (or set GEMINI_API_KEY env var)"
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Process multiple PDFs in parallel"
    )

    parser.add_argument(
        "--no-diagrams",
        action="store_true",
        help="Skip diagram extraction"
    )

    parser.add_argument(
        "--no-answers",
        action="store_true",
        help="Skip answer key extraction"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Setup
    setup_logging(args.verbose)
    print_banner()

    # Validate API key
    if not args.api_key:
        print("Error: Gemini API key required. Set GEMINI_API_KEY or use --api-key")
        sys.exit(1)

    # Get PDF files
    pdf_files = get_pdf_files(args.pdf_paths)
    if not pdf_files:
        print(f"Error: No PDF files found in {args.pdf_paths}")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF file(s):")
    for f in pdf_files:
        print(f"  - {f.name}")

    # Process
    asyncio.run(process_pdfs(
        pdf_files=pdf_files,
        output_dir=args.output,
        api_key=args.api_key,
        parallel=args.parallel,
        extract_diagrams=not args.no_diagrams,
        extract_answers=not args.no_answers
    ))

    print("\nDone!")


if __name__ == "__main__":
    main()
