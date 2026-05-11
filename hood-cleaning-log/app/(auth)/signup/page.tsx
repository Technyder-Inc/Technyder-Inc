'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'

export default function SignupPage() {
  const router = useRouter()
  const [form, setForm] = useState({ name: '', restaurantName: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function update(k: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, [k]: e.target.value }))
  }

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    const supabase = createClient()
    const { error } = await supabase.auth.signUp({
      email: form.email,
      password: form.password,
      options: {
        data: {
          full_name: form.name,
          restaurant_name: form.restaurantName,
        },
      },
    })
    if (error) { setError(error.message); setLoading(false); return }
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50 px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-zinc-200 p-8 shadow-sm">
        <h1 className="text-2xl font-bold mb-1">Start your free trial</h1>
        <p className="text-sm text-zinc-500 mb-6">14 days free · No credit card required</p>
        <form onSubmit={handleSignup} className="space-y-4">
          {[
            { label: 'Your name', key: 'name' as const, type: 'text', auto: 'name' },
            { label: 'Restaurant / group name', key: 'restaurantName' as const, type: 'text', auto: 'organization' },
            { label: 'Work email', key: 'email' as const, type: 'email', auto: 'email' },
            { label: 'Password', key: 'password' as const, type: 'password', auto: 'new-password' },
          ].map(({ label, key, type, auto }) => (
            <div key={key}>
              <label className="block text-sm font-medium mb-1">{label}</label>
              <input
                type={type} required autoComplete={auto}
                value={form[key]} onChange={update(key)}
                className="w-full border border-zinc-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900"
              />
            </div>
          ))}
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit" disabled={loading}
            className="w-full bg-zinc-900 text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-zinc-700 disabled:opacity-50"
          >
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        <p className="text-xs text-zinc-400 text-center mt-4">$89/month per location after trial</p>
        <p className="text-sm text-zinc-500 text-center mt-3">
          Have an account?{' '}
          <Link href="/login" className="text-zinc-900 font-medium hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
