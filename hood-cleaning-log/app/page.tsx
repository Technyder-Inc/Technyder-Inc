import Link from 'next/link'

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-zinc-100">
        <span className="font-bold text-lg tracking-tight">Hood Cleaning Log</span>
        <div className="flex gap-3">
          <Link href="/login" className="text-sm text-zinc-600 hover:text-zinc-900 px-4 py-2">Log in</Link>
          <Link href="/signup" className="text-sm bg-zinc-900 text-white px-4 py-2 rounded-lg hover:bg-zinc-700">
            Start free trial
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-block bg-red-50 text-red-700 text-xs font-semibold px-3 py-1 rounded-full mb-6">
          NFPA-96 Compliance Made Simple
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-zinc-900 leading-tight mb-6">
          Never fail a hood cleaning audit again
        </h1>
        <p className="text-lg text-zinc-500 mb-8 max-w-xl mx-auto">
          Vendor scans a QR sticker, signs on glass, and your kitchen gets a green check.
          Export a 3-year audit packet in seconds — not minutes of digging through paper.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link href="/signup" className="bg-zinc-900 text-white px-6 py-3 rounded-lg font-semibold hover:bg-zinc-700">
            Start 14-day free trial
          </Link>
          <Link href="/vendor/demo" className="border border-zinc-200 text-zinc-700 px-6 py-3 rounded-lg font-semibold hover:bg-zinc-50">
            See vendor form demo
          </Link>
        </div>
        <p className="text-xs text-zinc-400 mt-4">$89/month per location · No annual contract · Self-serve</p>
      </section>

      {/* Social proof */}
      <section className="max-w-2xl mx-auto px-6 py-10">
        <div className="bg-red-50 border border-red-100 rounded-xl p-6">
          <p className="text-sm text-red-800 italic">
            &ldquo;Insurance dropped me because I couldn&apos;t produce hood cleaning records from 14 months ago.&rdquo;
          </p>
          <p className="text-xs text-red-500 mt-2">— r/KitchenConfidential, March 2026</p>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-3xl mx-auto px-6 py-12">
        <h2 className="text-2xl font-bold text-center mb-10">How it works</h2>
        <div className="grid sm:grid-cols-3 gap-8">
          {[
            { step: '1', title: 'Vendor scans QR', desc: 'Each hood has a unique QR sticker. Vendor scans it, fills the form, adds photos, and signs on their phone.' },
            { step: '2', title: 'Manager sees green', desc: 'Your location board shows green / yellow / red status for every hood. Get SMS alerts before the 90-day window lapses.' },
            { step: '3', title: 'Export audit packet', desc: 'One tap generates a PDF with the full 3-year history — ready for fire marshal, insurance carrier, or health inspection.' },
          ].map(({ step, title, desc }) => (
            <div key={step} className="text-center">
              <div className="w-10 h-10 bg-zinc-900 text-white rounded-full flex items-center justify-center font-bold mx-auto mb-3">{step}</div>
              <h3 className="font-semibold mb-2">{title}</h3>
              <p className="text-sm text-zinc-500">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-sm mx-auto px-6 py-12 text-center">
        <h2 className="text-2xl font-bold mb-8">Simple pricing</h2>
        <div className="border border-zinc-200 rounded-2xl p-8 shadow-sm">
          <p className="text-4xl font-bold">$89<span className="text-lg font-normal text-zinc-400">/mo</span></p>
          <p className="text-sm text-zinc-500 mt-1">per location</p>
          <ul className="text-sm text-zinc-600 mt-6 space-y-2 text-left">
            {['Unlimited hoods per location', 'Unlimited vendor form submissions', 'SMS reminders', 'PDF audit exports', '3-year record history', 'Multi-location dashboard'].map(f => (
              <li key={f} className="flex gap-2"><span className="text-green-500">✓</span>{f}</li>
            ))}
          </ul>
          <Link href="/signup" className="block mt-8 bg-zinc-900 text-white px-6 py-3 rounded-lg font-semibold hover:bg-zinc-700">
            Start free trial
          </Link>
        </div>
      </section>

      <footer className="text-center text-xs text-zinc-400 py-8 border-t border-zinc-100">
        © {new Date().getFullYear()} Technyder · Hood Cleaning Log
      </footer>
    </main>
  )
}
