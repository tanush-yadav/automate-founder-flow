-- Database schema for Founder Flow Automation system

-- Table to store overall job search runs
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Use Supabase's default UUID generation
    user_id UUID REFERENCES auth.users(id) NULL, -- Optional: Link to Supabase Auth user
    created_at TIMESTAMPTZ DEFAULT timezone('utc', now()) NOT NULL,
    raw_query TEXT NULL,
    parsed_role TEXT NULL,
    parsed_location TEXT NULL,
    parsed_filters TEXT[] NULL, -- Array of text for filters
    google_dorks TEXT[] NULL, -- Array of text for dorks
    status TEXT NOT NULL DEFAULT 'Pending', -- e.g., Pending, Searching, ProcessingLeads, SendingEmails, Complete, Failed
    streamlit_session_id TEXT NULL, -- Optional: For potential state linking
    error_message TEXT NULL -- Store any error message if the job fails
);

-- Add Row Level Security (Example - adapt as needed)
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
-- Uncomment to use auth-based RLS policies:
-- CREATE POLICY "Users can view their own jobs" ON jobs FOR SELECT USING (auth.uid() = user_id);
-- CREATE POLICY "Users can insert their own jobs" ON jobs FOR INSERT WITH CHECK (auth.uid() = user_id);
-- For single-user systems, you might want a simpler policy:
CREATE POLICY "Allow all access to jobs" ON jobs FOR ALL USING (true);

-- Table to store collected leads associated with a job run
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE NOT NULL, -- Link to the parent job, cascade delete
    created_at TIMESTAMPTZ DEFAULT timezone('utc', now()) NOT NULL,
    job_url TEXT NOT NULL,
    company_url TEXT NULL,
    role_title TEXT NULL,
    company_name TEXT NULL,
    contact_name TEXT NULL,
    contact_title TEXT NULL,
    contact_linkedin_url TEXT NULL,
    contact_email TEXT NULL,
    status TEXT NOT NULL DEFAULT 'Pending', -- e.g., Pending, ScrapingFailed, ContactNotFound, EmailNotFound, ReadyToSend, Sending, EmailSent, EmailFailed
    last_attempted_at TIMESTAMPTZ NULL, -- Timestamp of the last processing attempt
    error_message TEXT NULL -- Store any error specific to this lead
);

-- Add index for faster lookup by job_id and potentially status
CREATE INDEX idx_leads_job_id ON leads(job_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE UNIQUE INDEX idx_leads_job_url_job_id ON leads(job_id, job_url); -- Ensure job URLs are unique per job

-- Add Row Level Security (Example - adapt based on jobs policy)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
-- Create a simple policy for single-user systems
CREATE POLICY "Allow all access to leads" ON leads FOR ALL USING (true);

-- Table to log individual emails sent (if not just updating lead status)
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL, -- Link to the lead, set null if lead deleted
    sent_at TIMESTAMPTZ DEFAULT timezone('utc', now()) NOT NULL,
    resend_message_id TEXT NULL, -- ID returned by Resend API
    status TEXT NOT NULL, -- e.g., Sent, Failed, Bounced
    template_used TEXT NULL, -- Name or identifier of the template used
    to_email TEXT NOT NULL,
    subject TEXT NULL
);

-- Add index for faster lookup by lead_id
CREATE INDEX idx_emails_lead_id ON emails(lead_id);

-- Add Row Level Security (Example - adapt based on leads/jobs policy)
ALTER TABLE emails ENABLE ROW LEVEL SECURITY;
-- Create a simple policy for single-user systems
CREATE POLICY "Allow all access to emails" ON emails FOR ALL USING (true);

-- Table for email templates
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) NULL, -- Optional: User-specific templates
    created_at TIMESTAMPTZ DEFAULT timezone('utc', now()) NOT NULL,
    name TEXT NOT NULL UNIQUE, -- Unique name for the template
    subject TEXT NOT NULL,
    body TEXT NOT NULL, -- HTML or Markdown content
    variables JSONB NULL -- Optional: Store list of expected {{variables}} as JSON
);

-- Add Row Level Security (Example)
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
-- Create a simple policy for single-user systems
CREATE POLICY "Allow all access to templates" ON templates FOR ALL USING (true);

-- Insert a default template
INSERT INTO templates (name, subject, body, variables)
VALUES (
    'Default Template',
    'Regarding {{role}} position at {{company_name}}',
    '<p>Hello {{founder_name}},</p>

    <p>I came across the {{role}} position at {{company_name}} and I''m very interested in learning more.</p>

    <p>Would you be open to a quick chat about this opportunity?</p>

    <p>Best regards,<br>
    Your Name</p>',
    '["role", "founder_name", "company_name"]'::jsonb
);