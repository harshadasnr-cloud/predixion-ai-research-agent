
import argparse
import json
import logging
import sys

from pydantic import ValidationError

from app.agent import run_research


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Predixion AI Research Agent"
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="The research question to investigate",
    )
    args = parser.parse_args()

    question = args.question
    if not question:
        question = input("Enter your research question: ").strip()

    if len(question) < 3:
        print("Error: Please enter a question with at least 3 characters.")
        return 2

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        report = run_research(question)
        print("\n" + report.model_dump_json(indent=2))
        return 0
    except (RuntimeError, ValueError, ValidationError) as exc:
        print(f"\nResearch failed: {exc}", file=sys.stderr)
        return 1
    except Exception:
        logging.exception("Unexpected research failure.")
        print(
            "Research failed unexpectedly. Check the logs and configuration.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
