'use client'
import { useEffect, useRef, useState } from 'react'
import { useParams } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import SignaturePad from 'react-signature-canvas'

type Step = 'loading' | 'not_found' | 'form' | 'submitting' | 'success' | 'error'

export default function VendorFormPage() {
  const { qrCode } = useParams<{ qrCode: string }>()
  const [step, setStep] = useState<Step>('loading')
  const [hood, setHood] = useState<{ id: string; name: string; location: string; frequency_days: number } | null>(null)
  const [form, setForm] = useState({ vendor_name: '', tech_name: '', notes: '' })
  const [beforePhoto, setBeforePhoto] = useState<File | null>(null)
  const [afterPhoto, setAfterPhoto] = useState<File | null>(null)
  const sigRef = useRef<SignaturePad>(null)
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    async function loadHood() {
      if (qrCode === 'demo') {
        setHood({ id: 'demo', name: 'Main Cook Line Hood #1', location: 'Demo Restaurant', frequency_days: 90 })
        setStep('form')
        return
      }
      const supabase = createClient()
      const { data } = await supabase
        .from('hoods')
        .select('id, name, frequency_days, locations(name)')
        .eq('qr_code', qrCode)
        .eq('active', true)
        .single()

      if (!data) { setStep('not_found'); return }
      setHood({
        id: data.id,
        name: data.name,
        frequency_days: data.frequency_days,
        location: (data.locations as unknown as { name: string } | null)?.name ?? '',
      })
      setStep('form')
    }
    loadHood()
  }, [qrCode])

  function update(k: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm(f => ({ ...f, [k]: e.target.value }))
  }

  async function uploadPhoto(file: File, path: string): Promise<string | null> {
    const supabase = createClient()
    const { data, error } = await supabase.storage
      .from('cleaning-photos')
      .upload(path, file, { upsert: true })
    if (error) return null
    const { data: { publicUrl } } = supabase.storage.from('cleaning-photos').getPublicUrl(data.path)
    return publicUrl
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!hood || hood.id === 'demo') { setStep('success'); return }
    if (!form.vendor_name || !form.tech_name) return

    const sig = sigRef.current
    if (!sig || sig.isEmpty()) { setErrorMsg('Please provide a signature.'); return }

    setStep('submitting')
    const supabase = createClient()

    const ts = Date.now()
    const [beforeUrl, afterUrl] = await Promise.all([
      beforePhoto ? uploadPhoto(beforePhoto, `${hood.id}/${ts}-before.jpg`) : Promise.resolve(null),
      afterPhoto ? uploadPhoto(afterPhoto, `${hood.id}/${ts}-after.jpg`) : Promise.resolve(null),
    ])

    // Upload signature as base64 data URL — store inline for simplicity
    const sigDataUrl = sig.toDataURL('image/png')

    const { error } = await supabase.from('cleaning_records').insert({
      hood_id: hood.id,
      vendor_name: form.vendor_name,
      tech_name: form.tech_name,
      notes: form.notes || null,
      cleaned_at: new Date().toISOString(),
      before_photo_url: beforeUrl,
      after_photo_url: afterUrl,
      signature_url: sigDataUrl,
    })

    if (error) { setErrorMsg(error.message); setStep('error'); return }
    setStep('success')
  }

  if (step === 'loading') return (
    <div className="min-h-screen flex items-center justify-center text-zinc-400">Loading…</div>
  )

  if (step === 'not_found') return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center">
        <p className="text-3xl mb-3">🔍</p>
        <h1 className="font-bold text-lg">Hood not found</h1>
        <p className="text-sm text-zinc-500 mt-1">This QR code may be invalid or the hood has been removed.</p>
      </div>
    </div>
  )

  if (step === 'success') return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center text-3xl mx-auto mb-4">✓</div>
        <h1 className="font-bold text-xl text-green-700">Cleaning recorded!</h1>
        <p className="text-sm text-zinc-500 mt-2">
          <strong>{hood?.name}</strong> at <strong>{hood?.location}</strong>
        </p>
        <p className="text-xs text-zinc-400 mt-4">Next service due in {hood?.frequency_days} days.</p>
        <p className="text-xs text-zinc-300 mt-6">Hood Cleaning Log · Technyder</p>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-zinc-50 px-4 py-8">
      <div className="max-w-md mx-auto">
        <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
          <div className="mb-5">
            <p className="text-xs text-zinc-400 uppercase tracking-wide font-semibold">Hood Cleaning Record</p>
            <h1 className="text-lg font-bold mt-1">{hood?.name}</h1>
            <p className="text-sm text-zinc-500">{hood?.location}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Company name *</label>
              <input required value={form.vendor_name} onChange={update('vendor_name')}
                className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                placeholder="ABC Hood Cleaning Co." />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Technician name *</label>
              <input required value={form.tech_name} onChange={update('tech_name')}
                className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                placeholder="John Smith" />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Notes (optional)</label>
              <textarea value={form.notes} onChange={update('notes')} rows={2}
                className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
                placeholder="Grease level, deficiencies found, etc." />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">Before photo</label>
                <input type="file" accept="image/*" capture="environment"
                  onChange={e => setBeforePhoto(e.target.files?.[0] ?? null)}
                  className="w-full text-xs text-zinc-500" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">After photo</label>
                <input type="file" accept="image/*" capture="environment"
                  onChange={e => setAfterPhoto(e.target.files?.[0] ?? null)}
                  className="w-full text-xs text-zinc-500" />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Technician signature *</label>
              <div className="border border-zinc-200 rounded-lg overflow-hidden bg-white">
                <SignaturePad
                  ref={sigRef}
                  canvasProps={{ className: 'w-full', height: 120, style: { touchAction: 'none' } }}
                />
              </div>
              <button type="button" onClick={() => sigRef.current?.clear()}
                className="text-xs text-zinc-400 hover:text-zinc-700 mt-1">
                Clear signature
              </button>
            </div>

            {errorMsg && <p className="text-sm text-red-600">{errorMsg}</p>}

            <button
              type="submit"
              disabled={step === 'submitting'}
              className="w-full bg-zinc-900 text-white py-3 rounded-lg font-semibold text-sm hover:bg-zinc-700 disabled:opacity-50"
            >
              {step === 'submitting' ? 'Submitting…' : 'Submit cleaning record'}
            </button>
          </form>

          <p className="text-xs text-center text-zinc-300 mt-4">Hood Cleaning Log · Technyder</p>
        </div>
      </div>
    </div>
  )
}
