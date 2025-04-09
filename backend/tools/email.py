"""
Email sending tools using Yagmail
"""

import os
import logging
import random
import uuid
import yagmail
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, time
import pytz
from ..models import Lead, EmailTemplate
import traceback

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
    sf_tz = pytz.timezone("America/Los_Angeles")
    sf_time = now.astimezone(sf_tz)

    # Define business hour boundaries
    start_hour = 9  # 9 AM
    end_hour = 13  # 1 PM

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

    # Convert back to UTC and format
    return scheduled_time.astimezone(pytz.utc).isoformat()


class EmailSender:
    """Email sending class using Yagmail"""

    def __init__(self):
        self.yag = None
        self._init_email_client()

    def _init_email_client(self):
        """Initialize Yagmail connection"""
        try:
            email_user = os.environ.get("GMAIL_USER")
            email_password = os.environ.get("GMAIL_APP_PASSWORD")

            if not email_user or not email_password:
                logger.error("Gmail credentials not found in environment variables")
                return

            self.yag = yagmail.SMTP(
                email_user,
                email_password,
                host="smtp.gmail.com",
                port=587,
                smtp_starttls=True,
                smtp_skip_login=False,
            )
            logger.info(f"Email client initialized for {email_user}")
        except Exception as e:
            logger.error(f"Failed to initialize email client: {str(e)}")
            self.yag = None

# FIXME: Not working most probably gotta test thing function.
def send_email_yagmail(
    to: str,
    subject: str,
    contents: List[str],
    from_email: Optional[str] = None,
    attachments: List[str] = None,
    bcc: Optional[str] = None,
    schedule: bool = True,
) -> Dict[str, Any]:
    """
    Send an email using Yagmail with Gmail Mailsuite tracking

    Args:
        to: Recipient email address
        subject: Email subject
        contents: List of content blocks (can be plain text or HTML)
        from_email: Sender email address (optional, uses GMAIL_USER env var)
        attachments: List of file paths to attach
        bcc: BCC recipient for tracking
        schedule: Whether to schedule the email for SF business hours (9 AM-1 PM)

    Returns:
        Dictionary with sending status and tracking info
    """
    # Generate tracking ID
    tracking_id = str(uuid.uuid4())

    # Initialize email sender
    sender = EmailSender()
    if not sender.yag:
        return {"error": "Email client initialization failed"}

    # Get from email
    from_email = from_email or os.environ.get("GMAIL_USER")

    if not to:
        logger.error("No recipient email address provided")
        return {"error": "No recipient email address provided"}

    # Handle scheduling
    if schedule:
        send_at = get_next_sf_business_hour()
        logger.info(f"Email scheduled for {send_at}")

        # Store in Supabase
        from .supabase import get_supabase_client

        try:
            client = get_supabase_client()

            email_data = {
                "to_email": to,
                "subject": subject,
                "body": contents[0] if contents else "",
                "status": "Scheduled",
                "scheduled_at": send_at,
                "template_used": "direct_send",
                "email_tracking_id": tracking_id,
                "delivery_metrics": {"retries": 0},
            }

            if attachments:
                email_data["attachments"] = attachments

            if bcc:
                email_data["bcc"] = bcc

            response = client.table("emails").insert(email_data).execute()

            if response.data and len(response.data) > 0:
                email_id = response.data[0].get("id")
                return {
                    "status": "scheduled",
                    "scheduled_time": send_at,
                    "email_id": email_id,
                    "tracking_id": tracking_id,
                }
        except Exception as e:
            logger.error(f"Failed to schedule email: {str(e)}")
            return {"error": f"Failed to schedule email: {str(e)}"}

    # Send immediately
    try:
        # Prepare email parameters
        email_params = {"to": to, "subject": subject, "contents": contents}

        if attachments:
            email_params["attachments"] = attachments

        if bcc:
            email_params["bcc"] = bcc

        # Send the email
        sender.yag.send(**email_params)
        logger.info(f"Email sent successfully to {to}")

        # Log the sent email
        try:
            from .supabase import get_supabase_client

            client = get_supabase_client()

            email_data = {
                "to_email": to,
                "subject": subject,
                "body": contents[0] if contents else "",
                "status": "Sent",
                "sent_at": datetime.now(pytz.utc).isoformat(),
                "template_used": "direct_send",
                "email_tracking_id": tracking_id,
                "delivery_metrics": {"sent_time": datetime.now(pytz.utc).isoformat()},
            }

            if attachments:
                email_data["attachments"] = attachments

            if bcc:
                email_data["bcc"] = bcc

            response = client.table("emails").insert(email_data).execute()

            if response.data and len(response.data) > 0:
                email_id = response.data[0].get("id")
                return {
                    "status": "sent",
                    "email_id": email_id,
                    "tracking_id": tracking_id,
                }
        except Exception as e:
            logger.error(f"Failed to log sent email: {str(e)}")

        return {"status": "sent", "tracking_id": tracking_id}

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return {"error": str(e)}


def render_email_template(
    template: EmailTemplate, vars_dict: Dict[str, str]
) -> Dict[str, Any]:
    """
    Render an email template by replacing variables with values

    Args:
        template: EmailTemplate object
        vars_dict: Dictionary of variable names and values

    Returns:
        Dictionary with rendered 'subject' and 'body' and other metadata
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

    # Prepare result with additional formatting options
    return {
        "subject": subject,
        "body": body,
        "html_body": (
            body
            if body.strip().startswith("<")
            else f"<p>{body.replace('\n\n', '</p><p>')}</p>"
        ),
        "plain_body": (
            body.replace("<p>", "").replace("</p>", "\n\n")
            if body.strip().startswith("<")
            else body
        ),
        "contents": [body],  # Format ready for Yagmail
    }


def prepare_email_for_lead(lead: Lead, template: EmailTemplate) -> Dict[str, Any]:
    """
    Prepare a personalized email for a lead

    Args:
        lead: Lead object with contact information
        template: EmailTemplate to use

    Returns:
        Dictionary with rendered email content and metadata
    """

    lead = Lead(**lead)
    # Create variables dictionary from lead information
    vars_dict = {
        "role": lead.role_title or "the role",
        "founder_name": lead.contact_name or "Founder",
        "company_name": lead.company_name or "your company",
    }

    # Render the template
    return render_email_template(template, vars_dict)


def process_scheduled_emails():
    """Process pending emails that are scheduled to be sent"""
    try:
        from .supabase import get_supabase_client

        client = get_supabase_client()
        now = datetime.now(pytz.utc).isoformat()

        # Get emails ready to send
        response = (
            client.table("emails")
            .select("*")
            .eq("status", "Scheduled")
            .lte("scheduled_at", now)
            .execute()
        )

        if not response.data:
            logger.info("No scheduled emails ready to send")
            return

        logger.info(f"Processing {len(response.data)} scheduled emails")
        sender = EmailSender()

        if not sender.yag:
            logger.error(
                "Email client initialization failed, cannot process scheduled emails"
            )
            return

        for email in response.data:
            try:
                # Prepare email parameters
                email_params = {
                    "to": email["to_email"],
                    "subject": email["subject"],
                    "contents": [email.get("body", "")],
                }

                if email.get("attachments"):
                    email_params["attachments"] = email["attachments"]

                if email.get("bcc"):
                    email_params["bcc"] = email["bcc"]

                # Send the email
                sender.yag.send(**email_params)

                # Update status
                client.table("emails").update(
                    {
                        "status": "Sent",
                        "sent_at": datetime.now(pytz.utc).isoformat(),
                        "delivery_metrics": {
                            "sent_time": datetime.now(pytz.utc).isoformat()
                        },
                    }
                ).eq("id", email["id"]).execute()

                logger.info(
                    f"Scheduled email {email['id']} sent successfully to {email['to_email']}"
                )

            except Exception as e:
                logger.error(f"Failed to send scheduled email {email['id']}: {str(e)}")

                # Update retry count
                delivery_metrics = email.get("delivery_metrics", {})
                if not delivery_metrics:
                    delivery_metrics = {"retries": 0}

                retries = delivery_metrics.get("retries", 0) + 1

                # Exponential backoff for retries
                next_retry = datetime.now(pytz.utc) + timedelta(hours=2**retries)

                client.table("emails").update(
                    {
                        "status": "Failed",
                        "delivery_metrics": {
                            "retries": retries,
                            "last_error": str(e),
                            "next_retry": (
                                next_retry.isoformat() if retries < 3 else None
                            ),
                        },
                    }
                ).eq("id", email["id"]).execute()

    except Exception as e:
        logger.error(f"Error processing scheduled emails: {str(e)}")
