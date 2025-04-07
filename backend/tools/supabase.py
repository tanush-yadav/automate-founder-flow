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
    supabase_key = os.environ.get("SUPABASE_KEY")

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

def log_email_sent(lead_id: str, to_email: str, subject: str, template_name: str, resend_id: Optional[str] = None, status: str = "Sent") -> Optional[str]:
    """
    Log an email that was sent

    Args:
        lead_id: ID of the lead the email was sent to
        to_email: Recipient email address
        subject: Email subject
        template_name: Name of the template used
        resend_id: Optional ID from Resend API
        status: Email status (default: "Sent")

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
        if resend_id:
            email_data["resend_message_id"] = resend_id

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
            logger.info(f"Template not found: {name}")
            return None

    except Exception as e:
        logger.error(f"Error getting email template: {str(e)}")
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
            return templates[0]["name"]

        # Create a default template
        default_template = {
            "name": "Default Template",
            "subject": "Regarding {{role}} position at {{company_name}}",
            "body": """
            <p>Hello {{founder_name}},</p>

            <p>I came across the {{role}} position at {{company_name}} and I'm very interested in learning more.</p>

            <p>Would you be open to a quick chat about this opportunity?</p>

            <p>Best regards,<br>
            Your Name</p>
            """,
            "variables": ["role", "founder_name", "company_name"]
        }

        # Insert the template
        logger.info("Creating default email template")
        response = client.table("templates").insert(default_template).execute()

        return "Default Template"

    except Exception as e:
        logger.error(f"Error ensuring default template: {str(e)}")
        return "Default Template"  # Return the name anyway as a fallback