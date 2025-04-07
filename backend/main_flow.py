"""
Main ControlFlow orchestration for the Founder Flow automation system
"""
import controlflow as cf
import logging
from typing import Dict, List, Any, Optional
import uuid
from .models import Job, Lead
from .tasks import (
    parse_user_input_task,
    generate_search_plan_task,
    execute_search_task,
    collect_lead_task,
    send_email_task,
    process_job_results_task
)
from .tools.supabase import (
    log_job_start,
    update_job_status,
    save_lead,
    update_lead_status
)

logger = logging.getLogger(__name__)

class JobRunResult:
    """Class to store and track the results of a job run"""
    def __init__(self, job_id: str, job: Job = None):
        self.job_id = job_id
        self.job = job
        self.status = "Pending"
        self.leads = []
        self.job_urls = []
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary"""
        return {
            "job_id": self.job_id,
            "status": self.status,
            "job": self.job.dict() if self.job else None,
            "leads_count": len(self.leads),
            "job_urls_count": len(self.job_urls),
            "error": self.error
        }

def run_founder_flow(user_query: str, use_mocks: bool = False) -> JobRunResult:
    """
    Run the main Founder Flow automation process

    Args:
        user_query: Raw user query string
        use_mocks: Whether to use mock tools for testing

    Returns:
        JobRunResult object with results and status
    """
    # Create a flow to manage the entire process
    with cf.Flow(name="Founder Flow") as flow:
        try:
            # Create a job record to track the run
            job = Job(raw_query=user_query)
            job_id = log_job_start(job)
            result = JobRunResult(job_id=job_id, job=job)

            # Update job status
            update_job_status(job_id, "Parsing")
            result.status = "Parsing"

            # STEP 1: Parse the user query
            logger.info("STEP 1: Parsing user query")
            job_query = parse_user_input_task(user_query, use_mocks=use_mocks)

            # Update job with parsed info
            job.parsed_role = job_query.role
            job.parsed_location = job_query.location
            update_job_status(job_id, "GeneratingPlan")
            result.status = "GeneratingPlan"

            # STEP 2: Generate search plan
            logger.info("STEP 2: Generating search plan")
            job_query = generate_search_plan_task(job_query, use_mocks=use_mocks)

            # Update job with dorks
            job.google_dorks = job_query.google_dorks
            update_job_status(job_id, "Searching")
            result.status = "Searching"

            # STEP 3: Execute search
            logger.info("STEP 3: Executing search")
            job_urls = execute_search_task(job_query, use_mocks=use_mocks)
            result.job_urls = job_urls

            if not job_urls:
                logger.warning("No job URLs found")
                update_job_status(job_id, "NoResults", "No job URLs found")
                result.status = "NoResults"
                result.error = "No job URLs found"
                return result

            update_job_status(job_id, "CollectingLeads")
            result.status = "CollectingLeads"

            # STEP 4: Collect leads (process each job URL)
            logger.info(f"STEP 4: Collecting leads from {len(job_urls)} job URLs")
            leads = []

            # First process company URLs as they're more likely to have founder information
            company_urls = [url for url in job_urls if 'workatastartup.com/companies/' in url]
            job_listing_urls = [url for url in job_urls if 'workatastartup.com/jobs/' in url]

            # Process company URLs first, then job listing URLs
            prioritized_urls = company_urls + job_listing_urls
            logger.info(f"Processing {len(company_urls)} company URLs and {len(job_listing_urls)} job listing URLs")

            for url in prioritized_urls:
                try:
                    # Process each URL
                    lead = collect_lead_task(url, use_mocks=use_mocks)

                    # Save lead to database
                    lead_id = save_lead(lead, job_id)

                    # Check if we found an email
                    if lead.contact_email:
                        update_lead_status(lead_id, "ReadyToSend", lead.contact_email)
                        lead.status = "ReadyToSend"
                    else:
                        update_lead_status(lead_id, "EmailNotFound",
                                          error_message="No email found for contact")
                        lead.status = "EmailNotFound"

                    leads.append(lead)

                    logger.info(f"Processed lead for {lead.company_name}: {lead.contact_name} ({lead.contact_email})")

                except Exception as e:
                    logger.error(f"Error processing URL {url}: {str(e)}")
                    # Continue with next URL

            # Update job with leads
            job.leads = leads
            result.leads = leads

            # Check if we found any leads
            if not leads:
                logger.warning("No leads collected")
                update_job_status(job_id, "NoLeads", "No leads could be collected")
                result.status = "NoLeads"
                result.error = "No leads could be collected"
                return result

            # Update job status
            update_job_status(job_id, "Complete")
            result.status = "Complete"

            # Process and summarize results
            job = process_job_results_task(job, use_mocks=use_mocks)
            result.job = job

            return result

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Error in founder flow: {str(e)}\nTraceback:\n{tb}")
            if 'job_id' in locals():
                update_job_status(job_id, "Failed", str(e))
            result = JobRunResult(job_id=job_id if 'job_id' in locals() else None)
            result.status = "Failed"
            result.error = f"{str(e)}\n\nTraceback:\n{tb}"
            return result

def send_emails_for_job(job_id: str, template_name: str = "Default Template", use_mocks: bool = False) -> Dict[str, Any]:
    """
    Send emails for leads collected in a job

    Args:
        job_id: ID of the job
        template_name: Name of the email template to use
        use_mocks: Whether to use mock tools for testing

    Returns:
        Dictionary with email sending results
    """
    # Create a flow to manage the email sending process
    with cf.Flow(name="Email Sending Flow") as flow:
        try:
            # Update job status
            update_job_status(job_id, "SendingEmails")

            # Get leads that are ready to send
            from .tools.supabase import get_leads_to_email
            leads_data = get_leads_to_email(job_id)

            if not leads_data:
                logger.warning(f"No leads ready for emailing found for job {job_id}")
                update_job_status(job_id, "NoEmailsToSend", "No leads ready for emailing")
                return {
                    "status": "NoEmailsToSend",
                    "job_id": job_id,
                    "emails_sent": 0
                }

            # Send emails to each lead
            emails_sent = 0

            for lead_data in leads_data:
                try:
                    # Convert lead data to Lead object
                    lead = Lead(**lead_data)

                    # Send email
                    result = send_email_task(lead, template_name, use_mocks=use_mocks)

                    if result.get("status") == "Sent" or "id" in result:
                        emails_sent += 1
                        update_lead_status(lead_data["id"], "EmailSent")
                    else:
                        update_lead_status(lead_data["id"], "EmailFailed",
                                          error_message=result.get("error", "Unknown error"))

                except Exception as e:
                    import traceback
                    tb = traceback.format_exc()
                    logger.error(f"Error sending email for lead {lead_data.get('id')}: {str(e)}\nTraceback:\n{tb}")
                    update_lead_status(lead_data["id"], "EmailFailed", error_message=f"{str(e)}\n\nTraceback:\n{tb}")

            # Update job status
            update_job_status(job_id, "EmailsComplete")

            return {
                "status": "Complete",
                "job_id": job_id,
                "emails_sent": emails_sent,
                "total_leads": len(leads_data)
            }

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Error in email sending flow: {str(e)}\nTraceback:\n{tb}")
            update_job_status(job_id, "EmailFailed", str(e))
            return {
                "status": "Failed",
                "job_id": job_id,
                "error": f"{str(e)}\n\nTraceback:\n{tb}",
                "emails_sent": 0
            }