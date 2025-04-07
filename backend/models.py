# Classes to get filters and roles from the NLP query
# All defaulting to workatastartup.com

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class JobQuery(BaseModel):
    """Query model for job search parameters"""
    raw_query: str = Field(..., description="The original user query string")
    role: str = Field(..., description="Job role/title to search for")
    location: str = Field("remote", description="Location preference (default: remote)")
    limit: int = Field(10, description="Maximum number of links to process")
    google_dorks: List[str] = Field(default_factory=list, description="Generated Google dork queries")


class JobPageDetails(BaseModel):
    """Details scraped from a job listing page"""
    job_url: HttpUrl
    role_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    company_url: Optional[HttpUrl] = None


class CompanyPageDetails(BaseModel):
    """Details scraped from a company page"""
    company_url: HttpUrl
    company_name: Optional[str] = None
    founders: List[dict] = Field(default_factory=list, description="List of founders with name, title, and linkedin_url if available")


class Lead(BaseModel):
    """Model for a potential job lead"""
    job_url: HttpUrl
    company_url: Optional[HttpUrl] = None
    role_title: Optional[str] = None
    company_name: Optional[str] = None
    job_description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_title: Optional[str] = None
    contact_linkedin_url: Optional[HttpUrl] = None
    contact_email: Optional[str] = None
    status: str = "Pending"
    error_message: Optional[str] = None


class Job(BaseModel):
    """Overall job search run model"""
    id: Optional[str] = None
    raw_query: str
    parsed_role: Optional[str] = None
    parsed_location: Optional[str] = Field("remote", description="Default to remote")
    parsed_filters: List[str] = Field(default_factory=list)
    google_dorks: List[str] = Field(default_factory=list)
    status: str = "Pending"
    leads: List[Lead] = Field(default_factory=list)
    error_message: Optional[str] = None


class EmailTemplate(BaseModel):
    """Email template model"""
    name: str
    subject: str
    body: str
    variables: List[str] = Field(default_factory=list, description="List of variable placeholders like {{role}}")


class EmailLog(BaseModel):
    """Log of an email sent"""
    lead_id: str
    to_email: str
    subject: str
    template_used: str
    status: str = "Pending"
    resend_message_id: Optional[str] = None
