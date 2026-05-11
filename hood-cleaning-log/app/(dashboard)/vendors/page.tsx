import { createClient } from '@/lib/supabase/server'
import { formatDate } from '@/lib/utils'

export default async function VendorsPage() {
  const supabase = await createClient()

  const { data: vendors } = await supabase
    .from('vendors')
    .select('*, cleaning_records(count)')
    .eq('active', true)
    .is('deleted_at', null)
    .order('name')

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Vendor Directory</h1>
      </div>

      {!vendors?.length && (
        <div className="text-center py-12 text-zinc-400">
          <p className="text-3xl mb-2">🚛</p>
          <p className="font-medium">No vendors yet</p>
          <p className="text-sm mt-1">Vendors are auto-added when they submit their first cleaning record.</p>
        </div>
      )}

      <div className="bg-white rounded-xl border border-zinc-200 overflow-hidden">
        {vendors && vendors.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 text-xs text-zinc-500 uppercase tracking-wide">
              <tr>
                <th className="text-left px-4 py-3">Vendor</th>
                <th className="text-left px-4 py-3">Phone</th>
                <th className="text-left px-4 py-3">Email</th>
                <th className="text-left px-4 py-3">License</th>
                <th className="text-left px-4 py-3">Total visits</th>
                <th className="text-left px-4 py-3">Since</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {vendors.map(v => (
                <tr key={v.id} className="hover:bg-zinc-50">
                  <td className="px-4 py-3 font-medium">{v.name}</td>
                  <td className="px-4 py-3 text-zinc-600">{v.phone ?? '—'}</td>
                  <td className="px-4 py-3 text-zinc-600">{v.email ?? '—'}</td>
                  <td className="px-4 py-3 text-zinc-600">{v.license_number ?? '—'}</td>
                  <td className="px-4 py-3 text-zinc-600">{(v.cleaning_records as { count: number }[] | null)?.[0]?.count ?? 0}</td>
                  <td className="px-4 py-3 text-zinc-600">{formatDate(v.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
