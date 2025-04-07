"""
Web scraping tools for extracting data from WorkAtAStartup.com using Playwright
"""
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin
import asyncio
from playwright.async_api import async_playwright, Page, Error as PlaywrightError
from ..models import JobPageDetails, CompanyPageDetails

logger = logging.getLogger(__name__)

async def scrape_job_page(url: str) -> JobPageDetails:
    """
    Scrape a job listing page on workatastartup.com using Playwright

    Args:
        url: URL of the job listing page

    Returns:
        JobPageDetails object with extracted information
    """
    logger.info(f"Scraping job page: {url}")

    # Initialize the return object with the URL
    job_details = JobPageDetails(job_url=url)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Navigate to the job page
                response = await page.goto(url, wait_until="networkidle")

                # Check if page returned 404 Not Found or other error status
                if response and (response.status >= 400 or not response.ok):
                    logger.warning(f"Page returned status {response.status}: {url}")
                    return job_details

                # Direct targeting of elements with specific classes

                # Get role and company from the specific span element
                company_name_element = await page.query_selector('.company-name')
                if company_name_element:
                    full_text = await company_name_element.inner_text()
                    logger.info(f"Found company-name element: {full_text}")

                    # Parse text like "Ex-Founder at SimCare AI (S24)"
                    if " at " in full_text:
                        parts = full_text.split(" at ", 1)
                        job_details.role_title = parts[0].strip()

                        # Handle company name with batch annotation like "(S24)"
                        company_part = parts[1].strip()
                        if " (" in company_part:
                            company_part = company_part.split(" (", 1)[0].strip()
                        job_details.company_name = company_part

                # If we didn't get the role title from the company name element, look for it directly
                if not job_details.role_title:
                    role_element = await page.query_selector('h1')
                    if role_element:
                        job_details.role_title = await role_element.inner_text()

                # Get company URL - direct link to company page
                company_link = await page.query_selector('a[href*="/companies/"]')
                if company_link:
                    company_url = await company_link.get_attribute('href')
                    if company_url:
                        job_details.company_url = urljoin('https://www.workatastartup.com', company_url)

                # Extract job description - look for specific content sections
                description_sections = []

                # Look for "About the role" section directly
                about_role = await page.query_selector('h2:has-text("About the role"), h3:has-text("About the role")')
                if about_role:
                    # Get the next element which contains the content
                    content = await about_role.evaluate('el => { let next = el.nextElementSibling; return next ? next.innerText : ""; }')
                    if content:
                        description_sections.append(f"About the role\n\n{content}")

                # Look for "Responsibilities" section
                responsibilities = await page.query_selector('h2:has-text("Responsibilities"), h3:has-text("Responsibilities")')
                if responsibilities:
                    content = await responsibilities.evaluate('el => { let next = el.nextElementSibling; return next ? next.innerText : ""; }')
                    if content:
                        description_sections.append(f"Responsibilities\n\n{content}")

                # Look for "Requirements" section
                requirements = await page.query_selector('h2:has-text("Requirements"), h3:has-text("Requirements")')
                if requirements:
                    content = await requirements.evaluate('el => { let next = el.nextElementSibling; return next ? next.innerText : ""; }')
                    if content:
                        description_sections.append(f"Requirements\n\n{content}")

                # Combine all sections
                if description_sections:
                    job_details.job_description = "\n\n".join(description_sections)
                else:
                    # Fallback to main content if no specific sections found
                    main_content = await page.query_selector('main')
                    if main_content:
                        job_details.job_description = await main_content.inner_text()

            except PlaywrightError as e:
                # Handle Playwright-specific errors like navigation failures
                if "404" in str(e) or "Page not found" in str(e):
                    logger.warning(f"Page not found (404): {url}")
                else:
                    logger.error(f"Playwright error scraping job page {url}: {str(e)}")

            await browser.close()

        logger.info(f"Successfully scraped job page: {url}")
        return job_details

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error scraping job page {url}: {str(e)}\nTraceback:\n{tb}")
        return job_details


async def scrape_company_page(url: str) -> CompanyPageDetails:
    """
    Scrape a company page on workatastartup.com to extract founder information using Playwright

    Args:
        url: URL of the company page

    Returns:
        CompanyPageDetails object with extracted information
    """
    logger.info(f"Scraping company page: {url}")

    # Initialize the return object with the URL
    company_details = CompanyPageDetails(company_url=url)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Navigate to the company page
                response = await page.goto(url, wait_until="networkidle")

                # Check if page returned 404 Not Found or other error status
                if response and (response.status >= 400 or not response.ok):
                    logger.warning(f"Page returned status {response.status}: {url}")
                    return company_details

                # Extract company name only if not already set (normally it should be set from job page)
                if not company_details.company_name:
                    company_name_element = await page.query_selector('h1')
                    if company_name_element:
                        company_details.company_name = await company_name_element.inner_text()

                # FOCUS ONLY ON FOUNDERS SECTION
                # Look for the founders section directly - it usually has a heading
                founders_section = await page.query_selector('h2:has-text("Founders"), h3:has-text("Founders"), h4:has-text("Founders")')

                founders = []

                if founders_section:
                    # Get the container that has the founder profiles
                    founders_container = await founders_section.evaluate('''
                        el => {
                            // Get the parent container that holds all founder profiles
                            let container = el.nextElementSibling;
                            return container ? container.outerHTML : null;
                        }
                    ''')

                    if founders_container:
                        # Extract all founder profiles from the container
                        founder_profiles = await page.evaluate('''
                            html => {
                                const container = document.createElement('div');
                                container.innerHTML = html;

                                // Find all potential founder profile elements
                                // They usually have an image, name, title, and LinkedIn link
                                const profiles = [];

                                // Look for LinkedIn links
                                const linkedInLinks = container.querySelectorAll('a[href*="linkedin.com"]');

                                for (const link of linkedInLinks) {
                                    // For each LinkedIn link, find the surrounding profile info
                                    let profileElement = link;
                                    // Go up to likely profile container
                                    for (let i = 0; i < 3; i++) {
                                        if (!profileElement.parentElement) break;
                                        profileElement = profileElement.parentElement;

                                        // If this element has multiple children, it might be the profile container
                                        if (profileElement.children.length >= 3) break;
                                    }

                                    // Extract profile information
                                    const profile = {
                                        name: null,
                                        title: null,
                                        linkedin_url: link.href
                                    };

                                    // Find name and title
                                    const nameElements = profileElement.querySelectorAll('h3, h4, strong, b, p');
                                    for (const el of nameElements) {
                                        const text = el.innerText.trim();
                                        // Skip elements with "founder" which is likely a title
                                        if (text && text.length < 50 && !text.toLowerCase().includes('founder')) {
                                            profile.name = text;
                                            break;
                                        }
                                    }

                                    // Find title
                                    const titleElements = profileElement.querySelectorAll('p, div');
                                    for (const el of titleElements) {
                                        const text = el.innerText.trim();
                                        if (text && (
                                            text.toLowerCase().includes('founder') ||
                                            text.toLowerCase().includes('ceo') ||
                                            text.toLowerCase().includes('chief')
                                        )) {
                                            profile.title = text;
                                            break;
                                        }
                                    }

                                    // Only add if we have a LinkedIn URL
                                    if (profile.linkedin_url) {
                                        profiles.push(profile);
                                    }
                                }

                                return profiles;
                            }
                        ''', founders_container)

                        if founder_profiles:
                            # Filter out duplicates
                            seen_links = set()
                            for profile in founder_profiles:
                                if profile.get('linkedin_url') and profile['linkedin_url'] not in seen_links:
                                    seen_links.add(profile['linkedin_url'])

                                    # If no title was found but we have LinkedIn, set a default title
                                    if not profile.get('title') and profile.get('linkedin_url'):
                                        profile['title'] = "Co-founder"

                                    founders.append(profile)

                # If we couldn't find founders through the section heading, try a direct search for LinkedIn links
                if not founders:
                    # Look for all LinkedIn links on the page
                    linkedin_links = await page.query_selector_all('a[href*="linkedin.com"]')

                    for link in linkedin_links:
                        try:
                            # Check if this link is related to a founder
                            is_founder_link = await link.evaluate('''
                                link => {
                                    // Check surrounding text for founder-related terms
                                    let element = link;
                                    for (let i = 0; i < 3; i++) {
                                        if (!element.parentElement) break;
                                        element = element.parentElement;

                                        if (element.innerText && (
                                            element.innerText.toLowerCase().includes('founder') ||
                                            element.innerText.toLowerCase().includes('ceo') ||
                                            element.innerText.toLowerCase().includes('chief')
                                        )) {
                                            return true;
                                        }
                                    }
                                    return false;
                                }
                            ''')

                            if is_founder_link:
                                linkedin_url = await link.get_attribute('href')

                                # Get surrounding text to extract name and title
                                profile_info = await link.evaluate('''
                                    link => {
                                        let element = link;
                                        for (let i = 0; i < 3; i++) {
                                            if (!element.parentElement) break;
                                            element = element.parentElement;
                                        }

                                        // Extract information
                                        const name = element.querySelector('h3, h4, strong, b')?.innerText.trim() || null;

                                        // Find title in paragraphs or divs
                                        let title = null;
                                        const elements = element.querySelectorAll('p, div');
                                        for (const el of elements) {
                                            if (el.innerText && (
                                                el.innerText.toLowerCase().includes('founder') ||
                                                el.innerText.toLowerCase().includes('ceo') ||
                                                el.innerText.toLowerCase().includes('chief')
                                            )) {
                                                title = el.innerText.trim();
                                                break;
                                            }
                                        }

                                        return { name, title };
                                    }
                                ''')

                                # Create founder profile
                                founder = {
                                    'linkedin_url': linkedin_url
                                }

                                if profile_info.get('name'):
                                    founder['name'] = profile_info['name']

                                if profile_info.get('title'):
                                    founder['title'] = profile_info['title']
                                else:
                                    founder['title'] = "Co-founder"  # Default title

                                # Check for duplicates
                                if not any(f.get('linkedin_url') == linkedin_url for f in founders):
                                    founders.append(founder)

                        except Exception as e:
                            logger.warning(f"Error processing LinkedIn link: {str(e)}")

                company_details.founders = founders

            except PlaywrightError as e:
                # Handle Playwright-specific errors
                if "404" in str(e) or "Page not found" in str(e):
                    logger.warning(f"Page not found (404): {url}")
                else:
                    logger.error(f"Playwright error scraping company page {url}: {str(e)}")

            await browser.close()

        logger.info(f"Successfully scraped company page: {url}, found {len(founders)} founders")
        return company_details

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Error scraping company page {url}: {str(e)}\nTraceback:\n{tb}")
        return company_details


def find_contact_linkedin(company_details: CompanyPageDetails, job_details: Optional[JobPageDetails] = None) -> Optional[str]:
    """
    Identify the best contact's LinkedIn URL from the company page details.
    Focus ONLY on founders/CEOs, not hiring managers.

    Args:
        company_details: CompanyPageDetails object with company and founder info
        job_details: Optional JobPageDetails that might contain additional clues

    Returns:
        LinkedIn URL of the best contact, or None if not found
    """
    # No need to convert if it's already a CompanyPageDetails object
    if not isinstance(company_details, CompanyPageDetails):
        company_details = CompanyPageDetails(**company_details)

    if job_details and not isinstance(job_details, JobPageDetails):
        job_details = JobPageDetails(**job_details)

    # If we have no founders, we can't find a contact
    if not company_details.founders:
        return None

    # First, look for CEO or primary founder
    for founder in company_details.founders:
        title = founder.get('title', '').lower()
        if title and ('ceo' in title or 'chief' in title):
            return founder.get('linkedin_url')

    # Next, look for any co-founder
    for founder in company_details.founders:
        title = founder.get('title', '').lower()
        if title and 'founder' in title:
            return founder.get('linkedin_url')

    # If no CEO or specific founder title found, return the first founder with a LinkedIn URL
    for founder in company_details.founders:
        if founder.get('linkedin_url'):
            return founder.get('linkedin_url')

    # No suitable LinkedIn URL found
    return None


# Helper function to run async functions
def run_async(async_func, *args, **kwargs):
    """Run an async function synchronously"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_func(*args, **kwargs))


# Synchronous wrappers for the async functions
def scrape_job_page_sync(url: str) -> JobPageDetails:
    """Synchronous wrapper for scrape_job_page"""
    return run_async(scrape_job_page, url)


def scrape_company_page_sync(url: str) -> CompanyPageDetails:
    """Synchronous wrapper for scrape_company_page"""
    return run_async(scrape_company_page, url)