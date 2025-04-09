"""
FastAPI application for testing Founder Flow with mock tools
"""
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import supabase
from supabase import create_client, Client
from dotenv import load_dotenv
from .models import JobQuery, Lead, Job
from .tasks import (
    parse_user_input_task,
    generate_search_plan_task,
    execute_search_task,
    collect_lead_task,
    send_email_task
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Optional: Set other loggers to DEBUG level
for module in ["backend", "controlflow"]:
    logging.getLogger(module).setLevel(logging.DEBUG)

# Supabase client setup
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    logger.warning("Supabase environment variables (SUPABASE_URL, SUPABASE_ANON_KEY) not found. Database operations will fail.")
    supabase_client = None
else:
    try:
        supabase_client: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        supabase_client = None

# Create FastAPI app
app = FastAPI(
    title="Founder Flow API",
    description="API for testing Founder Flow automation with mock tools",
    version="0.1.0"
)

# Add CORS middleware to allow testing from frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For testing only - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class QueryRequest(BaseModel):
    query: str
    use_mocks: bool = False
    limit: int = 10  # Default limit of 10 results

class LeadRequest(BaseModel):
    job_url: str
    use_mocks: bool = False

class EmailRequest(BaseModel):
    lead: Lead
    template_name: str = "Default Template"
    use_mocks: bool = False

# Response models
class JobQueryResponse(BaseModel):
    job_query: JobQuery

class JobUrlsResponse(BaseModel):
    urls: List[str]

class LeadResponse(BaseModel):
    lead: Lead

class EmailResponse(BaseModel):
    result: Dict[str, Any]


@app.get("/")
def read_root():
    """Root endpoint - health check"""
    return {"status": "ok", "message": "Founder Flow API is running"}


@app.post("/parse-query", response_model=JobQueryResponse)
def parse_query(request: QueryRequest):
    """Parse a job search query into structured parameters"""
    try:
        logger.info(f"Parsing query: {request.query}")
        job_query = parse_user_input_task(request.query, use_mocks=request.use_mocks)
        return {"job_query": job_query}
    except Exception as e:
        logger.error(f"Error parsing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-search-plan", response_model=JobQueryResponse)
def generate_search_plan(request: JobQueryResponse):
    """Generate Google dorks for a job query"""
    try:
        logger.info(f"Generating search plan for: {request.job_query.role}")
        job_query = generate_search_plan_task(request.job_query, use_mocks=True)
        return {"job_query": job_query}
    except Exception as e:
        logger.error(f"Error generating search plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute-search", response_model=JobUrlsResponse)
def execute_search(request: JobQueryResponse):
    """Execute search and return job URLs"""
    try:
        logger.info(f"Executing search for: {request.job_query.role}")
        urls = execute_search_task(request.job_query, use_mocks=True)
        return {"urls": urls}
    except Exception as e:
        logger.error(f"Error executing search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collect-lead", response_model=LeadResponse)
def collect_lead(request: LeadRequest):
    """Collect lead information from a job URL"""
    try:
        logger.info(f"Collecting lead from: {request.job_url}")
        lead = collect_lead_task(request.job_url, use_mocks=request.use_mocks)
        return {"lead": lead}
    except Exception as e:
        logger.error(f"Error collecting lead: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-email", response_model=EmailResponse)
def send_email(request: EmailRequest):
    """Send an email to a lead"""
    try:
        logger.info(f"Sending email to: {request.lead.contact_name} at {request.lead.company_name}")
        result = send_email_task(
            request.lead,
            template_name=request.template_name,

        )
        return {"result": result}
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create-and-execute-job")
def create_and_execute_job(request: QueryRequest):
    """Create a job in Supabase, execute the workflow, save leads, and schedule emails"""
    # Check if Supabase client is available
    if supabase_client is None:
        raise HTTPException(
            status_code=503,
            detail="Database connection not available. Check server logs for details."
        )

    try:
        # 1. Parse the query
        logger.info(f"Starting job creation and execution for query: {request.query}")
        job_query = parse_user_input_task(request.query)

        # 2. Create and save job to Supabase
        now = datetime.now().isoformat()
        job_data = {
            "raw_query": request.query,
            "parsed_role": job_query.role,
            "parsed_location": job_query.location,
            "parsed_filters": job_query.filters if hasattr(job_query, "filters") else None,
            "status": "Searching",
            "created_at": now,
        }

        # Insert job into Supabase and get the ID
        response = supabase_client.table("jobs").insert(job_data).execute()
        if len(response.data) == 0:
            raise HTTPException(status_code=500, detail="Failed to create job in database")

        job_id = response.data[0]["id"]
        logger.info(f"Created job with ID: {job_id}")

        # 3. Generate search plan
        job_query = generate_search_plan_task(job_query)

        # Update job with search parameters
        supabase_client.table("jobs").update({
            "google_dorks": job_query.dorks if hasattr(job_query, "dorks") else None
        }).eq("id", job_id).execute()

        # 4. Execute search
        job_urls = execute_search_task(job_query)

        # Update job status to processing leads
        supabase_client.table("jobs").update({
            "status": "ProcessingLeads"
        }).eq("id", job_id).execute()

        # 5. Collect leads (limit to the specified number)
        leads = []
        leads_data = []
        for url in job_urls[:request.limit]:
            try:
                lead = collect_lead_task(url)
                leads.append(lead)

                # Prepare lead data for database
                lead_data = {
                    "job_id": job_id,
                    "job_url": str(url),
                    "company_url": str(lead.company_url) if lead.company_url else None,
                    "role_title": lead.role_title,
                    "company_name": lead.company_name,
                    "contact_name": lead.contact_name,
                    "contact_title": lead.contact_title,
                    "contact_linkedin_url": str(lead.contact_linkedin_url) if lead.contact_linkedin_url else None,
                    "contact_email": lead.contact_email,
                    "status": "ReadyToSend"
                }
                leads_data.append(lead_data)
            except Exception as e:
                logger.error(f"Error collecting lead from {url}: {str(e)}")

        # 6. Save leads to Supabase
        lead_response = None
        if leads_data:
            print(f"lead data : {leads_data}")
            lead_response = supabase_client.table("leads").insert(leads_data).execute()
            if not lead_response.data:
                logger.error("Failed to save leads to database")

        # 7. Schedule emails
        emails_data = []
        if lead_response and lead_response.data:
            for lead_record in lead_response.data:
                lead_id = lead_record["id"]
                contact_email = lead_record["contact_email"]

                # Skip if no email address
                if not contact_email:
                    continue

                # Schedule email for 1 day from now
                scheduled_time = (datetime.now() + timedelta(days=1)).isoformat()

                # Get template
                try:
                    logger.info("Attempting to retrieve Default Template from database")
                    template_response = supabase_client.table("templates").select("*").eq("name", "Default Template").execute()
                    logger.info(f"Template response data: {template_response.data if hasattr(template_response, 'data') else 'No data'}")

                    template = template_response.data[0] if template_response.data else None

                    if not template:
                        logger.warning("Default Template not found in database, attempting to create it")
                        # Try to ensure a default template exists
                        from .tools.supabase import ensure_default_template
                        ensure_default_template()

                        # Try to get the template again
                        template_response = supabase_client.table("templates").select("*").eq("name", "Default Template").execute()
                        template = template_response.data[0] if template_response.data else None

                        if not template:
                            logger.error("Still unable to retrieve Default Template after creation attempt")

                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    logger.error(f"Error retrieving template: {str(e)}\nTraceback:\n{error_trace}")
                    template = None

                if template:
                    # Convert dictionary to Lead object
                    from .models import Lead
                    lead_obj = Lead(
                        job_url=lead_record["job_url"],
                        company_url=lead_record["company_url"],
                        role_title=lead_record["role_title"],
                        company_name=lead_record["company_name"],
                        contact_name=lead_record["contact_name"],
                        contact_title=lead_record["contact_title"],
                        contact_linkedin_url=lead_record["contact_linkedin_url"] if "contact_linkedin_url" in lead_record else None,
                        contact_email=lead_record["contact_email"]
                    )

                    # Now pass the Lead object to send_email_task
                    result = send_email_task(lead_obj, template_name=template["name"], use_mocks=request.use_mocks)
                    logger.info(f"Email task result: {result}")

                    # Prepare email data
                    if result.get("status") == "Failed":
                        # Handle failed email preparation
                        email_data = {
                            "lead_id": lead_id,
                            "to_email": contact_email,
                            "subject": "Email preparation failed",
                            "status": "Failed",
                            "body": result.get("error", "Unknown error"),
                            "scheduled_at": scheduled_time
                        }
                    else:
                        # Success case - make sure to use get() with defaults to avoid KeyError
                        email_data = {
                            "lead_id": lead_id,
                            "to_email": contact_email,
                            "subject": result.get("subject", "No subject"),
                            "status": "ReadyToSend",
                            "body": result.get("body", "No body content"),
                            "scheduled_at": scheduled_time
                        }
                    emails_data.append(email_data)
                else:
                    email_data = {
                        "lead_id": lead_id,
                        "to_email": contact_email,
                        "subject": "No template found",
                        "status": "Failed",
                        "body": "No template found",
                        "scheduled_at": scheduled_time
                    }
                    emails_data.append(email_data)

        # Save scheduled emails to database
        # FIXME: This is already getting saved in the tool.
        if emails_data:
            email_response = supabase_client.table("emails").insert(emails_data).execute()
            if not email_response.data:
                logger.error("Failed to schedule emails in database")

        # 8. Mark job as complete
        supabase_client.table("jobs").update({
            "status": "Complete"
        }).eq("id", job_id).execute()

        return {
            "job_id": job_id,
            "status": "Complete",
            "leads_collected": len(leads_data),
            "emails_scheduled": len(emails_data),
            "job_urls_found": len(job_urls)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        # If job was created, mark it as failed
        if locals().get("job_id"):
            supabase_client.table("jobs").update({
                "status": "Failed",
                "error_message": str(e)
            }).eq("id", job_id).execute()

        logger.error(f"Error in job creation and execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env loading")

    # Get port from environment or default to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.api:app", host="0.0.0.0", port=port, reload=True)