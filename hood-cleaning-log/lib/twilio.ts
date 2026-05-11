import twilio from 'twilio'

const client = twilio(
  process.env.TWILIO_ACCOUNT_SID!,
  process.env.TWILIO_AUTH_TOKEN!
)

export async function sendSms(to: string, body: string) {
  return client.messages.create({
    from: process.env.TWILIO_PHONE_NUMBER!,
    to,
    body,
  })
}

export function buildDueReminderMessage(hoodName: string, locationName: string, daysUntilDue: number): string {
  if (daysUntilDue <= 0) {
    return `OVERDUE: Hood "${hoodName}" at ${locationName} is past its cleaning due date. Schedule service immediately to maintain NFPA-96 compliance.`
  }
  return `Reminder: Hood "${hoodName}" at ${locationName} is due for cleaning in ${daysUntilDue} day${daysUntilDue === 1 ? '' : 's'}. — Hood Cleaning Log by Technyder`
}
