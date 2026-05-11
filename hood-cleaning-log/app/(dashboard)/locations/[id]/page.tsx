import { createClient } from '@/lib/supabase/server'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { computeHoodStatus } from '@/lib/supabase/types'
import { formatDate } from '@/lib/utils'
import { HoodStatusPill } from '@/components/hood-status-pill'
import { QrPrintButton } from '@/components/qr-print-button'

interface Props { params: Promise<{ id: string }> }

export default async function LocationDetailPage({ params }: Props) {
  const { id } = await params
  const supabase = await createClient()

  const { data: location } = await supabase
    .from('locations')
    .select('*')
    .eq('id', id)
    .single()

  if (!location) notFound()

  const { data: hoods } = await supabase
    .from('hoods')
    .select('*, cleaning_records(id, vendor_name, tech_name, cleaned_at, next_due_at, before_photo_url, after_photo_url, notes)')
    .eq('location_id', id)
    .eq('active', true)
    .is('deleted_at', null)
    .order('name')

  return (
    <div>
      <div className="flex items-center gap-2 text-sm text-zinc-400 mb-4">
        <Link href="/dashboard" className="hover:text-zinc-700">Locations</Link>
        <span>/</span>
        <span className="text-zinc-700 font-medium">{location.name}</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold">{location.name}</h1>
          <p className="text-sm text-zinc-400">{location.address}{location.city ? `, ${location.city}` : ''}{location.state ? ` ${location.state}` : ''}</p>
        </div>
        <div className="flex gap-2">
          <Link href={`/audit?location=${id}`} className="text-sm border border-zinc-200 px-3 py-2 rounded-lg hover:bg-zinc-50">
            Audit Packet
          </Link>
          <Link href={`/locations/${id}/hoods/new`} className="text-sm bg-zinc-900 text-white px-3 py-2 rounded-lg hover:bg-zinc-700">
            + Add Hood
          </Link>
        </div>
      </div>

      {!hoods?.length && (
        <div className="text-center py-12 text-zinc-400">
          <p className="text-3xl mb-2">🔧</p>
          <p className="font-medium">No hoods yet</p>
          <Link href={`/locations/${id}/hoods/new`} className="inline-block mt-3 bg-zinc-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-zinc-700">
            Add first hood
          </Link>
        </div>
      )}

      <div className="space-y-4">
        {hoods?.map(hood => {
          const records = ((hood.cleaning_records ?? []) as Array<{
            id: string; vendor_name: string; tech_name: string
            cleaned_at: string; next_due_at: string
            before_photo_url: string | null; after_photo_url: string | null; notes: string | null
          }>).sort((a, b) => new Date(b.cleaned_at).getTime() - new Date(a.cleaned_at).getTime())

          const latest = records[0]
          const status = computeHoodStatus(latest?.next_due_at ?? null)

          return (
            <div key={hood.id} className="bg-white rounded-xl border border-zinc-200 overflow-hidden">
              {/* Hood header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-100">
                <div className="flex items-center gap-3">
                  <HoodStatusPill status={status} />
                  <div>
                    <h2 className="font-semibold text-sm">{hood.name}</h2>
                    <p className="text-xs text-zinc-400">Every {hood.frequency_days} days</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <QrPrintButton hoodId={hood.id} hoodName={hood.name} qrCode={hood.qr_code} />
                </div>
              </div>

              {/* Latest record summary */}
              {latest && (
                <div className="px-4 py-3 bg-zinc-50 text-xs text-zinc-600 flex flex-wrap gap-4">
                  <span>Last cleaned: <strong>{formatDate(latest.cleaned_at)}</strong></span>
                  <span>Vendor: <strong>{latest.vendor_name}</strong></span>
                  <span>Tech: <strong>{latest.tech_name}</strong></span>
                  <span>Next due: <strong className={status === 'red' ? 'text-red-600' : status === 'yellow' ? 'text-yellow-600' : ''}>
                    {formatDate(latest.next_due_at)}
                  </strong></span>
                </div>
              )}

              {/* Cleaning history timeline */}
              <div className="px-4 py-3">
                <p className="text-xs font-semibold text-zinc-400 mb-2 uppercase tracking-wide">Cleaning History</p>
                {records.length === 0 && (
                  <p className="text-xs text-zinc-400">No cleaning records yet.</p>
                )}
                <div className="space-y-2">
                  {records.slice(0, 5).map(r => (
                    <div key={r.id} className="flex items-start gap-3 text-xs">
                      <span className="text-zinc-300 mt-0.5">●</span>
                      <div>
                        <span className="font-medium">{formatDate(r.cleaned_at)}</span>
                        <span className="text-zinc-400"> · {r.vendor_name} / {r.tech_name}</span>
                        {r.notes && <p className="text-zinc-500 mt-0.5">{r.notes}</p>}
                        <div className="flex gap-2 mt-1">
                          {r.before_photo_url && (
                            <a href={r.before_photo_url} target="_blank" rel="noopener noreferrer"
                              className="text-blue-600 hover:underline">Before photo</a>
                          )}
                          {r.after_photo_url && (
                            <a href={r.after_photo_url} target="_blank" rel="noopener noreferrer"
                              className="text-blue-600 hover:underline">After photo</a>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
