Launch a job with simple NLP (works for workatstartup.com only right now)

- Configure the google dorks and query you are targetting.
- Filters and preferences: only one filter i.e. "remote"
  class Query:
  location : str
  role : str
  limit: int
  google_dorks: list[str]

  using above structure we can output google dork query to execute and get links to click and get info.

- Limits of links used from google search output.
  All the above with a single prompt - We output queries and filters in the way job understands.
  User prompts -> Passed to controlflow function -> outputs.
- Choose from templates already defined by the user.
- Review the results returned from the NLP.

pseudo controlflow function
