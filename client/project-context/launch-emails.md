- once we get the leadlist
- we schedule emails to each of the leadlist with the collected variables

```
import resend

resend.api_key = "re_123456789"

params: resend.Emails.SendParams = {
  "from": "Acme <onboarding@resend.dev>",
  "to": ["delivered@resend.dev"],
  "subject": "hello world",
  "html": "<p>it works!</p>"
}

email = resend.Emails.send(params)
print(email)
```

Once succesfully scheduled - We add that to our supabase DB, so we can show that in our current emails.
Check @src/app to understand the data structure required for supabase table
We show the scheduled emails here.
