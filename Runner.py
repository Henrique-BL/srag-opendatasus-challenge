"""
Main runner for SRAG OpenDataSUS Challenge
Handles report generation and pipeline execution based on command-line arguments.
"""

import sys
import argparse
import logging
import logging.config
import json
from datetime import datetime
from src.app.Graph import compiled_graph as report_graph
from src.pipelines.load import compiled_graph as load_graph

logging_config = json.load(open("src/settings/logging.json"))
logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments for the runner.
    Examples:
    python Runner.py --generate-report 2024-08-28
    python Runner.py --generate-report 2024-08-28  --load
    python Runner.py --load
    python Runner.py --generate-report today
    """
    parser = argparse.ArgumentParser(
        description="SRAG OpenDataSUS Challenge - Report Generator and Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        
    )
    # Report generation arguments
    parser.add_argument(
        "--generate-report", 
        type=str, 
        metavar="DATE",
        help="Generate report for specified date (YYYY-MM-DD format or 'today')"
    )
    
    parser.add_argument(
        "--sections",
        nargs="+",
        default=["p-aumento-dos-casos", "p-taxa-de-mortalidade", 
                 "p-taxa-de-ocupacao-uti", "p-taxa-de-vacinacao", 
                 "p-last-30-days-analysis", "p-last-12-months-analysis"],
        help="Report sections to include (default: all sections)"
    )
    
    # Pipeline arguments
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run setup pipeline (create database and tables)"
    )
    
    parser.add_argument(
        "--load",
        action="store_true",
        help="Run load pipeline (insert data into database)"
    )
    
    # Utility arguments
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()

def validate_date(date_str: str) -> str:
    """Validate and format the date string."""
    if date_str.lower() == "today":
        return datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Validate date format
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD or 'today'")

def run_load_pipeline():
    """Run the load pipeline to insert data into database."""
    logger.info("Starting load pipeline...")
    try:
        # Create initial state for load pipeline
        initial_state = {
            "data": None,  # Will be handled by the pipeline
            "stage": "start"
        }
        
        # Run the compiled load graph
        result = load_graph.invoke(initial_state)
        
        if result.get("stage") == "error":
            logger.error("Load pipeline failed")
            return False
            
        logger.info("Load pipeline completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error running load pipeline: {e}")
        return False

def generate_report(report_date: str, sections: list[str]):
    """Generate a report for the specified date and sections."""
    logger.info(f"Generating report for date: {report_date}")
    logger.info(f"Including sections: {sections}")
    
    try:
        # Create initial state for report generation
        initial_state = {
            "report_date": report_date,
            "report": {},
            "sections": sections,
            "data": {},
            "news": [],
            "stage": "start"
        }
        
        # Run the compiled report graph
        result = report_graph.invoke(initial_state)
        
        if result.get("stage") == "error":
            logger.error("Report generation failed")
            return False
            
        logger.info("Report generated successfully")
        logger.info("Report saved to: src/data/reports/relatorio_influenza.pdf")
        return True
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return False

def main():
    """Main entry point for the application."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        logger.info("Starting SRAG OpenDataSUS Challenge Runner")
        
        # Track success of operations
        success = True
        
        # Run load pipeline if requested
        if args.load:
            success &= run_load_pipeline()
        
        # Generate report if requested
        if args.generate_report:
            try:
                validated_date = validate_date(args.generate_report)
                success &= generate_report(validated_date, args.sections)
            except ValueError as e:
                logger.error(f"Date validation error: {e}")
                success = False
        
        # Check if no action was specified
        if not any([args.setup, args.load, args.generate_report]):
            logger.warning("No action specified. Use --help for usage information.")
            return 1
        
        # Return appropriate exit code
        if success:
            logger.info("All operations completed successfully")
            return 0
        else:
            logger.error("Some operations failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
