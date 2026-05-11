import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { sendSms, buildDueReminderMessage } from '@/lib/twilio'

// Called by GitHub Actions cron (or Supabase scheduled function) daily
export async function POST(request: NextRequest) {
  const authHeader = request.headers.get('authorization')
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const supabase = await createClient()

  // Find hoods where next_due_at is within notification window
  const { data: records } = await supabase
    .from('cleaning_records')
    .select(`
      hood_id,
      next_due_at,
      hoods(name, location_id, locations(name)),
      notification_settings!inner(phone, notify_days_before, enabled)
    `)
    .gt('next_due_at', new Date().toISOString())
    .lte('next_due_at', new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString())

  let sent = 0
  for (const record of records ?? []) {
    const hood = record.hoods as unknown as { name: string; locations: { name: string } | null } | null
    const settings = record.notification_settings as { phone: string; notify_days_before: number[]; enabled: boolean }[] | null

    if (!hood || !settings?.length) continue

    const daysUntilDue = Math.floor(
      (new Date(record.next_due_at).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
    )

    for (const setting of settings) {
      if (!setting.enabled || !setting.phone) continue
      if (!setting.notify_days_before.includes(daysUntilDue)) continue

      const msg = buildDueReminderMessage(hood.name, hood.locations?.name ?? '', daysUntilDue)
      await sendSms(setting.phone, msg)
      sent++
    }
  }

  return NextResponse.json({ sent })
}
