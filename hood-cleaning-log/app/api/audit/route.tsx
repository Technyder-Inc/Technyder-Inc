import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { renderToBuffer, Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer'
import { formatDate } from '@/lib/utils'

const styles = StyleSheet.create({
  page: { padding: 40, fontFamily: 'Helvetica', fontSize: 10, color: '#18181b' },
  header: { marginBottom: 24 },
  title: { fontSize: 18, fontWeight: 'bold', marginBottom: 4 },
  subtitle: { fontSize: 10, color: '#71717a' },
  divider: { borderBottom: '1px solid #e4e4e7', marginVertical: 12 },
  tableHeader: { flexDirection: 'row', backgroundColor: '#f4f4f5', padding: '6 8', borderRadius: 4, marginBottom: 4 },
  tableRow: { flexDirection: 'row', padding: '5 8', borderBottom: '1px solid #f4f4f5' },
  col1: { width: '22%' }, col2: { width: '18%' }, col3: { width: '22%' },
  col4: { width: '18%' }, col5: { width: '20%' },
  th: { fontSize: 8, fontWeight: 'bold', color: '#71717a', textTransform: 'uppercase' },
  td: { fontSize: 9, color: '#3f3f46' },
  footer: { position: 'absolute', bottom: 30, left: 40, right: 40, textAlign: 'center', fontSize: 8, color: '#a1a1aa' },
})

export async function POST(request: NextRequest) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const body = await request.json()
  const { location_id, date_from, date_to, records } = body

  const { data: location } = await supabase
    .from('locations').select('name, address, city, state').eq('id', location_id).single()

  const AuditDocument = () => (
    <Document>
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Hood Cleaning Audit Packet</Text>
          <Text style={styles.subtitle}>
            {location?.name} · {location?.address}{location?.city ? `, ${location.city}` : ''}{location?.state ? ` ${location.state}` : ''}
          </Text>
          <Text style={styles.subtitle}>Period: {formatDate(date_from)} – {formatDate(date_to)}</Text>
          <Text style={styles.subtitle}>Generated: {formatDate(new Date().toISOString())} · NFPA-96 Compliance Record</Text>
        </View>

        <View style={styles.divider} />

        {/* Table header */}
        <View style={styles.tableHeader}>
          <Text style={[styles.col1, styles.th]}>Hood</Text>
          <Text style={[styles.col2, styles.th]}>Cleaned</Text>
          <Text style={[styles.col3, styles.th]}>Vendor</Text>
          <Text style={[styles.col4, styles.th]}>Tech</Text>
          <Text style={[styles.col5, styles.th]}>Next Due</Text>
        </View>

        {records.map((r: { id: string; hood_name?: string; cleaned_at: string; vendor_name: string; tech_name: string; next_due_at: string }) => (
          <View key={r.id} style={styles.tableRow}>
            <Text style={[styles.col1, styles.td]}>{r.hood_name ?? '—'}</Text>
            <Text style={[styles.col2, styles.td]}>{formatDate(r.cleaned_at)}</Text>
            <Text style={[styles.col3, styles.td]}>{r.vendor_name}</Text>
            <Text style={[styles.col4, styles.td]}>{r.tech_name}</Text>
            <Text style={[styles.col5, styles.td]}>{formatDate(r.next_due_at)}</Text>
          </View>
        ))}

        <Text style={styles.footer}>
          Hood Cleaning Log · Technyder · CONFIDENTIAL · {records.length} records
        </Text>
      </Page>
    </Document>
  )

  const buffer = await renderToBuffer(<AuditDocument />)
  const uint8 = new Uint8Array(buffer)

  return new NextResponse(uint8, {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': `attachment; filename="audit-${location_id}-${date_to}.pdf"`,
    },
  })
}
