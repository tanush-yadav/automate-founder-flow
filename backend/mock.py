"""
Mock testing utilities for Founder Flow components

This script provides a simple way to test individual components of the
Founder Flow automation without relying on the Streamlit interface.

Usage:
    python mock.py {component} [options]

Components:
    parse_query - Test query parsing
    generate_dorks - Test generating Google dorks
    search - Test search execution
    collect_lead - Test lead collection
    send_email - Test email sending
    full - Run the full workflow
    leads_only - Run real testing workflow up to lead collection, without sending emails

Example:
    python mock.py parse_query "find backend engineers in San Francisco"
    python mock.py full "find senior iOS developers in New York"
"""

import sys
import logging
import json
from typing import Dict, Any, List, Optional
import os
import traceback

# Load environment variables first, before any other imports
from dotenv import load_dotenv
load_dotenv()
print("Environment variables loaded from .env file")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
# Set loggers to DEBUG level for testing
for module in ["backend", "controlflow"]:
    logging.getLogger(module).setLevel(logging.DEBUG)

# Now import components after env variables are loaded
from .models import JobQuery, Lead
from .tasks import (
    parse_user_input_task,
    generate_search_plan_task,
    execute_search_task,
    collect_lead_task,
    send_email_task
)

def test_parse_query(query: str) -> JobQuery:
    """Test parsing a user query"""
    print(f"\n=== Testing query parsing for: '{query}' ===\n")

    job_query = parse_user_input_task(query, use_mocks=True)
    print("\nParsed Query:")
    print(f"  Role: {job_query.role}")
    print(f"  Location: {job_query.location}")
    print(f"  Raw Query: {job_query.raw_query}")
    print(f"  Limit: {job_query.limit}")

    return job_query

def test_generate_dorks(job_query: JobQuery) -> JobQuery:
    """Test generating Google dorks for a job query"""
    print(f"\n=== Testing dork generation for: '{job_query.role}' ===\n")

    job_query = generate_search_plan_task(job_query, use_mocks=True)
    print("\nGenerated Google Dorks:")
    for i, dork in enumerate(job_query.google_dorks, 1):
        print(f"  {i}. {dork}")

    return job_query

def test_search(job_query: JobQuery) -> List[str]:
    """Test executing a search with the generated dorks"""
    print(f"\n=== Testing search execution for: '{job_query.role}' ===\n")

    urls = execute_search_task(job_query, use_mocks=True)
    print(f"\nFound {len(urls)} job URLs:")
    for i, url in enumerate(urls, 1):
        print(f"  {i}. {url}")

    return urls

def test_collect_lead(url: str) -> Lead:
    """Test collecting lead information from a job URL"""
    print(f"\n=== Testing lead collection for URL: '{url}' ===\n")

    lead = collect_lead_task(url, use_mocks=True)
    print("\nCollected Lead Information:")
    print(f"  Company: {lead.company_name}")
    print(f"  Role: {lead.role_title}")
    print(f"  Contact: {lead.contact_name} ({lead.contact_title})")
    print(f"  Email: {lead.contact_email}")
    print(f"  LinkedIn: {lead.contact_linkedin_url}")

    return lead

def test_send_email(lead: Lead) -> Dict[str, Any]:
    """Test sending an email to a lead"""
    if not lead.contact_email:
        print("\n!!! Cannot send email: No contact email available !!!\n")
        return {"status": "error", "message": "No contact email available"}

    print(f"\n=== Testing email sending to: '{lead.contact_name}' at '{lead.company_name}' ===\n")

    try:
        # Try to ensure the default template exists first
        from .tools.supabase import ensure_default_template
        template_name = ensure_default_template()
        print(f"Using template: {template_name}")

        result = send_email_task(lead, use_mocks=True)
        print("\nEmail Sending Result:")
        print(json.dumps(result, indent=2))

        return result
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"\nError sending email: {str(e)}")
        print(f"\nTraceback:\n{error_trace}")
        logger.error(f"Error in test_send_email: {str(e)}\nTraceback:\n{error_trace}")
        return {"status": "error", "message": str(e)}

def test_full_workflow(query: str) -> Dict[str, Any]:
    """Test the full Founder Flow workflow using real functions"""
    print(f"\n=== Running full workflow with real functions for query: '{query}' ===\n")

    # 1. Parse the query (real)
    job_query = parse_user_input_task(query, use_mocks=False)
    print("\nParsed Query:")
    print(f"  Role: {job_query.role}")
    print(f"  Location: {job_query.location}")
    print(f"  Raw Query: {job_query.raw_query}")
    print(f"  Limit: {job_query.limit}")

    # 2. Generate search plan (real)
    job_query = generate_search_plan_task(job_query, use_mocks=False)
    print("\nGenerated Google Dorks:")
    for i, dork in enumerate(job_query.google_dorks, 1):
        print(f"  {i}. {dork}")

    # 3. Execute search (real)
    job_urls = execute_search_task(job_query, use_mocks=False)
    print(f"\nFound {len(job_urls)} job URLs:")
    for i, url in enumerate(job_urls, 1):
        print(f"  {i}. {url}")

    # 4. Collect leads (limit to first for testing)
    leads = []
    for url in job_urls[:1]:
        try:
            lead = collect_lead_task(url, use_mocks=False)
            leads.append(lead)
            print("\nCollected Lead Information:")
            print(f"  Company: {lead.company_name}")
            print(f"  Role: {lead.role_title}")
            print(f"  Contact: {lead.contact_name} ({lead.contact_title})")
            print(f"  Email: {lead.contact_email}")
            print(f"  LinkedIn: {lead.contact_linkedin_url}")

            # 5. Send email to the lead
            if lead.contact_email:
                result = send_email_task(lead, use_mocks=False)
                print("\nEmail Sending Result:")
                print(json.dumps(result, indent=2))

        except Exception as e:
            logger.error(f"Error processing lead from {url}: {str(e)}")

    # 6. Summarize results
    print("\n=== Workflow Summary ===\n")
    print(f"  Query: '{query}'")
    print(f"  Google Dorks Generated: {len(job_query.google_dorks)}")
    print(f"  Job URLs Found: {len(job_urls)}")
    print(f"  Leads Collected: {len(leads)}")
    print(f"  Leads with Email: {sum(1 for lead in leads if lead.contact_email)}")

    return {
        "job_query": job_query,
        "job_urls_count": len(job_urls),
        "leads_count": len(leads),
        "leads_with_email": sum(1 for lead in leads if lead.contact_email)
    }

def test_leads_only_workflow(query: str, limit: int = 5) -> List[Lead]:
    """Run real testing workflow up to lead collection, without sending emails"""
    print(f"\n=== Running real workflow (no email) for query: '{query}' ===\n")

    # 1. Parse the query (real)
    job_query = parse_user_input_task(query, use_mocks=False)
    print("\nParsed Query:")
    print(f"  Role: {job_query.role}")
    print(f"  Location: {job_query.location}")
    print(f"  Raw Query: {job_query.raw_query}")
    print(f"  Limit: {job_query.limit}")

    # 2. Generate search plan (real)
    job_query = generate_search_plan_task(job_query, use_mocks=False)
    print("\nGenerated Google Dorks:")
    for i, dork in enumerate(job_query.google_dorks, 1):
        print(f"  {i}. {dork}")

    # 3. Execute search (real)
    job_urls = execute_search_task(job_query, use_mocks=False)
    print(f"\nFound {len(job_urls)} job URLs:")
    for i, url in enumerate(job_urls, 1):
        print(f"  {i}. {url}")

    # 4. Collect leads (real, but limit for testing)
    leads = []
    for url in job_urls:
        try:
            lead = collect_lead_task(url, use_mocks=False)
            leads.append(lead)
            print("\nCollected Lead Information:")
            print(f"  Company: {lead.company_name}")
            print(f"  Role: {lead.role_title}")
            print(f"  Contact: {lead.contact_name} ({lead.contact_title})")
            print(f"  Email: {lead.contact_email}")
            print(f"  LinkedIn: {lead.contact_linkedin_url}")

        except Exception as e:
            logger.error(f"Error processing lead from {url}: {str(e)}")

    # 5. Summarize results
    print("\n=== Workflow Summary (No Emails Sent) ===\n")
    print(f"  Query: '{query}'")
    print(f"  Google Dorks Generated: {len(job_query.google_dorks)}")
    print(f"  Job URLs Found: {len(job_urls)}")
    print(f"  Leads Collected: {len(leads)}")
    print(f"  Leads with Email: {sum(1 for lead in leads if lead.contact_email)}")

    return leads


def show_help():
    """Display help information"""
    print(__doc__)


def main():
    """Main entry point"""
    # Print current environment variables for debugging
    print(f"\nEnvironment Variables:")
    print(f"  SUPABASE_URL: {'Set' if os.environ.get('SUPABASE_URL') else 'Not Set'}")
    print(f"  SUPABASE_ANON_KEY: {'Set' if os.environ.get('SUPABASE_ANON_KEY') else 'Not Set'}")
    print(f"  APOLLO_API_KEY: {'Set' if os.environ.get('APOLLO_API_KEY') else 'Not Set'}")
    print(f"  OPENAI_API_KEY: {'Set' if os.environ.get('OPENAI_API_KEY') else 'Not Set'}")
    print(f"  GMAIL_USER: {'Set' if os.environ.get('GMAIL_USER') else 'Not Set'}")
    print("")

    if len(sys.argv) < 2:
        show_help()
        return

    component = sys.argv[1].lower()

    if component == "help" or component == "--help" or component == "-h":
        show_help()
        return

    if len(sys.argv) < 3 and component != "help":
        print("Error: Missing required arguments")
        show_help()
        return

    # Handle different component testing
    try:
        if component == "parse_query":
            test_parse_query(sys.argv[2])

        elif component == "generate_dorks":
            query = sys.argv[2]
            job_query = test_parse_query(query)
            test_generate_dorks(job_query)

        elif component == "search":
            query = sys.argv[2]
            job_query = test_parse_query(query)
            job_query = test_generate_dorks(job_query)
            test_search(job_query)

        elif component == "collect_lead":
            url = sys.argv[2]
            test_collect_lead(url)

        elif component == "send_email":
            url = sys.argv[2]
            lead = test_collect_lead(url)
            test_send_email(lead)

        elif component == "full":
            query = sys.argv[2]
            test_full_workflow(query)

        elif component == "leads_only":
            query = sys.argv[2]
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
            test_leads_only_workflow(query, limit)

        else:
            print(f"Unknown component: {component}")
            show_help()
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"\nError executing {component}: {str(e)}")
        print(f"\nTraceback:\n{error_trace}")
        logger.error(f"Error in main execution: {str(e)}\nTraceback:\n{error_trace}")

if __name__ == "__main__":
    main()