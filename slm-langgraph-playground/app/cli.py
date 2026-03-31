from __future__ import annotations

import argparse
import json

from .config import load_settings
from .logging_config import configure_logging
from .runner import run_prompt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a local SLM through a small LangGraph pipeline.")
    parser.add_argument("--prompt", required=True, help="Text prompt to send to the graph.")
    parser.add_argument("--model", help="Optional model override from AVAILABLE_MODELS.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = load_settings()
    configure_logging(settings.log_level)

    try:
        result = run_prompt(args.prompt, model=args.model, settings=settings)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
