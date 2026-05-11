'use client'
import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { Location, CleaningRecord } from '@/lib/supabase/types'
import { formatDate } from '@/lib/utils'

export default function AuditPage() {
  const [locations, setLocations] = useState<Location[]>([])
  const [selectedLocation, setSelectedLocation] = useState('')
  const [dateFrom, setDateFrom] = useState(() => {
    const d = new Date(); d.setFullYear(d.getFullYear() - 3)
    return d.toISOString().slice(0, 10)
  })
  const [dateTo, setDateTo] = useState(() => new Date().toISOString().slice(0, 10))
  const [records, setRecords] = useState<(CleaningRecord & { hood_name?: string })[]>([])
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    const supabase = createClient()
    supabase.from('locations').select('*').eq('active', true).then(({ data }) => {
      setLocations(data ?? [])
      if (data?.[0]) setSelectedLocation(data[0].id)
    })
  }, [])

  async function loadRecords() {
    if (!selectedLocation) return
    setLoading(true)
    const supabase = createClient()
    const { data } = await supabase
      .from('cleaning_records')
      .select('*, hoods(name, location_id)')
      .gte('cleaned_at', `${dateFrom}T00:00:00`)
      .lte('cleaned_at', `${dateTo}T23:59:59`)
      .order('cleaned_at', { ascending: false })

    const filtered = (data ?? []).filter(r =>
      (r.hoods as { location_id: string } | null)?.location_id === selectedLocation
    ).map(r => ({ ...r, hood_name: (r.hoods as { name: string } | null)?.name }))

    setRecords(filtered)
    setLoading(false)
  }

  async function generatePDF() {
    setGenerating(true)
    const location = locations.find(l => l.id === selectedLocation)

    const res = await fetch('/api/audit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ location_id: selectedLocation, date_from: dateFrom, date_to: dateTo, records }),
    })

    if (res.ok) {
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `hood-cleaning-audit-${location?.name ?? 'export'}-${dateTo}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    }
    setGenerating(false)
  }

  return (
    <div>
      <h1 className="text-xl font-bold mb-6">Audit Packet Builder</h1>

      <div className="bg-white rounded-xl border border-zinc-200 p-5 mb-6">
        <div className="grid sm:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">Location</label>
            <select value={selectedLocation} onChange={e => setSelectedLocation(e.target.value)}
              className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900">
              {locations.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">From</label>
            <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)}
              className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">To</label>
            <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)}
              className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900" />
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={loadRecords} disabled={loading}
            className="text-sm border border-zinc-200 px-4 py-2 rounded-lg hover:bg-zinc-50 disabled:opacity-50">
            {loading ? 'Loading…' : 'Preview records'}
          </button>
          <button onClick={generatePDF} disabled={generating || records.length === 0}
            className="text-sm bg-zinc-900 text-white px-4 py-2 rounded-lg hover:bg-zinc-700 disabled:opacity-50">
            {generating ? 'Generating PDF…' : `Export PDF (${records.length} records)`}
          </button>
        </div>
      </div>

      {records.length > 0 && (
        <div className="bg-white rounded-xl border border-zinc-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 text-xs text-zinc-500 uppercase tracking-wide">
              <tr>
                <th className="text-left px-4 py-3">Hood</th>
                <th className="text-left px-4 py-3">Cleaned</th>
                <th className="text-left px-4 py-3">Vendor</th>
                <th className="text-left px-4 py-3">Tech</th>
                <th className="text-left px-4 py-3">Next Due</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {records.map(r => (
                <tr key={r.id} className="hover:bg-zinc-50">
                  <td className="px-4 py-3 font-medium">{r.hood_name}</td>
                  <td className="px-4 py-3 text-zinc-600">{formatDate(r.cleaned_at)}</td>
                  <td className="px-4 py-3 text-zinc-600">{r.vendor_name}</td>
                  <td className="px-4 py-3 text-zinc-600">{r.tech_name}</td>
                  <td className="px-4 py-3 text-zinc-600">{formatDate(r.next_due_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
