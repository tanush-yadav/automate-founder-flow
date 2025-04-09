"""
Search tools for generating and executing Google search queries
"""
import requests
from typing import List, Optional, Tuple
import logging
from ..models import JobQuery
import os

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


def execute_google_search(dorks: List[str], limit: int = 10, start_index: int = 0) -> Tuple[List[str], int]:
    """
    Execute Google search using SERP API and extract job URLs

    Args:
        dorks: List of Google search query strings
        limit: Maximum number of results to return
        start_index: Index to start from (for pagination/continuation)

    Returns:
        A tuple containing (list of job URLs from workatastartup.com, next start index)
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
                "api_key": os.environ.get("SERP_API_KEY"),
                "num": results_per_dork * 2,  # Request more results as some may not be relevant
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


