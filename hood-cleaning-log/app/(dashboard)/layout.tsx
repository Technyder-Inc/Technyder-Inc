import Link from 'next/link'
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top nav */}
      <header className="bg-white border-b border-zinc-100 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
        <Link href="/dashboard" className="font-bold text-base tracking-tight">Hood Log</Link>
        <nav className="hidden sm:flex gap-6 text-sm text-zinc-600">
          <Link href="/dashboard" className="hover:text-zinc-900">Locations</Link>
          <Link href="/audit" className="hover:text-zinc-900">Audit Packets</Link>
          <Link href="/vendors" className="hover:text-zinc-900">Vendors</Link>
          <Link href="/settings" className="hover:text-zinc-900">Settings</Link>
        </nav>
        <form action="/api/auth/signout" method="post">
          <button className="text-xs text-zinc-400 hover:text-zinc-700">Sign out</button>
        </form>
      </header>

      {/* Page content */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6">
        {children}
      </main>

      {/* Mobile bottom nav */}
      <nav className="sm:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-zinc-100 flex justify-around py-2 z-10">
        {[
          { href: '/dashboard', label: 'Locations', icon: '🏠' },
          { href: '/audit', label: 'Audit', icon: '📄' },
          { href: '/vendors', label: 'Vendors', icon: '🚛' },
          { href: '/settings', label: 'Settings', icon: '⚙️' },
        ].map(({ href, label, icon }) => (
          <Link key={href} href={href} className="flex flex-col items-center gap-0.5 text-zinc-500 hover:text-zinc-900 text-xs px-3 py-1">
            <span className="text-lg leading-none">{icon}</span>
            {label}
          </Link>
        ))}
      </nav>
    </div>
  )
}
