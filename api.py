"""
FastAPI application for testing Founder Flow with mock tools
"""
import logging
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from backend.models import JobQuery, Lead, Job
from backend.tasks import (
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

# Optional: Set other loggers to DEBUG level
for module in ["backend", "controlflow"]:
    logging.getLogger(module).setLevel(logging.DEBUG)

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
    use_mocks: bool = True

class LeadRequest(BaseModel):
    job_url: str
    use_mocks: bool = True

class EmailRequest(BaseModel):
    lead: Lead
    template_name: str = "Default Template"
    use_mocks: bool = True

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
            use_mocks=request.use_mocks
        )
        return {"result": result}
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/full-workflow")
def run_full_workflow(request: QueryRequest):
    """Run the full founder flow workflow with mock tools"""
    try:
        # 1. Parse the query
        logger.info(f"Starting full workflow for query: {request.query}")
        job_query = parse_user_input_task(request.query, use_mocks=request.use_mocks)

        # 2. Generate search plan
        job_query = generate_search_plan_task(job_query, use_mocks=request.use_mocks)

        # 3. Execute search
        job_urls = execute_search_task(job_query, use_mocks=request.use_mocks)

        # 4. Collect leads (limit to first 3 for testing)
        leads = []
        for url in job_urls[:3]:
            try:
                lead = collect_lead_task(url, use_mocks=request.use_mocks)
                leads.append(lead)
            except Exception as e:
                logger.error(f"Error collecting lead from {url}: {str(e)}")

        # 5. Create a job object with collected leads
        job = Job(
            id=None,  # Will be assigned by database
            raw_query=job_query.raw_query,
            role=job_query.role,
            location=job_query.location,
            status="Testing",
            leads=leads
        )

        return {
            "job": job,
            "leads_collected": len(leads),
            "job_urls_found": len(job_urls)
        }
    except Exception as e:
        logger.error(f"Error in full workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Get port from environment or default to 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)