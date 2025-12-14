"""Cost tracking and monitoring for the extraction pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import json
import logging
import uuid


@dataclass
class TokenUsage:
    """Track token usage for a single API call."""
    agent: str
    operation: str
    input_tokens: int
    output_tokens: int
    model: str
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def calculate_cost(self, pricing: Dict[str, float]) -> float:
        """Calculate cost based on model pricing."""
        input_cost = (self.input_tokens / 1_000_000) * pricing.get(f"{self.model}_input", 0)
        output_cost = (self.output_tokens / 1_000_000) * pricing.get(f"{self.model}_output", 0)
        return input_cost + output_cost

    def to_dict(self) -> Dict:
        return {
            "agent": self.agent,
            "operation": self.operation,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "timestamp": self.timestamp.isoformat()
        }


# Default pricing for Gemini models (per 1M tokens)
DEFAULT_PRICING = {
    "gemini-2.5-flash_input": 0.075,
    "gemini-2.5-flash_output": 0.30,
    "gemini-2.0-flash_input": 0.10,
    "gemini-2.0-flash_output": 0.40,
    "gemini-1.5-flash_input": 0.075,
    "gemini-1.5-flash_output": 0.30,
    "gemini-1.5-pro_input": 1.25,
    "gemini-1.5-pro_output": 5.00,
}


@dataclass
class PipelineMetrics:
    """Aggregate metrics for an extraction run."""
    run_id: str
    pdf_path: str
    start_time: datetime
    end_time: Optional[datetime] = None
    token_usage: List[TokenUsage] = field(default_factory=list)
    questions_extracted: int = 0
    diagrams_extracted: int = 0
    pages_processed: int = 0
    errors: List[Dict] = field(default_factory=list)
    pricing: Dict[str, float] = field(default_factory=lambda: DEFAULT_PRICING.copy())

    @property
    def total_tokens(self) -> int:
        return sum(t.total_tokens for t in self.token_usage)

    @property
    def total_input_tokens(self) -> int:
        return sum(t.input_tokens for t in self.token_usage)

    @property
    def total_output_tokens(self) -> int:
        return sum(t.output_tokens for t in self.token_usage)

    @property
    def total_cost(self) -> float:
        return sum(t.calculate_cost(self.pricing) for t in self.token_usage)

    @property
    def processing_time_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    def get_usage_by_agent(self) -> Dict[str, Dict[str, int]]:
        """Get token usage breakdown by agent."""
        breakdown = {}
        for usage in self.token_usage:
            if usage.agent not in breakdown:
                breakdown[usage.agent] = {"input": 0, "output": 0, "calls": 0}
            breakdown[usage.agent]["input"] += usage.input_tokens
            breakdown[usage.agent]["output"] += usage.output_tokens
            breakdown[usage.agent]["calls"] += 1
        return breakdown

    def to_dict(self) -> Dict:
        return {
            "run_id": self.run_id,
            "pdf_path": self.pdf_path,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "processing_time_seconds": round(self.processing_time_seconds, 2),
            "total_tokens": self.total_tokens,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "questions_extracted": self.questions_extracted,
            "diagrams_extracted": self.diagrams_extracted,
            "pages_processed": self.pages_processed,
            "usage_by_agent": self.get_usage_by_agent(),
            "token_usage_details": [t.to_dict() for t in self.token_usage],
            "errors": self.errors
        }


class CostTracker:
    """
    Central cost tracking for the entire pipeline.
    Provides real-time monitoring and historical analysis.
    """

    def __init__(self, log_dir: str = "logs/costs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.current_run: Optional[PipelineMetrics] = None
        self.logger = logging.getLogger("CostTracker")
        self.pricing = DEFAULT_PRICING.copy()

    def start_run(self, pdf_path: str) -> str:
        """Start tracking a new extraction run."""
        run_id = str(uuid.uuid4())[:8]
        self.current_run = PipelineMetrics(
            run_id=run_id,
            pdf_path=pdf_path,
            start_time=datetime.now(),
            pricing=self.pricing
        )
        self.logger.info(f"Started extraction run {run_id} for {pdf_path}")
        return run_id

    def log_usage(
        self,
        agent: str,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "gemini-2.5-flash"
    ) -> None:
        """Log token usage for an API call."""
        if not self.current_run:
            self.logger.warning("No active run. Creating anonymous run.")
            self.start_run("unknown")

        usage = TokenUsage(
            agent=agent,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model
        )
        self.current_run.token_usage.append(usage)

        cost = usage.calculate_cost(self.pricing)
        self.logger.debug(
            f"[{agent}] {operation}: {input_tokens:,} in / {output_tokens:,} out = ${cost:.6f}"
        )

    def log_error(self, agent: str, error: Exception, context: Dict = None) -> None:
        """Log an error during extraction."""
        if self.current_run:
            self.current_run.errors.append({
                "agent": agent,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            })
            self.logger.error(f"[{agent}] Error: {error}")

    def update_counts(
        self,
        questions: int = 0,
        diagrams: int = 0,
        pages: int = 0
    ) -> None:
        """Update extraction counts."""
        if self.current_run:
            self.current_run.questions_extracted += questions
            self.current_run.diagrams_extracted += diagrams
            self.current_run.pages_processed += pages

    def end_run(self) -> PipelineMetrics:
        """End the current run and save metrics."""
        if not self.current_run:
            raise ValueError("No active run to end.")

        self.current_run.end_time = datetime.now()

        # Save to file
        log_file = self.log_dir / f"{self.current_run.run_id}.json"
        with open(log_file, "w") as f:
            json.dump(self.current_run.to_dict(), f, indent=2, default=str)

        self.logger.info(
            f"Completed run {self.current_run.run_id}: "
            f"{self.current_run.questions_extracted} questions, "
            f"{self.current_run.diagrams_extracted} diagrams, "
            f"{self.current_run.total_tokens:,} tokens, "
            f"${self.current_run.total_cost:.4f}"
        )

        result = self.current_run
        self.current_run = None
        return result

    def get_current_stats(self) -> Dict:
        """Get current run statistics."""
        if not self.current_run:
            return {"status": "no_active_run"}

        return {
            "run_id": self.current_run.run_id,
            "elapsed_seconds": (datetime.now() - self.current_run.start_time).total_seconds(),
            "total_tokens": self.current_run.total_tokens,
            "current_cost": round(self.current_run.total_cost, 6),
            "api_calls": len(self.current_run.token_usage),
            "questions": self.current_run.questions_extracted,
            "diagrams": self.current_run.diagrams_extracted
        }

    def print_summary(self) -> None:
        """Print a summary of the current run."""
        if not self.current_run:
            print("No active run.")
            return

        stats = self.get_current_stats()
        print("\n" + "=" * 50)
        print("EXTRACTION PIPELINE STATS")
        print("=" * 50)
        print(f"Run ID:          {stats['run_id']}")
        print(f"Elapsed:         {stats['elapsed_seconds']:.1f}s")
        print(f"API Calls:       {stats['api_calls']}")
        print(f"Total Tokens:    {stats['total_tokens']:,}")
        print(f"Current Cost:    ${stats['current_cost']:.4f}")
        print(f"Questions:       {stats['questions']}")
        print(f"Diagrams:        {stats['diagrams']}")
        print("-" * 50)
        print("Usage by Agent:")
        for agent, usage in self.current_run.get_usage_by_agent().items():
            print(f"  {agent}: {usage['input']:,} in / {usage['output']:,} out ({usage['calls']} calls)")
        print("=" * 50 + "\n")
