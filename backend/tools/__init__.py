"""
Tool registration module for ControlFlow
"""
import logging
from typing import List

# Import all tools that will be registered
from .search import generate_google_dorks, execute_google_search
from .scraping import (
    scrape_job_page, scrape_company_page, find_contact_linkedin,
)
from .apollo import get_email_from_linkedin, mock_get_email_from_linkedin
from .email import (
    send_email_yagmail, render_email_template, prepare_email_for_lead,
)
from .supabase import (
    log_job_start, update_job_status, save_lead, update_lead_status,
    log_email_sent, get_leads_to_email, get_templates, get_template_by_name,
    ensure_default_template
)

logger = logging.getLogger(__name__)

# All tools available for use
SEARCH_TOOLS = [
    generate_google_dorks,
    execute_google_search
]

SCRAPING_TOOLS = [
    scrape_job_page,
    scrape_company_page,
    find_contact_linkedin
]

CONTACT_TOOLS = [
    get_email_from_linkedin
]

EMAIL_TOOLS = [
    render_email_template,
    prepare_email_for_lead,
    send_email_yagmail
]

DB_TOOLS = [
    log_job_start,
    update_job_status,
    save_lead,
    update_lead_status,
    log_email_sent,
    get_leads_to_email,
    get_templates,
    get_template_by_name,
    ensure_default_template
]

# All production tools
ALL_TOOLS = SEARCH_TOOLS + SCRAPING_TOOLS + CONTACT_TOOLS + EMAIL_TOOLS + DB_TOOLS


def get_tools(use_mocks: bool = False) -> List:
    """
    Get a list of tools to use with ControlFlow

    Args:
        use_mocks: Whether to use mock tools instead of real ones

    Returns:
        List of tool functions
    """
    try:
        return ALL_TOOLS
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error loading tools: {str(e)}\nTraceback:\n{error_trace}")
        raise