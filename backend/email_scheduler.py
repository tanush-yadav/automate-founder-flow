#!/usr/bin/env python
"""
Standalone script to process scheduled emails
Run with: python -m backend.email_scheduler
"""
import os
import sys
import logging
from dotenv import load_dotenv
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'email_scheduler.log'), mode='a')
    ]
)

logger = logging.getLogger("email_scheduler")

def ensure_log_dir():
    """Ensure the logs directory exists"""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

def process_emails_once():
    """Process all scheduled emails once"""
    # Import after environment variables are loaded
    from .tools.email import process_scheduled_emails

    try:
        logger.info("Processing scheduled emails")
        process_scheduled_emails()
        logger.info("Completed processing scheduled emails")
        return True
    except Exception as e:
        logger.error(f"Error processing scheduled emails: {str(e)}")
        return False

def run_scheduler(interval_minutes=5, run_once=False):
    """
    Run the email scheduler continuously

    Args:
        interval_minutes: Minutes to wait between processing cycles
        run_once: If True, runs once and exits; if False, runs continuously
    """
    if run_once:
        return process_emails_once()

    logger.info(f"Starting email scheduler with {interval_minutes} minute interval")

    try:
        while True:
            process_emails_once()
            logger.info(f"Sleeping for {interval_minutes} minutes")
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        logger.info("Email scheduler stopped by user")
    except Exception as e:
        logger.error(f"Email scheduler stopped due to error: {str(e)}")
        return False

    return True

def main():
    """Main entry point for the email scheduler"""
    # Create log directory if it doesn't exist
    ensure_log_dir()

    # Load environment variables
    load_dotenv()

    # Check required environment variables
    if not os.environ.get("GMAIL_USER") or not os.environ.get("GMAIL_APP_PASSWORD"):
        logger.error("Missing required environment variables: GMAIL_USER and GMAIL_APP_PASSWORD")
        sys.exit(1)

    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_ANON_KEY"):
        logger.error("Missing required environment variables: SUPABASE_URL and SUPABASE_ANON_KEY")
        sys.exit(1)

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Process scheduled emails')
    parser.add_argument('--interval', type=int, default=5, help='Interval in minutes between processing cycles')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    args = parser.parse_args()

    # Run the scheduler
    success = run_scheduler(interval_minutes=args.interval, run_once=args.once)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()