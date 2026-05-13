#!/usr/bin/env python
"""
Direct ETL Pipeline Orchestrator

This script provides a command-line interface to run ETL tasks directly,
without requiring Django or Celery infrastructure. Useful for local development
and testing.

Usage:
    python etl_orchestrator.py run-all              # Run complete pipeline
    python etl_orchestrator.py extract              # Run extraction only
    python etl_orchestrator.py transform            # Run transformation only
    python etl_orchestrator.py load                 # Run load only
    python etl_orchestrator.py --help               # Show help
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List
import traceback

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent
ETL_DIR = PROJECT_ROOT / "etl"
if str(ETL_DIR) not in sys.path:
    sys.path.insert(0, str(ETL_DIR))

# Setup logging
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'etl_orchestrator.log'),
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


class ETLOrchestrator:
    """Orchestrates ETL pipeline execution."""

    def __init__(self):
        """Initialize orchestrator."""
        self.execution_results: Dict[str, Dict] = {}
        self.start_time = None
        self.end_time = None

    def run_extraction(self) -> bool:
        """
        Run extraction phase.

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("PHASE 1: EXTRACTION")
        logger.info("=" * 60)

        try:
            from extract_from_excel import main as extract_main

            logger.info("Starting data extraction from Excel files...")
            extract_main()
            logger.info("✓ Extraction completed successfully")

            self.execution_results['extraction'] = {
                'status': 'SUCCESS',
                'message': 'Data extraction completed'
            }
            return True

        except Exception as e:
            logger.error(f"✗ Extraction failed: {e}")
            logger.error(traceback.format_exc())

            self.execution_results['extraction'] = {
                'status': 'FAILED',
                'message': str(e)
            }
            return False

    def run_transformation(self) -> bool:
        """
        Run transformation phase.

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2: TRANSFORMATION")
        logger.info("=" * 60)

        try:
            from clean_and_transform import main as transform_main

            logger.info("Starting data cleaning and transformation...")
            transform_main()
            logger.info("✓ Transformation completed successfully")

            self.execution_results['transformation'] = {
                'status': 'SUCCESS',
                'message': 'Data transformation completed'
            }
            return True

        except Exception as e:
            logger.error(f"✗ Transformation failed: {e}")
            logger.error(traceback.format_exc())

            self.execution_results['transformation'] = {
                'status': 'FAILED',
                'message': str(e)
            }
            return False

    def run_load(self) -> bool:
        """
        Run load phase.

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 3: LOAD")
        logger.info("=" * 60)

        try:
            from load_to_warehouse import main as load_main

            logger.info("Starting data load to warehouse...")
            load_main()
            logger.info("✓ Load completed successfully")

            self.execution_results['load'] = {
                'status': 'SUCCESS',
                'message': 'Data load completed'
            }
            return True

        except Exception as e:
            logger.error(f"✗ Load failed: {e}")
            logger.error(traceback.format_exc())

            self.execution_results['load'] = {
                'status': 'FAILED',
                'message': str(e)
            }
            return False

    def run_pipeline(
        self,
        phases: List[str] = None,
        stop_on_failure: bool = True
    ) -> bool:
        """
        Run ETL pipeline phases.

        Args:
            phases: List of phases to run ('extract', 'transform', 'load')
            stop_on_failure: Stop execution on first failure

        Returns:
            bool: True if all phases successful, False otherwise
        """
        import time

        if phases is None:
            phases = ['extract', 'transform', 'load']

        self.start_time = time.time()
        all_successful = True

        try:
            logger.info("\n" + "🚀 " * 20)
            logger.info("STARTING ETL PIPELINE")
            logger.info(f"Phases: {', '.join(phases)}")
            logger.info("🚀 " * 20)

            if 'extract' in phases:
                if not self.run_extraction():
                    all_successful = False
                    if stop_on_failure:
                        logger.warning("Stopping pipeline due to extraction failure")
                        return False

            if 'transform' in phases:
                if not self.run_transformation():
                    all_successful = False
                    if stop_on_failure:
                        logger.warning("Stopping pipeline due to transformation failure")
                        return False

            if 'load' in phases:
                if not self.run_load():
                    all_successful = False
                    if stop_on_failure:
                        logger.warning("Stopping pipeline due to load failure")
                        return False

            self.end_time = time.time()
            self._print_summary()

            return all_successful

        except KeyboardInterrupt:
            logger.warning("\n⚠️  Pipeline interrupted by user")
            return False
        except Exception as e:
            logger.error(f"\n✗ Unexpected error: {e}")
            logger.error(traceback.format_exc())
            return False

    def _print_summary(self):
        """Print execution summary."""
        duration = self.end_time - self.start_time if self.end_time else 0

        logger.info("\n" + "=" * 60)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 60)

        for phase, result in self.execution_results.items():
            status_icon = "✓" if result['status'] == 'SUCCESS' else "✗"
            logger.info(f"{status_icon} {phase.upper()}: {result['status']}")
            if result['message']:
                logger.info(f"  └─ {result['message']}")

        logger.info(f"\nTotal Duration: {duration:.2f} seconds")

        all_successful = all(
            r['status'] == 'SUCCESS'
            for r in self.execution_results.values()
        )

        if all_successful:
            logger.info("\n🎉 ETL Pipeline completed successfully!")
        else:
            logger.error("\n⚠️  ETL Pipeline completed with errors")

        logger.info("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='ETL Pipeline Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python etl_orchestrator.py run-all        Run complete pipeline
  python etl_orchestrator.py extract        Run extraction only
  python etl_orchestrator.py transform      Run transformation only
  python etl_orchestrator.py load           Run load only
  python etl_orchestrator.py --help         Show this help
        """
    )

    parser.add_argument(
        'command',
        nargs='?',
        default='run-all',
        choices=['run-all', 'extract', 'transform', 'load'],
        help='ETL command to execute'
    )

    parser.add_argument(
        '--stop-on-failure',
        action='store_true',
        default=True,
        help='Stop pipeline on first failure (default: True)'
    )

    parser.add_argument(
        '--continue-on-failure',
        action='store_true',
        help='Continue pipeline even if a phase fails'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    # Map commands to phases
    command_to_phases = {
        'run-all': ['extract', 'transform', 'load'],
        'extract': ['extract'],
        'transform': ['transform'],
        'load': ['load'],
    }

    phases = command_to_phases.get(args.command, ['extract', 'transform', 'load'])
    stop_on_failure = not args.continue_on_failure

    # Run orchestrator
    orchestrator = ETLOrchestrator()
    success = orchestrator.run_pipeline(phases=phases, stop_on_failure=stop_on_failure)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
