"""
ControlFlow tasks for the Founder Flow automation system
"""
import controlflow as cf
import logging
from typing import Dict, List, Any, Optional
from .agent import (
    create_query_parser_agent,
    create_lead_collector_agent,
    create_email_agent,
    get_default_agent
)
from .models import JobQuery, Lead, Job

logger = logging.getLogger(__name__)

def parse_user_input_task(user_query: str, use_mocks: bool = False) -> JobQuery:
    """
    Create a task for parsing the user's job search query

    Args:
        user_query: Raw user query string
        use_mocks: Whether to use mock tools for testing

    Returns:
        JobQuery object with structured search parameters
    """
    logger.info(f"Creating task to parse user query: {user_query}")

    # Create a task to parse the user query
    task = cf.Task(
        objective="Parse the user's job search query into structured parameters",
        agents=[create_query_parser_agent(use_mocks=use_mocks)],
        context={"user_query": user_query},
        instructions="""
        Analyze the provided user_query and extract job search parameters.
        Return a JobQuery object with the following fields:
        - raw_query: The original user query
        - role: The job role/title extracted (REQUIRED)
        - location: The preferred location (default to 'remote' if not specified)
        - limit: Maximum number of job URLs to process (default to 10)

        Be careful to extract meaningful role information, as this will be used for search.
        """,
        result_type=JobQuery
    )

    # Run the task
    result = task.run()
    logger.info(f"Parsed query: {result}")
    return result

def generate_search_plan_task(job_query: JobQuery, use_mocks: bool = False) -> JobQuery:
    """
    Create a task for generating Google Dorks based on the structured query

    Args:
        job_query: JobQuery object with search parameters
        use_mocks: Whether to use mock tools for testing

    Returns:
        Updated JobQuery object with google_dorks field populated
    """
    print(f"Generating search plan for: {job_query}")

    # Create a task to generate the search plan
    task = cf.Task(
        objective="Generate Google Dorks for searching workatastartup.com",
        agents=[get_default_agent(use_mocks=use_mocks)],
        context={"query": job_query},
        instructions="""
        Use the generate_google_dorks tool to create search queries for the provided job query.
        Return the updated JobQuery object with the google_dorks field populated.
        """,
        result_type=JobQuery)

    # Run the task
    result = task.run()
    logger.info(f"Generated {len(result.google_dorks)} dorks")
    return result

def execute_search_task(job_query: JobQuery, use_mocks: bool = False) -> List[str]:
    """
    Create a task for executing the search and returning job URLs

    Args:
        job_query: JobQuery object with google_dorks
        use_mocks: Whether to use mock tools for testing

    Returns:
        List of job URLs from workatastartup.com
    """
    # Create a task to execute the search
    task = cf.Task(
        objective=f"Find job listings for {job_query.role} on workatastartup.com",
        agents=[get_default_agent(use_mocks=use_mocks)],
        context={"dorks": job_query.google_dorks, "limit": job_query.limit},
        instructions="""
        Use the execute_google_search tool to find job URLs.
        Pass the dorks from the context and the specified limit.
        Return a list of job URLs from workatastartup.com.
        """,
        result_type=List[str]
    )

    # Run the task
    result = task.run()
    logger.info(f"Found {len(result)} job URLs")
    return result

def collect_lead_task(job_url: str, use_mocks: bool = False) -> Lead:
    """
    Create a task for collecting lead information from a job URL

    Args:
        job_url: URL of the job listing
        use_mocks: Whether to use mock tools for testing

    Returns:
        Lead object with collected information
    """
    # Create a task to collect the lead
    task = cf.Task(
        objective=f"Collect lead information from job listing",
        agents=[create_lead_collector_agent(use_mocks=use_mocks)],
        context={"job_url": job_url},
        instructions="""
        Follow these steps to collect lead information:
        1. Use scrape_job_page (or mock_scrape_job_page if testing) to get job details
        2. Extract the company URL from the job page
        3. Use scrape_company_page (or mock_scrape_company_page if testing) to get company details
        4. Find a founder (preferably CEO) from the company page and get their LinkedIn URL
        5. Use get_email_from_linkedin (or mock_get_email_from_linkedin if testing) to find their email
        6. Return a Lead object with all collected information

        IMPORTANT: Skip the hiring manager search and ONLY focus on finding a founder from the company page.
        Look for CEO or other founder roles specifically, and prioritize these contacts.

        If any step fails, continue with the available information and note what's missing.
        """,
        result_type=Lead
    )

    # Run the task
    result = task.run()
    return result

def send_email_task(lead: Lead, template_name: str = "Default Template", use_mocks: bool = False) -> Dict[str, Any]:
    """
    Create a task for sending an email to a lead

    Args:
        lead: Lead object with contact information
        template_name: Name of the email template to use
        use_mocks: Whether to use mock tools for testing

    Returns:
        Dictionary with email sending result
    """
    if not lead.contact_email:
        logger.warning(f"Cannot send email to lead without email address: {lead.company_name}")
        return {"status": "Failed", "error": "No contact email available"}


    # Create a task to send the email
    task = cf.Task(
        objective=f"Send personalized email to lead",
        agents=[create_email_agent(use_mocks=use_mocks)],
        context={"lead": lead, "template_name": template_name},
        instructions="""
        Follow these steps to send an email to the lead:
        1. Get the email template using get_template_by_name
        2. Prepare a personalized email using prepare_email_for_lead
        3. Send the email using send_email_resend (or mock_send_email_resend if testing)
        4. Log the email using log_email_sent
        5. Return a dictionary with the sending result

        Ensure the email is properly personalized with the lead's information.
        """,
        result_type=Dict[str, Any]
    )

    # Run the task
    result = task.run()
    logger.info(f"Email sending result: {result}")
    return result

def process_job_results_task(job: Job, use_mocks: bool = False) -> Job:
    """
    Create a task for processing the overall job results

    Args:
        job: Job object with all details and leads
        use_mocks: Whether to use mock tools for testing

    Returns:
        Updated Job object with summary information
    """
    logger.info(f"Creating task to process results for job: {job.raw_query}")

    # Create a task to process the results
    task = cf.Task(
        objective=f"Process and summarize job search results",
        agents=[get_default_agent(use_mocks=use_mocks)],
        context={"job": job},
        instructions="""
        Analyze the job search results and provide a summary:
        1. Count the total number of leads found
        2. Count how many leads have contact emails
        3. Count how many emails were sent successfully
        4. Update the job status to "Complete"
        5. Return the updated Job object with summary information
        """,
        result_type=Job
    )

    # Run the task
    result = task.run()
    logger.info(f"Processed job results: {len(result.leads)} leads")
    return result