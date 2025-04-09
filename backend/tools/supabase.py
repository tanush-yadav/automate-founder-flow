"""
Supabase integration tools for database operations
"""
import os
import logging
from typing import Optional, List, Dict, Any
import supabase
from supabase import create_client, Client
from ..models import Job, Lead, EmailTemplate, EmailLog

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """
    Get a Supabase client instance

    Returns:
        Supabase Client instance

    Raises:
        ValueError: If Supabase URL or API key are not configured
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        error_msg = "Supabase URL and key must be provided as environment variables"
        logger.error(error_msg)
        raise ValueError(error_msg)

    return create_client(supabase_url, supabase_key)

def log_job_start(job: Job) -> str:
    """
    Log a new job start to the database

    Args:
        job: Job object with query details

    Returns:
        ID of the created job record
    """
    try:
        client = get_supabase_client()

        # Convert Job object to dict for insertion
        job_data = job.dict(exclude={"id", "leads"})

        # Insert the job record
        logger.info(f"Logging new job: {job.raw_query}")
        response = client.table("jobs").insert(job_data).execute()

        # Extract the job ID from the response
        if response.data and len(response.data) > 0:
            job_id = response.data[0].get("id")
            logger.info(f"Job logged with ID: {job_id}")
            return job_id
        else:
            logger.error("Failed to get job ID from Supabase response")
            return None

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error logging job start: {str(e)}\nTraceback:\n{tb}")
        return None

def update_job_status(job_id: str, status: str, error_message: Optional[str] = None) -> bool:
    """
    Update the status of a job

    Args:
        job_id: ID of the job to update
        status: New status value
        error_message: Optional error message

    Returns:
        True if update succeeded, False otherwise
    """
    try:
        client = get_supabase_client()

        # Prepare update data
        update_data = {"status": status}
        if error_message:
            update_data["error_message"] = error_message

        # Update the job record
        logger.info(f"Updating job {job_id} status to: {status}")
        response = client.table("jobs").update(update_data).eq("id", job_id).execute()

        return True

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error updating job status: {str(e)}\nTraceback:\n{tb}")
        return False

def update_job_search_index(job_id: str, last_processed_index: int) -> bool:
    """
    Update the last processed search index for a job

    Args:
        job_id: ID of the job to update
        last_processed_index: Index of the last processed search result

    Returns:
        True if update succeeded, False otherwise
    """
    try:
        client = get_supabase_client()

        # Prepare update data
        update_data = {"last_processed_index": last_processed_index}

        # Update the job record
        logger.info(f"Updating job {job_id} last_processed_index to: {last_processed_index}")
        response = client.table("jobs").update(update_data).eq("id", job_id).execute()

        return True

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error updating job search index: {str(e)}\nTraceback:\n{tb}")
        return False

def get_job_last_index(job_id: str) -> int:
    """
    Get the last processed search index for a job

    Args:
        job_id: ID of the job

    Returns:
        Last processed index or 0 if not found
    """
    try:
        client = get_supabase_client()

        # Query for the job
        logger.info(f"Fetching last_processed_index for job: {job_id}")
        response = client.table("jobs").select("last_processed_index").eq("id", job_id).execute()

        # Extract the last processed index
        if response.data and len(response.data) > 0:
            last_index = response.data[0].get("last_processed_index", 0)
            logger.info(f"Retrieved last_processed_index: {last_index}")
            return last_index
        else:
            logger.warning(f"No job found with ID: {job_id}")
            return 0

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error getting job last index: {str(e)}\nTraceback:\n{tb}")
        return 0

def get_similar_job(role: str, location: str) -> Optional[Dict[str, Any]]:
    """
    Get a similar job with the same role and location

    Args:
        role: Job role
        location: Job location

    Returns:
        Job record if found, None otherwise
    """
    try:
        client = get_supabase_client()

        # Query for similar jobs with the same role and location
        logger.info(f"Searching for similar jobs with role: {role}, location: {location}")
        response = client.table("jobs").select("*") \
            .eq("parsed_role", role) \
            .eq("parsed_location", location) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        # Extract the job from the response
        if response.data and len(response.data) > 0:
            job = response.data[0]
            logger.info(f"Found similar job with ID: {job.get('id')}")
            return job
        else:
            logger.info(f"No similar job found for role: {role}, location: {location}")
            return None

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error getting similar job: {str(e)}\nTraceback:\n{tb}")
        return None

def check_lead_exists(company_name: Optional[str] = None, company_url: Optional[str] = None) -> bool:
    """
    Check if a lead with the given company name or URL already exists

    Args:
        company_name: Company name to check
        company_url: Company URL to check

    Returns:
        True if a lead exists, False otherwise
    """
    try:
        client = get_supabase_client()
        query = client.table("leads").select("id")

        # Add filters based on provided parameters
        if company_name:
            query = query.eq("company_name", company_name)
        elif company_url:
            query = query.eq("company_url", company_url)
        else:
            logger.warning("No company name or URL provided for lead existence check")
            return False

        # Execute the query
        response = query.execute()

        # Check if any leads were found
        exists = response.data and len(response.data) > 0
        if exists:
            logger.info(f"Lead already exists for company: {company_name or company_url}")
        else:
            logger.info(f"No existing lead found for company: {company_name or company_url}")

        return exists

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error checking if lead exists: {str(e)}\nTraceback:\n{tb}")
        return False

def save_lead(lead: Lead, job_id: str) -> Optional[str]:
    """
    Save a lead to the database

    Args:
        lead: Lead object with details
        job_id: ID of the parent job

    Returns:
        ID of the created lead record, or None if failed
    """
    try:
        # Check if lead already exists
        if lead.company_name or lead.company_url:
            if check_lead_exists(lead.company_name, lead.company_url):
                logger.info(f"Skipping duplicate lead for company: {lead.company_name}")
                return None

        client = get_supabase_client()

        # Convert Lead object to dict for insertion
        lead_data = lead.dict(exclude={"id"})
        # Add job_id
        lead_data["job_id"] = job_id

        # Insert the lead record
        logger.info(f"Saving lead for job {job_id}: {lead.company_name}")
        response = client.table("leads").insert(lead_data).execute()

        # Extract the lead ID from the response
        if response.data and len(response.data) > 0:
            lead_id = response.data[0].get("id")
            logger.info(f"Lead saved with ID: {lead_id}")
            return lead_id
        else:
            logger.error("Failed to get lead ID from Supabase response")
            return None

    except Exception as e:
        logger.error(f"Error saving lead: {str(e)}")
        return None

def update_lead_status(lead_id: str, status: str, email: Optional[str] = None, error_message: Optional[str] = None) -> bool:
    """
    Update the status of a lead

    Args:
        lead_id: ID of the lead to update
        status: New status value
        email: Optional email address found
        error_message: Optional error message

    Returns:
        True if update succeeded, False otherwise
    """
    try:
        client = get_supabase_client()

        # Prepare update data
        update_data = {"status": status}
        if email:
            update_data["contact_email"] = email
        if error_message:
            update_data["error_message"] = error_message

        # Update the lead record
        logger.info(f"Updating lead {lead_id} status to: {status}")
        response = client.table("leads").update(update_data).eq("id", lead_id).execute()

        return True

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error updating lead status: {str(e)}\nTraceback:\n{tb}")
        return False

def log_email_sent(lead_id: str, to_email: str, subject: str, template_name: str,
                tracking_id: Optional[str] = None, status: str = "Sent",
                body: Optional[str] = None, scheduled_at: Optional[str] = None) -> Optional[str]:
    """
    Log an email that was sent

    Args:
        lead_id: ID of the lead the email was sent to
        to_email: Recipient email address
        subject: Email subject
        template_name: Name of the template used
        tracking_id: Optional tracking ID for the email
        status: Email status (default: "Sent")
        body: Optional email body text
        scheduled_at: Optional scheduled send time

    Returns:
        ID of the created email log record, or None if failed
    """
    try:
        client = get_supabase_client()

        # Prepare email log data
        email_data = {
            "lead_id": lead_id,
            "to_email": to_email,
            "subject": subject,
            "template_used": template_name,
            "status": status,
        }

        if tracking_id:
            email_data["email_tracking_id"] = tracking_id

        if body:
            email_data["body"] = body

        if scheduled_at:
            email_data["scheduled_at"] = scheduled_at

        # Insert the email log record
        logger.info(f"Logging email sent to: {to_email}")
        response = client.table("emails").insert(email_data).execute()

        # Extract the email log ID from the response
        if response.data and len(response.data) > 0:
            email_id = response.data[0].get("id")
            logger.info(f"Email log created with ID: {email_id}")
            return email_id
        else:
            logger.error("Failed to get email log ID from Supabase response")
            return None

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error logging email: {str(e)}\nTraceback:\n{tb}")
        return None

def get_leads_to_email(job_id: str) -> List[Dict[str, Any]]:
    """
    Get leads that are ready to be emailed for a job

    Args:
        job_id: ID of the job

    Returns:
        List of lead records that have contact emails but haven't been emailed yet
    """
    try:
        client = get_supabase_client()

        # Query for leads with emails that haven't been emailed yet
        logger.info(f"Fetching leads ready for emailing for job: {job_id}")
        response = client.table("leads").select("*") \
            .eq("job_id", job_id) \
            .not_.is_("contact_email", "null") \
            .eq("status", "ReadyToSend") \
            .execute()

        if response.data:
            logger.info(f"Found {len(response.data)} leads ready for emailing")
            return response.data
        else:
            logger.info("No leads ready for emailing found")
            return []

    except Exception as e:
        logger.error(f"Error getting leads to email: {str(e)}")
        return []

def get_templates() -> List[Dict[str, Any]]:
    """
    Get all email templates

    Returns:
        List of email template records
    """
    try:
        client = get_supabase_client()

        # Query for all templates
        logger.info("Fetching email templates")
        response = client.table("templates").select("*").execute()

        if response.data:
            logger.info(f"Found {len(response.data)} email templates")
            return response.data
        else:
            logger.info("No email templates found")
            return []

    except Exception as e:
        logger.error(f"Error getting email templates: {str(e)}")
        return []

def get_template_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Get an email template by name

    Args:
        name: Name of the template

    Returns:
        Template record if found, None otherwise
    """
    try:
        client = get_supabase_client()

        # Query for the template
        logger.info(f"Fetching email template: {name}")
        response = client.table("templates").select("*").eq("name", name).execute()

        if response.data and len(response.data) > 0:
            logger.info(f"Found template: {name}")
            return response.data[0]
        else:
            logger.warning(f"Template not found: {name}")
            return None

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error getting email template: {str(e)}\nTraceback:\n{error_trace}")
        return None


# Create default email template if none exist
def ensure_default_template() -> str:
    """
    Ensure at least one default email template exists

    Returns:
        Name of the default template
    """
    try:
        client = get_supabase_client()

        # Check if any templates exist
        templates = get_templates()
        if templates:
            logger.info(f"Found existing templates: {[t['name'] for t in templates]}")
            return templates[0]["name"]

        # Create a default template
        default_template = {
            "name": "Default Template",
            "subject": "Regarding {role} role at {company_name}",
            "body": """
            Hi {founder_name},

            I came across the {role} role at {company_name}, and it feels like a perfect fit—I'm pumped to dive in and make waves. Here's a quick snapshot of what I've been up to:

            Sinking ship to rocket: Took a struggling startup with no tech team, zero cash, and high churn. In 6 months: rebuilt it with one engineer, scaled to $5K MRR, fully automated ops, and sold it to IgniteTech for $1M.

            Speed > perfection: At Layup (YC W23), I shipped MVPs in days. Most recently, built an AI voice agent that's now running at my cousin's restaurant in AU—fully integrated with their POS, calendar, and CRM.

            Built, failed, exited: Started with an agency in college—failed fast, learned faster. Joined a YC startup as a Founding Engineer. Bootstrapped my last company, couldn't scale it purely on revenue, but still drove it to acquisition.

            This time, I want to do it right—with the right team and product. Let's talk—I'd love to bring my hustle to {company_name}.

            Cheers,
            Tanush
            """,
            "variables": ["role", "founder_name", "company_name"]
        }

        # Insert the template
        logger.info("Creating default email template")
        response = client.table("templates").insert(default_template).execute()
        logger.info(f"Default template created with response: {response}")

        return "Default Template"

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error ensuring default template: {str(e)}\nTraceback:\n{error_trace}")
        return "Default Template"  # Return the name anyway as a fallback