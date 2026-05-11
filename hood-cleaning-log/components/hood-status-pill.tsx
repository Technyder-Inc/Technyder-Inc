'use client'
import { Badge } from '@/components/ui/badge'
import { type HoodStatus } from '@/lib/supabase/types'

interface HoodStatusPillProps {
  status: HoodStatus
  nextDueAt?: string | null
}

export function HoodStatusPill({ status, nextDueAt }: HoodStatusPillProps) {
  const label = {
    green: 'OK',
    yellow: 'Due Soon',
    red: 'OVERDUE',
    unknown: 'No Record',
  }[status]

  const variant = status === 'green' ? 'green'
    : status === 'yellow' ? 'yellow'
    : status === 'red' ? 'red'
    : 'default'

  return (
    <Badge variant={variant as 'green' | 'yellow' | 'red' | 'default'}>
      {label}
    </Badge>
  )
}
