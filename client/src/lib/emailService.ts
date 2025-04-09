import { EmailType, supabase } from './supabase'

export async function getEmails() {
  const { data, error } = await supabase
    .from('emails')
    .select('*')
    .order('sent_at', { ascending: false })

  if (error) {
    console.error('Error fetching emails:', error)
    return []
  }

  return data as EmailType[]
}

export async function getEmailById(id: string) {
  const { data, error } = await supabase
    .from('emails')
    .select('*')
    .eq('id', id)
    .single()

  if (error) {
    console.error('Error fetching email:', error)
    return null
  }

  return data as EmailType
}

// Convert Supabase email type to Mail type used in the UI
export function convertEmailToMailFormat(email: EmailType) {
  const name = email.to_email.split('@')[0] || 'Unknown'

  return {
    id: email.id,
    name: name.charAt(0).toUpperCase() + name.slice(1),
    email: email.to_email,
    subject: email.subject || 'No Subject',
    text: email.body || '',
    date: email.sent_at,
    read: true, // Assuming all emails are read
    labels: [email.status.toLowerCase()], // Using status as label
  }
}
