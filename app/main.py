import argparse
import logging
import sys

from pydantic import ValidationError

from app.agent import run_research


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Research Agent")
    parser.add_argument("question", nargs="?", help="The research question")
    parser.add_argument("--out", help="Also write the JSON report to this file")
    args = parser.parse_args()

    question = args.question or input("Enter your research question: ").strip()
    if len(question) < 3:
        print("Error: Please enter a question with at least 3 characters.", file=sys.stderr)
        return 2

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    try:
        report = run_research(question)
    except (RuntimeError, ValueError, ValidationError) as exc:
        print(f"Research failed: {exc}", file=sys.stderr)
        return 1
    except Exception:
        logging.exception("Unexpected research failure.")
        print("Research failed unexpectedly. Check the logs.", file=sys.stderr)
        return 1

    output = report.model_dump_json(indent=2)
    print(output)  # stdout = JSON only, so it can be piped
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
