"""
Tool registration module for ControlFlow
"""
import logging
from typing import List

# Import all tools that will be registered
from .search import generate_google_dorks, execute_google_search, mock_execute_google_search
from .scraping import (
    scrape_job_page, scrape_company_page, find_contact_linkedin,
)
from .apollo import get_email_from_linkedin, mock_get_email_from_linkedin
from .email import (
    send_email_resend, render_email_template, prepare_email_for_lead,
    mock_send_email_resend
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
    send_email_resend,
    render_email_template,
    prepare_email_for_lead
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

# Mock tools for testing without making external requests
MOCK_TOOLS = [
    mock_execute_google_search,
    mock_get_email_from_linkedin,
    mock_send_email_resend
]

# All production tools
ALL_TOOLS = SEARCH_TOOLS + SCRAPING_TOOLS + CONTACT_TOOLS + EMAIL_TOOLS + DB_TOOLS

# All testing tools (with mocks replacing real network calls)
ALL_TESTING_TOOLS = [tool for tool in ALL_TOOLS if tool not in
                    [execute_google_search, scrape_job_page, scrape_company_page,
                     get_email_from_linkedin, send_email_resend]] + MOCK_TOOLS

def get_tools(use_mocks: bool = False) -> List:
    """
    Get a list of tools to use with ControlFlow

    Args:
        use_mocks: Whether to use mock tools instead of real ones

    Returns:
        List of tool functions
    """
    if use_mocks:
        logger.info("Using mock tools for testing")
        return ALL_TESTING_TOOLS
    else:
        logger.info("Using real tools")
        return ALL_TOOLS