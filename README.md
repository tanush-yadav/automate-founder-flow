# Founder Flow Automation

AI-powered tool that automates finding job postings, identifying founder contacts, and sending personalized emails. Simply type what you're looking for and let the system do the rest.

## What It Does

- **Job Finding**: Searches WorkAtAStartup.com for relevant job listings
- **Lead Generation**: Automatically extracts company and contact information
- **Automated Outreach**: Schedules personalized emails to founders/CEOs

## How It Works

```
> find founding engineer roles in san francisco

✓ Found 12 job listings
✓ Collected 9 founder emails
✓ Scheduled 9 personalized outreach emails
```

One simple prompt saves 3-4 hours of manual work per outreach session.

## Next Steps

- **LinkedIn Integration**: Support "find me consulting roles in Canada" with LinkedIn outreach
- **UI Development**: Weekend project to add interface for creating sequences and playbooks
- **Playbooks**: Custom outreach strategies for different job types and markets, follow ups and outbox.

## Tech Stack

Python backend with ControlFlow for orchestration, Supabase for data storage, Apollo.io for contact lookups, and email integration with yagmail.
