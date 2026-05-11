import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | null | undefined) {
  if (!date) return 'Never'
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function daysUntil(date: string | null | undefined): number | null {
  if (!date) return null
  const now = new Date()
  const d = new Date(date)
  return Math.floor((d.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
}

export function daysAgo(date: string | null | undefined): number | null {
  if (!date) return null
  const now = new Date()
  const d = new Date(date)
  return Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24))
}
