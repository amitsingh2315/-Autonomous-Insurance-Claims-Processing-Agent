"""
CLI entry point for the Insurance Claims Processing Agent.

Usage:
    python -m backend.main --pdf data/sample_fnol.pdf
    python -m backend.main --pdf data/sample_fnol.pdf --output result.json
    python -m backend.main --pdf data/sample_fnol.pdf --verbose
"""

import argparse
import json
import logging
import sys
import os
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add the project root to sys.path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.graph import run_pipeline, format_output


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO

    # Use a handler with UTF-8 encoding for Windows compatibility
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)

    logging.root.handlers = []
    logging.root.addHandler(handler)
    logging.root.setLevel(level)

    # Quiet down noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Autonomous Insurance Claims Processing Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m backend.main --pdf data/sample_fnol.pdf
  python -m backend.main --pdf data/sample_fnol.pdf --output result.json
  python -m backend.main --pdf data/sample_fnol.pdf --verbose
        """,
    )
    parser.add_argument(
        "--pdf",
        required=True,
        help="Path to the FNOL PDF document to process",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Path to save JSON output (default: print to stdout)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    # Validate input
    if not os.path.exists(args.pdf):
        logger.error(f"PDF file not found: {args.pdf}")
        sys.exit(1)

    # Banner
    print("\n" + "=" * 60)
    print("  Autonomous Insurance Claims Processing Agent")
    print("  Powered by LangGraph + Groq AI")
    print("=" * 60 + "\n")

    try:
        # Run the pipeline
        result = run_pipeline(args.pdf)

        # Format output
        output = format_output(result)

        # Pretty-print JSON
        output_json = json.dumps(output, indent=2, ensure_ascii=False)

        if args.output:
            # Save to file
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json)
            logger.info(f"Output saved to: {args.output}")
        
        # Always print to stdout
        print("\n" + "=" * 60)
        print("  PROCESSING RESULT")
        print("=" * 60)
        print(output_json)
        print("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
