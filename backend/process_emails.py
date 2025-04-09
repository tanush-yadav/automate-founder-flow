"""
Process scheduled emails that are due to be sent
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('email_processor.log')
    ]
)

logger = logging.getLogger("email_processor")

def main():
    """Main entry point for the email processor"""
    # Load environment variables
    load_dotenv()

    # Check required environment variables
    if not os.environ.get("GMAIL_USER") or not os.environ.get("GMAIL_APP_PASSWORD"):
        logger.error("Missing required environment variables GMAIL_USER and GMAIL_APP_PASSWORD")
        sys.exit(1)

    if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_ANON_KEY"):
        logger.error("Missing required environment variables SUPABASE_URL and SUPABASE_ANON_KEY")
        sys.exit(1)

    # Import the processor (after environment variables are loaded)
    from .tools.email import process_scheduled_emails

    try:
        # Process all scheduled emails
        logger.info("Starting scheduled email processing")
        process_scheduled_emails()
        logger.info("Completed scheduled email processing")
    except Exception as e:
        logger.error(f"Error processing scheduled emails: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()