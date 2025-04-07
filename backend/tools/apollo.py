"""
Apollo.io API integration tools for email lookup
"""
import requests
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def get_email_from_linkedin(linkedin_url: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Use Apollo.io API to get email address from a LinkedIn profile URL

    Args:
        linkedin_url: The LinkedIn profile URL
        api_key: Apollo.io API key (optional, will try to get from environment if not provided)

    Returns:
        Email address if found, None otherwise
    """
    if not linkedin_url:
        logger.warning("No LinkedIn URL provided")
        return None

    # Get API key from parameter or environment
    apollo_api_key = api_key or os.environ.get("APOLLO_API_KEY")
    if not apollo_api_key:
        logger.error("Apollo API key not provided and not found in environment")
        return None

    logger.info(f"Looking up email for LinkedIn URL: {linkedin_url}")

    try:
        # Prepare the request to Apollo's people/match endpoint
        url = "https://api.apollo.io/v1/people/match"
        payload = {
            "api_key": apollo_api_key,
            "linkedin_url": linkedin_url
        }

        # Make the request
        response = requests.post(url, json=payload)
        response.raise_for_status()

        # Parse the response
        data = response.json()

        # Check if we got a person record
        if data.get("person"):
            person = data["person"]

            # Check for email
            email = person.get("email")
            if email:
                logger.info(f"Found email for {linkedin_url}: {email}")
                return email

            # If no direct email, look in contact details
            contact_info = person.get("contact_info", {})
            email_from_contact = contact_info.get("email")
            if email_from_contact:
                logger.info(f"Found email from contact info for {linkedin_url}: {email_from_contact}")
                return email_from_contact

        logger.warning(f"No email found for LinkedIn URL: {linkedin_url}")
        return None

    except requests.RequestException as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Request error during Apollo API call: {str(e)}\nTraceback:\n{tb}")
        return None

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error during Apollo API call: {str(e)}\nTraceback:\n{tb}")
        return None

def get_person_details_from_linkedin(linkedin_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get full person details from Apollo.io API using a LinkedIn profile URL

    Args:
        linkedin_url: The LinkedIn profile URL
        api_key: Apollo.io API key (optional, will try to get from environment if not provided)

    Returns:
        Dictionary with person details if found, empty dict otherwise
    """
    if not linkedin_url:
        logger.warning("No LinkedIn URL provided")
        return {}

    # Get API key from parameter or environment
    apollo_api_key = api_key or os.environ.get("APOLLO_API_KEY")
    if not apollo_api_key:
        logger.error("Apollo API key not provided and not found in environment")
        return {}

    logger.info(f"Looking up person details for LinkedIn URL: {linkedin_url}")

    try:
        # Prepare the request to Apollo's people/match endpoint
        url = "https://api.apollo.io/v1/people/match"
        payload = {
            "api_key": apollo_api_key,
            "linkedin_url": linkedin_url
        }

        # Make the request
        response = requests.post(url, json=payload)
        print("apollo response", response.json())
        response.raise_for_status()

        # Parse the response
        data = response.json()

        # Check if we got a person record
        if data.get("person"):
            return data["person"]

        logger.warning(f"No person found for LinkedIn URL: {linkedin_url}")
        return {}

    except requests.RequestException as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Request error during Apollo API call: {str(e)}\nTraceback:\n{tb}")
        return {}

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error during Apollo API call: {str(e)}\nTraceback:\n{tb}")
        return {}

# Mock implementation for testing without making actual API calls
def mock_get_email_from_linkedin(linkedin_url: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Mock implementation of get_email_from_linkedin for testing

    Args:
        linkedin_url: The LinkedIn profile URL
        api_key: Ignored in mock

    Returns:
        A mock email address based on the LinkedIn URL
    """
    if not linkedin_url:
        return None

    # Extract username from URL
    parts = linkedin_url.strip('/').split('/')
    username = parts[-1] if parts else "unknown"

    # Return fake email
    if 'janedoe' in username:
        return 'jane.doe@acmestartup.com'
    elif 'johnsmith' in username:
        return 'john.smith@acmestartup.com'
    else:
        # Generate email based on username
        return f"{username.lower().replace('-', '.')}@example.com"