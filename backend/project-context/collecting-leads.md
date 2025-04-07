Collect leads from results we got from google search

- Once the job is launched it will run for the limit and
  go to each job (https://www.workatastartup.com/jobs/73618) -> this will open on google search click
  know the hiring manager (by clicking on apply and seeing who we are texting)
  get to each company detail (https://www.workatastartup.com/companies/simcare-ai)
  check founders, if the hiring manager matches with any go to their linkedin
  if not, go to CEO's linkedin, access their email using apollo's API.

  - The endpoint to use is POST https://api.apollo.io/v1/people/match.
    `
{
"api_key": "YOUR_API_KEY",
"linkedin_url": "https://www.linkedin.com/in/example-profile"
}`

  if no result, check for other founders on the company page.
  come back with at-least one email collected.

- Collect the following
  role
  founder_name
  company_name

Above are the variables to be used in our email template
