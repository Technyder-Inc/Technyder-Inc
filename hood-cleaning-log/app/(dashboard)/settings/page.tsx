'use client'
import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { Location } from '@/lib/supabase/types'

export default function SettingsPage() {
  const [locations, setLocations] = useState<Location[]>([])
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const supabase = createClient()
    supabase.from('locations').select('*').eq('active', true).then(({ data }) => {
      setLocations(data ?? [])
    })
    supabase.from('notification_settings').select('*').limit(1).then(({ data }) => {
      if (data?.[0]) {
        setPhone(data[0].phone ?? '')
        setEmail(data[0].email ?? '')
      }
    })
  }, [])

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    const supabase = createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return

    await supabase.from('notification_settings').upsert({
      phone: phone || null,
      email: email || null,
      notify_days_before: [7, 3, 1],
      enabled: true,
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
    setLoading(false)
  }

  return (
    <div>
      <h1 className="text-xl font-bold mb-6">Settings</h1>

      <div className="max-w-md space-y-6">
        {/* Notification Settings */}
        <div className="bg-white rounded-xl border border-zinc-200 p-5">
          <h2 className="font-semibold mb-4">Reminder Notifications</h2>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">SMS phone number</label>
              <input type="tel" value={phone} onChange={e => setPhone(e.target.value)}
                placeholder="+1 555 000 0000"
                className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900" />
              <p className="text-xs text-zinc-400 mt-1">Receive SMS alerts 7, 3, and 1 day before cleaning is due.</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email address</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                placeholder="ops@restaurant.com"
                className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900" />
            </div>
            <button type="submit" disabled={loading}
              className="text-sm bg-zinc-900 text-white px-4 py-2 rounded-lg hover:bg-zinc-700 disabled:opacity-50">
              {saved ? 'Saved!' : loading ? 'Saving…' : 'Save notifications'}
            </button>
          </form>
        </div>

        {/* Locations */}
        <div className="bg-white rounded-xl border border-zinc-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Locations ({locations.length})</h2>
            <a href="/locations/new" className="text-xs text-zinc-500 hover:text-zinc-900 border border-zinc-200 px-3 py-1 rounded-lg">
              + Add
            </a>
          </div>
          {locations.map(l => (
            <div key={l.id} className="flex items-center justify-between py-2 border-b border-zinc-100 last:border-0 text-sm">
              <div>
                <p className="font-medium">{l.name}</p>
                <p className="text-xs text-zinc-400">{l.city}{l.state ? `, ${l.state}` : ''}</p>
              </div>
              <span className="text-xs text-green-600 font-medium">Active</span>
            </div>
          ))}
        </div>

        {/* Billing */}
        <div className="bg-white rounded-xl border border-zinc-200 p-5">
          <h2 className="font-semibold mb-2">Billing</h2>
          <p className="text-sm text-zinc-500 mb-3">$89/month per active location. Manage your subscription via Stripe.</p>
          <form action="/api/billing/portal" method="post">
            <button type="submit" className="text-sm border border-zinc-200 px-4 py-2 rounded-lg hover:bg-zinc-50">
              Manage billing
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
