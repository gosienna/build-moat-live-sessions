#!/usr/bin/env python3
"""Run a job description from data/chatgpt_task.db through LLMCaller.

Usage (from scaffold/):
    python scripts/test_llm_job.py
    python scripts/test_llm_job.py --job-id 1
    python scripts/test_llm_job.py --provider openai
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# scaffold/ on sys.path when run as: python scripts/test_llm_job.py
_SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
if str(_SCAFFOLD_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCAFFOLD_ROOT))

from dotenv import load_dotenv

from app.database import DATABASE_URL, SessionLocal
from app.LLMcaller import LLMCaller
from app.models import Job


def _load_env() -> None:
    for env_path in (
        _SCAFFOLD_ROOT.parent / ".env",
        _SCAFFOLD_ROOT / ".env",
    ):
        if env_path.is_file():
            load_dotenv(env_path)
            return
    load_dotenv()


def main() -> int:
    parser = argparse.ArgumentParser(description="Test LLMCaller against a stored job")
    parser.add_argument(
        "--job-id",
        type=int,
        default=None,
        help="Job id in chatgpt_task.db (default: first row)",
    )
    parser.add_argument(
        "--provider",
        choices=("anthropic", "openai", "gemini"),
        default=None,
        help="LLM provider (default: LLM_PROVIDER env or anthropic)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print job only; do not call the API",
    )
    args = parser.parse_args()

    _load_env()

    print(f"Database: {DATABASE_URL}\n")

    db = SessionLocal()
    try:
        if args.job_id is not None:
            job = db.query(Job).filter(Job.id == args.job_id).first()
            if job is None:
                print(f"No job with id={args.job_id}", file=sys.stderr)
                return 1
        else:
            job = db.query(Job).order_by(Job.id).first()
            if job is None:
                print("No jobs in database. Create one via task_create MCP tool.", file=sys.stderr)
                return 1

        print(
            f"Job #{job.id}\n"
            f"  status:       {job.status}\n"
            f"  scheduled_at: {job.scheduled_at}\n"
            f"  description:  {job.description!r}\n"
        )

        if args.dry_run:
            return 0

        provider = args.provider or __import__("os").getenv("LLM_PROVIDER", "anthropic")
        print(f"Calling LLM ({provider})...\n")
        llm = LLMCaller(service_provider=provider)
        result = llm.call(job.description)

        print("--- LLM response ---")
        print(result)
        print("--- end ---")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
