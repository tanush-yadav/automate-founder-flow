"""
Email sending tools using Resend API
"""
import os
import logging
import random
from typing import Optional, Dict, Any
import requests
from datetime import datetime, timedelta, time
import pytz
from ..models import Lead, EmailTemplate

logger = logging.getLogger(__name__)

def get_next_sf_business_hour() -> str:
    """
    Get the next available send time between 9 AM and 1 PM San Francisco time

    Returns:
        ISO 8601 formatted string for the scheduled send time
    """
    # Get current time in UTC
    now = datetime.now(pytz.utc)

    # Convert to San Francisco time (Pacific Time)
    sf_tz = pytz.timezone('America/Los_Angeles')
    sf_time = now.astimezone(sf_tz)

    # Define business hour boundaries
    start_hour = 9  # 9 AM
    end_hour = 13   # 1 PM

    # Create datetime for today at start_hour
    today_start = sf_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)

    # If it's before business hours today, schedule for today
    if sf_time.hour < start_hour:
        # Add a random minute offset (0-120 minutes)
        random_minutes = random.randint(0, 120)
        scheduled_time = today_start + timedelta(minutes=random_minutes)
    # If it's during business hours today, schedule for 30-60 minutes from now
    elif start_hour <= sf_time.hour < end_hour:
        random_minutes = random.randint(30, 60)
        scheduled_time = sf_time + timedelta(minutes=random_minutes)
        # Ensure it doesn't go beyond business hours
        if scheduled_time.hour >= end_hour:
            scheduled_time = today_start + timedelta(days=1)
    # If it's after business hours today, schedule for tomorrow
    else:
        scheduled_time = today_start + timedelta(days=1)

    # Convert back to UTC and format for Resend API
    return scheduled_time.astimezone(pytz.utc).isoformat()

def send_email_resend(to: str, subject: str, html_body: str, from_email: Optional[str] = None,
                      api_key: Optional[str] = None, schedule: bool = True) -> Dict[str, Any]:
    """
    Send an email using Resend API

    Args:
        to: Recipient email address
        subject: Email subject
        html_body: Email body in HTML format
        from_email: Sender email address (optional, defaults to configured address)
        api_key: Resend API key (optional, will try to get from environment if not provided)
        schedule: Whether to schedule the email for SF business hours (9 AM-1 PM)

    Returns:
        Dictionary with response from Resend API including 'id' if successful
    """
    if not to:
        logger.error("No recipient email address provided")
        return {"error": "No recipient email address provided"}

    # Get API key from parameter or environment
    resend_api_key = api_key or os.environ.get("RESEND_API_KEY")
    if not resend_api_key:
        logger.error("Resend API key not provided and not found in environment")
        return {"error": "Resend API key not provided"}

    # Get from email from parameter or environment or use default
    sender = from_email or os.environ.get("RESEND_FROM_EMAIL") or "onboarding@resend.dev"

    # Get scheduled send time if requested
    send_at = None
    if schedule:
        send_at = get_next_sf_business_hour()
        logger.info(f"Scheduling email to: {to} at {send_at}")
    else:
        logger.info(f"Sending email immediately to: {to}")

    try:
        # Prepare the request
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": sender,
            "to": to,
            "subject": subject,
            "html": html_body
        }

        # Add send_at parameter if scheduling
        if send_at:
            payload["send_at"] = send_at

        # Make the request
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        # Parse the response
        data = response.json()

        if send_at:
            logger.info(f"Email scheduled successfully to {to} for {send_at}, Resend ID: {data.get('id')}")
        else:
            logger.info(f"Email sent successfully to {to}, Resend ID: {data.get('id')}")
        return data

    except requests.RequestException as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Request error during Resend API call: {str(e)}\nTraceback:\n{tb}")
        return {"error": str(e), "traceback": tb}

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error during Resend API call: {str(e)}\nTraceback:\n{tb}")
        return {"error": str(e), "traceback": tb}

def render_email_template(template: EmailTemplate, vars_dict: Dict[str, str]) -> Dict[str, str]:
    """
    Render an email template by replacing variables with values

    Args:
        template: EmailTemplate object
        vars_dict: Dictionary of variable names and values

    Returns:
        Dictionary with rendered 'subject' and 'body'
    """
    # Start with copies of the template
    template = EmailTemplate(**template)
    subject = template.subject
    body = template.body

    # Replace each variable in the subject and body
    for var_name, var_value in vars_dict.items():
        placeholder = "{{" + var_name + "}}"
        subject = subject.replace(placeholder, var_value)
        body = body.replace(placeholder, var_value)

    return {
        "subject": subject,
        "body": body
    }

def prepare_email_for_lead(lead: Lead, template: EmailTemplate) -> Dict[str, str]:
    """
    Prepare a personalized email for a lead

    Args:
        lead: Lead object with contact information
        template: EmailTemplate to use

    Returns:
        Dictionary with rendered 'subject' and 'body'
    """
    template = EmailTemplate(**template)
    lead = Lead(**lead)

    # Create variables dictionary from lead information
    vars_dict = {
        "role": lead.role_title or "the role",
        "founder_name": lead.contact_name or "Founder",
        "company_name": lead.company_name or "your company"
    }

    # Render the template
    return render_email_template(template, vars_dict)

# Mock implementation for testing without making actual API calls
def mock_send_email_resend(to: str, subject: str, html_body: str, from_email: Optional[str] = None,
                          api_key: Optional[str] = None, schedule: bool = True) -> Dict[str, Any]:
    """
    Mock implementation of send_email_resend for testing

    Args:
        to: Recipient email address
        subject: Email subject
        html_body: Email body in HTML format
        from_email: Sender email address (ignored in mock)
        api_key: Resend API key (ignored in mock)
        schedule: Whether to schedule the email (for testing)

    Returns:
        Mock success response
    """
    send_info = "scheduled" if schedule else "sent"
    send_at = get_next_sf_business_hour() if schedule else None

    logger.info(f"MOCK: {send_info} email to {to} with subject '{subject}'")
    if send_at:
        logger.info(f"MOCK: Scheduled for {send_at}")

    # Generate a fake ID
    import uuid
    fake_id = str(uuid.uuid4())

    response = {
        "id": fake_id,
        "from": from_email or "onboarding@resend.dev",
        "to": to,
        "status": "scheduled" if schedule else "sent"
    }

    if send_at:
        response["scheduled_for"] = send_at

    return response