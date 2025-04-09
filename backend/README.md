# Founder Flow Automation

An AI-powered tool to automate the process of finding job postings on WorkAtAStartup.com, identifying founder/CEO contacts, and sending personalized emails.

## System Overview

Founder Flow Automation helps users find relevant job listings, collect contact information for founders/hiring managers, and send personalized outreach emails. The system works in three main stages:

1. **Launch Job**: Parse a natural language query to find job listings on WorkAtAStartup.com
2. **Collect Leads**: Extract company and contact information from each job listing
3. **Send Emails**: Send personalized emails to collected contacts

## Technology Stack

- **Backend**: Python with ControlFlow for AI agent orchestration
- **Database**: Supabase (PostgreSQL)
- **Email**: Resend API
- **Contact Lookup**: Apollo.io API
- **Frontend**: Streamlit
- **Testing API**: FastAPI

## Project Structure

```
.
├── backend/                     # Backend code
│   ├── models.py                # Pydantic data models
│   ├── agent.py                 # ControlFlow agent definitions
│   ├── tasks.py                 # ControlFlow task definitions
│   ├── main_flow.py             # Main orchestration flow
│   ├── tools/                   # Tool implementations
│   │   ├── __init__.py          # Tool registration
│   │   ├── search.py            # Google search tools
│   │   ├── scraping.py          # Web scraping tools
│   │   ├── apollo.py            # Contact lookup tools
│   │   ├── email.py             # Email sending tools
│   │   └── supabase.py          # Database interaction tools
│   └── project-context/         # Project documentation and resources
│       ├── launch-a-job.md      # Job launch documentation
│       ├── collecting-leads.md  # Lead collection documentation
│       ├── launch-emails.md     # Email sending documentation
│       ├── supabase.md          # Database schema documentation
│       └── database_schema.sql  # SQL for database setup
├── streamlit_app.py             # Streamlit application
├── api.py                       # FastAPI server for testing
├── mock.py                      # Command-line tool for mock testing
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
└── README.md                    # This file
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/username/automate-founder-flow.git
cd automate-founder-flow
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Supabase

1. Create a new Supabase project at [https://supabase.com](https://supabase.com)
2. From the Supabase SQL Editor, run the SQL script from `backend/project-context/database_schema.sql`
3. Make note of your Supabase URL and anon key

### 4. Create API Keys

1. Get an API key from [Apollo.io](https://apollo.io) for contact lookups
2. Get an API key from [Resend](https://resend.com) for sending emails
3. Set up a verified sender email address in Resend

### 5. Configure Environment Variables

1. Copy the example environment file: `cp .env.example .env`
2. Edit `.env` and add your API keys and other configuration values

### 6. Run the Application

```bash
streamlit run streamlit_app.py
```

## Usage Guide

### Launching a Job

1. Open the Streamlit app in your browser (typically at http://localhost:8501)
2. Enter a job search query (e.g., "Remote backend engineer at fintech startups")
3. Adjust the maximum number of links to process (default: 10)
4. Click "Launch Job"

### Monitoring Jobs and Leads

1. Go to the "Jobs & Leads" tab
2. View recent jobs and their status
3. Select a job to view its collected leads
4. Leads will show different statuses: Pending, ReadyToSend, EmailNotFound, etc.

### Sending Emails

1. Select a job with leads ready to send in the "Jobs & Leads" tab
2. Choose an email template
3. Click "Send Emails"
4. The system will send personalized emails to all ready leads

### Managing Email Templates

1. Go to the "Email Templates" tab
2. View existing templates
3. Preview templates with sample data

## Testing Tools

### Command-line Testing with mock.py

The `mock.py` script provides a simple way to test individual components or the entire workflow without relying on the Streamlit interface.

```bash
# Test query parsing
python mock.py parse_query "find senior backend engineers in San Francisco"

# Test Google dork generation
python mock.py generate_dorks "find senior backend engineers in San Francisco"

# Test search execution
python mock.py search "find senior backend engineers in San Francisco"

# Test lead collection from a specific URL
python mock.py collect_lead "https://www.workatastartup.com/jobs/12345"

# Test email sending for a specific job URL
python mock.py send_email "https://www.workatastartup.com/jobs/12345"

# Test the full workflow
python mock.py full "find senior backend engineers in San Francisco"
```

### FastAPI Testing Endpoints

The project includes a FastAPI server with endpoints for testing each component and the full workflow. This makes it easy to test with tools like Postman or curl.

To start the API server:

```bash
python api.py
```

#### Available Endpoints:

- `GET /`: Health check
- `POST /parse-query`: Parse a job search query
- `POST /generate-search-plan`: Generate Google dorks for a job query
- `POST /execute-search`: Execute search with Google dorks
- `POST /collect-lead`: Collect lead information from a job URL
- `POST /send-email`: Send an email to a lead
- `POST /full-workflow`: Run the full workflow

Example using curl:

```bash
# Test parsing a query
curl -X POST http://localhost:8000/parse-query \
  -H "Content-Type: application/json" \
  -d '{"query": "find senior backend engineers in San Francisco", "use_mocks": true}'
```

Or use Postman for a more user-friendly interface.

## Testing with Mock Mode

For testing without making actual API calls:

1. Set the `USE_MOCKS=true` in your .env file, or
2. Check the "Use mock tools" option when launching a job
3. Use the `use_mocks` parameter when calling the FastAPI endpoints

## Troubleshooting

- **Connection Issues**: Ensure your Supabase and API credentials are correct in the .env file
- **Missing Environment Variables**: Check that all required variables are set in your .env file
- **Scraping Failures**: The structure of WorkAtAStartup.com may change; report issues for updates

## Contribution Guidelines

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [ControlFlow](https://controlflow.ai/) for the AI agent orchestration framework
- [Supabase](https://supabase.com/) for the database backend
- [Streamlit](https://streamlit.io/) for the frontend framework
