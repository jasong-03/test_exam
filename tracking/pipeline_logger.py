"""Structured logging for agent interactions."""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import json
import logging


class PipelineLogger:
    """
    Structured logging for all agent interactions.
    Enables debugging and quality analysis.
    """

    def __init__(self, log_dir: str = "logs/agents"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.run_id: Optional[str] = None
        self.run_dir: Optional[Path] = None
        self.logger = logging.getLogger("PipelineLogger")

    def start_run(self, run_id: str) -> None:
        """Start logging for a run."""
        self.run_id = run_id
        self.run_dir = self.log_dir / run_id
        self.run_dir.mkdir(exist_ok=True)
        self.logger.info(f"Started logging for run {run_id}")

    def log_agent_input(self, agent: str, operation: str, input_data: Dict) -> None:
        """Log input to an agent."""
        self._write_log(agent, operation, "input", input_data)

    def log_agent_output(self, agent: str, operation: str, output_data: Dict) -> None:
        """Log output from an agent."""
        self._write_log(agent, operation, "output", output_data)

    def log_agent_prompt(
        self,
        agent: str,
        operation: str,
        prompt: str,
        response: str,
        model: str = "gemini-2.5-flash"
    ) -> None:
        """Log full prompt and response for LLM calls."""
        self._write_log(agent, operation, "llm_call", {
            "model": model,
            "prompt": prompt,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })

    def log_extraction_result(
        self,
        agent: str,
        page_number: int,
        result: Dict[str, Any]
    ) -> None:
        """Log extraction results for a page."""
        self._write_log(agent, f"page_{page_number}", "extraction", result)

    def log_error(
        self,
        agent: str,
        operation: str,
        error: Exception,
        context: Dict = None
    ) -> None:
        """Log an error with context."""
        self._write_log(agent, operation, "error", {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        })
        self.logger.error(f"[{agent}:{operation}] {error}")

    def _write_log(
        self,
        agent: str,
        operation: str,
        log_type: str,
        data: Dict
    ) -> None:
        """Write a log entry to file."""
        if not self.run_id or not self.run_dir:
            self.logger.warning("No active run for logging")
            return

        agent_dir = self.run_dir / agent
        agent_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%H%M%S%f")
        filename = f"{timestamp}_{operation}_{log_type}.json"

        try:
            with open(agent_dir / filename, "w") as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to write log: {e}")

    def get_run_logs(self, agent: Optional[str] = None) -> Dict[str, Any]:
        """Get all logs for the current run."""
        if not self.run_dir or not self.run_dir.exists():
            return {}

        logs = {}
        search_dir = self.run_dir / agent if agent else self.run_dir

        for log_file in search_dir.rglob("*.json"):
            relative_path = log_file.relative_to(self.run_dir)
            try:
                with open(log_file) as f:
                    logs[str(relative_path)] = json.load(f)
            except Exception as e:
                logs[str(relative_path)] = {"error": str(e)}

        return logs


class ConsoleProgressLogger:
    """Simple console progress logger for visual feedback."""

    def __init__(self, total_pages: int = 0):
        self.total_pages = total_pages
        self.current_page = 0
        self.start_time = datetime.now()

    def update(self, page: int, status: str = "") -> None:
        """Update progress."""
        self.current_page = page
        elapsed = (datetime.now() - self.start_time).total_seconds()

        if self.total_pages > 0:
            progress = (page / self.total_pages) * 100
            print(f"\r[{progress:5.1f}%] Page {page}/{self.total_pages} - {status} ({elapsed:.1f}s)", end="")
        else:
            print(f"\rPage {page} - {status} ({elapsed:.1f}s)", end="")

    def complete(self, message: str = "Done") -> None:
        """Mark as complete."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{message} in {elapsed:.1f}s")
