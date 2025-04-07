"""
Search tools for generating and executing Google search queries
"""
import requests
from typing import List, Optional
import logging
from ..models import JobQuery

logger = logging.getLogger(__name__)

def generate_google_dorks(query: JobQuery) -> List[str]:
    """
    Generate Google search queries (dorks) based on the structured job query

    Args:
        query: A JobQuery object containing search parameters

    Returns:
        A list of Google search query strings
    """
    # Base dork always targets workatastartup.com
    base_dork = "site:workatastartup.com"
    logger.info(f"Generating Google dorks for query: {query}")
    # transform the query dict to JobQuery object
    query = JobQuery(**query)
    # Add role search
    dorks = []

    # Main dork with all components
    main_dork = f"{base_dork} {query.role}"

    # Add location if it's not empty
    if query.location:
        main_dork += f" \"{query.location}\""

    dorks.append(main_dork)

    # Add variations if needed
    if query.role:
        # Try with quotes for exact match
        exact_role_dork = f"{base_dork} \"{query.role}\""
        if query.location:
            exact_role_dork += f" \"{query.location}\""
        dorks.append(exact_role_dork)

        # Try with "jobs" in the query
        jobs_dork = f"{base_dork} {query.role} jobs"
        if query.location:
            jobs_dork += f" \"{query.location}\""
        dorks.append(jobs_dork)

    logger.info(f"Generated {len(dorks)} Google dorks for query: {query.raw_query}")
    return dorks


def execute_google_search(dorks: List[str], limit: int = 10) -> List[str]:
    """
    Execute Google search using SERP API and extract job URLs

    Args:
        dorks: List of Google search query strings
        limit: Maximum number of results to return

    Returns:
        A list of job URLs from workatastartup.com
    """


    job_urls = []
    results_per_dork = max(1, limit // len(dorks))

    for dork in dorks:
        if len(job_urls) >= limit:
            break

        try:
            # Call SERP API for Google search
            params = {
                "engine": "google",
                "q": dork,
                "api_key": "fee38617c45b6681f06a5c9fbd18d068f3461d3b5767c22ec3959a7c61e9ffce",
                "num": results_per_dork * 2  # Request more results as some may not be relevant
            }

            logger.info(f"Calling SERP API with query: {dork}")
            response = requests.get("https://serpapi.com/search", params=params)
            response.raise_for_status()

            data = response.json()

            # Extract organic results
            organic_results = data.get("organic_results", [])

            for result in organic_results:
                url = result.get("link", "")

                # Filter for job URLs from workatastartup.com
                if url and 'workatastartup.com/jobs/' in url:
                    if url not in job_urls:
                        job_urls.append(url)
                        logger.info(f"Found job URL: {url}")
                        if len(job_urls) >= limit:
                            break

        except requests.RequestException as e:
            logger.error(f"Error calling SERP API: {str(e)}")
            # Continue with the next dork

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Unexpected error during SERP API search: {str(e)}\nTraceback:\n{tb}")
            # Continue with the next dork

    logger.info(f"Found {len(job_urls)} job URLs")
    return job_urls[:limit]


def mock_execute_google_search(dorks: List[str], limit: int = 10) -> List[str]:
    """
    Mock implementation of Google search for testing purposes

    Args:
        dorks: List of Google search query strings
        limit: Maximum number of results to return

    Returns:
        A list of mock job URLs from workatastartup.com
    """
    logger.info(f"Mock executing Google search with {len(dorks)} dorks")

    # Sample job URLs to return
    mock_urls = [
        "https://www.workatastartup.com/jobs/12345",
        "https://www.workatastartup.com/jobs/23456",
        "https://www.workatastartup.com/jobs/34567",
        "https://www.workatastartup.com/jobs/45678",
        "https://www.workatastartup.com/jobs/56789",
        "https://www.workatastartup.com/jobs/67890",
        "https://www.workatastartup.com/jobs/78901",
        "https://www.workatastartup.com/jobs/89012",
        "https://www.workatastartup.com/jobs/90123",
        "https://www.workatastartup.com/jobs/01234",
    ]

    # Add role and location info to the URLs to make them more realistic
    role_keywords = []
    location_keywords = []

    for dork in dorks:
        dork_parts = dork.lower().replace("site:workatastartup.com", "").strip()
        for part in dork_parts.split():
            if part.startswith('"') and part.endswith('"'):
                if "francisco" in part.lower() or "york" in part.lower() or "angeles" in part.lower():
                    location_keywords.append(part.strip('"'))
                else:
                    role_keywords.append(part.strip('"'))
            elif "engineer" in part.lower() or "developer" in part.lower() or "manager" in part.lower():
                role_keywords.append(part)

    role_keyword = role_keywords[0] if role_keywords else "software-engineer"
    location_keyword = location_keywords[0] if location_keywords else "san-francisco"

    result_urls = []
    for i, url in enumerate(mock_urls[:limit]):
        # Add role and location to make URLs more realistic
        enhanced_url = f"{url}-{role_keyword.lower().replace(' ', '-')}-{location_keyword.lower().replace(' ', '-')}"
        result_urls.append(enhanced_url)

    logger.info(f"Found {len(result_urls)} mock job URLs")
    return result_urls
