"""
ControlFlow agent definitions for the Founder Flow automation system
"""
import controlflow as cf
import logging
from typing import Dict, List, Any, Optional
from .tools import get_tools

logger = logging.getLogger(__name__)

# Instructions for agents to follow when parsing user queries
QUERY_PARSER_INSTRUCTIONS = """
You are an agent specialized in understanding job search queries. Your task is to extract key information from a user query and organize it into structured data.

Follow these rules:
1. Extract the job role/title (e.g., "backend engineer", "product manager", "designer")
2. Identify location preferences (default to "remote" if not specified)
3. Extract any other relevant filters (company stage, industry, technology, etc.)
4. Be concise and precise in your extraction
5. If the query is ambiguous, make reasonable assumptions based on context
"""

# Instructions for agents to follow when collecting lead information
LEAD_COLLECTOR_INSTRUCTIONS = """
You are an agent specialized in extracting information from job listings and company pages on WorkAtAStartup.com.

Follow these steps:
1. Use the scraping tools to extract job details and company information
2. Identify the best contact person (preferably CEO or founder)
3. Find their LinkedIn URL
4. Use Apollo.io to find their email address
5. Organize the collected information into a structured lead

Be thorough and accurate in your data extraction. If certain information can't be found, note that clearly.
"""

# Instructions for agents to follow when sending personalized emails
EMAIL_AGENT_INSTRUCTIONS = """
You are an agent specialized in sending personalized emails to job listing contacts.

Follow these steps:
1. Select an appropriate email template
2. Personalize the template based on the lead information (company name, role, contact's name)
3. Ensure the email is professional and compelling
4. Send the email using the provided tools
5. Log the email sending status

Be careful to use accurate information and professional language in all communications.
"""

def create_query_parser_agent(use_mocks: bool = False) -> cf.Agent:
    """
    Create an agent for parsing user queries into structured job search parameters

    Args:
        use_mocks: Whether to use mock tools for testing

    Returns:
        ControlFlow Agent configured for query parsing
    """
    # Define the tools the agent will have access to
    agent_tools = get_tools(use_mocks=use_mocks)

    # Create and return the agent
    agent = cf.Agent(
        name="Query Parser",
        instructions=QUERY_PARSER_INSTRUCTIONS,
        tools=agent_tools
    )

    logger.info("Created Query Parser agent")
    return agent

def create_lead_collector_agent(use_mocks: bool = False) -> cf.Agent:
    """
    Create an agent for collecting lead information from job and company pages

    Args:
        use_mocks: Whether to use mock tools for testing

    Returns:
        ControlFlow Agent configured for lead collection
    """
    # Define the tools the agent will have access to
    agent_tools = get_tools(use_mocks=use_mocks)

    # Create and return the agent
    agent = cf.Agent(
        name="Lead Collector",
        instructions=LEAD_COLLECTOR_INSTRUCTIONS,
        tools=agent_tools
    )

    logger.info("Created Lead Collector agent")
    return agent

def create_email_agent(use_mocks: bool = False) -> cf.Agent:
    """
    Create an agent for sending personalized emails to leads

    Args:
        use_mocks: Whether to use mock tools for testing

    Returns:
        ControlFlow Agent configured for email sending
    """
    # Define the tools the agent will have access to
    agent_tools = get_tools(use_mocks=use_mocks)

    # Create and return the agent
    agent = cf.Agent(
        name="Email Agent",
        instructions=EMAIL_AGENT_INSTRUCTIONS,
        tools=agent_tools
    )

    logger.info("Created Email Agent")
    return agent

def get_default_agent(use_mocks: bool = False) -> cf.Agent:
    """
    Get a default general-purpose agent

    Args:
        use_mocks: Whether to use mock tools for testing

    Returns:
        Default ControlFlow Agent
    """
    # Define the tools the agent will have access to
    agent_tools = get_tools(use_mocks=use_mocks)

    # Create and return the agent
    agent = cf.Agent(
        name="Founder Flow Assistant",
        tools=agent_tools
    )

    logger.info("Created default agent")
    return agent
