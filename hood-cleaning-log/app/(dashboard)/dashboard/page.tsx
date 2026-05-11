import { createClient } from '@/lib/supabase/server'
import Link from 'next/link'
import { computeHoodStatus } from '@/lib/supabase/types'
import { formatDate, daysUntil } from '@/lib/utils'
import { HoodStatusPill } from '@/components/hood-status-pill'

export default async function DashboardPage() {
  const supabase = await createClient()

  const { data: locations } = await supabase
    .from('locations')
    .select('*, hoods(id, name, frequency_days, cleaning_records(cleaned_at, next_due_at) )')
    .eq('active', true)
    .is('deleted_at', null)
    .order('name')

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Location Board</h1>
        <Link href="/locations/new" className="text-sm bg-zinc-900 text-white px-4 py-2 rounded-lg hover:bg-zinc-700">
          + Add Location
        </Link>
      </div>

      {!locations?.length && (
        <div className="text-center py-16 text-zinc-400">
          <p className="text-4xl mb-3">🏠</p>
          <p className="font-medium">No locations yet</p>
          <p className="text-sm mt-1">Add your first restaurant location to get started.</p>
          <Link href="/locations/new" className="inline-block mt-4 bg-zinc-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-zinc-700">
            Add location
          </Link>
        </div>
      )}

      <div className="space-y-4">
        {locations?.map((loc) => {
          const hoods = (loc.hoods ?? []) as Array<{
            id: string; name: string; frequency_days: number
            cleaning_records: Array<{ cleaned_at: string; next_due_at: string }>
          }>

          const hoodStatuses = hoods.map(h => {
            const latest = h.cleaning_records?.sort((a, b) =>
              new Date(b.cleaned_at).getTime() - new Date(a.cleaned_at).getTime()
            )[0]
            return computeHoodStatus(latest?.next_due_at ?? null)
          })

          const locStatus = hoodStatuses.includes('red') ? 'red'
            : hoodStatuses.includes('yellow') ? 'yellow'
            : hoodStatuses.every(s => s === 'green') && hoodStatuses.length > 0 ? 'green'
            : 'unknown'

          return (
            <Link key={loc.id} href={`/locations/${loc.id}`}
              className="block bg-white rounded-xl border border-zinc-200 p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h2 className="font-semibold">{loc.name}</h2>
                  <p className="text-xs text-zinc-400">{loc.city}{loc.state ? `, ${loc.state}` : ''}</p>
                </div>
                <HoodStatusPill status={locStatus} />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {hoods.map(h => {
                  const latest = h.cleaning_records?.sort((a, b) =>
                    new Date(b.cleaned_at).getTime() - new Date(a.cleaned_at).getTime()
                  )[0]
                  const status = computeHoodStatus(latest?.next_due_at ?? null)
                  const days = daysUntil(latest?.next_due_at)

                  return (
                    <div key={h.id} className="bg-zinc-50 rounded-lg p-2.5 text-xs">
                      <div className="flex items-center justify-between gap-1 mb-1">
                        <span className="font-medium truncate">{h.name}</span>
                        <HoodStatusPill status={status} />
                      </div>
                      <p className="text-zinc-400">
                        {latest
                          ? days !== null && days < 0
                            ? `Overdue ${Math.abs(days)}d`
                            : days !== null
                              ? `Due in ${days}d`
                              : formatDate(latest.next_due_at)
                          : 'No record'}
                      </p>
                    </div>
                  )
                })}
                {hoods.length === 0 && (
                  <p className="text-xs text-zinc-400 col-span-full">No hoods configured</p>
                )}
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}
