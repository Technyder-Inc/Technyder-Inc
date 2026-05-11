export type SubscriptionStatus = 'trialing' | 'active' | 'past_due' | 'canceled'
export type UserRole = 'owner' | 'manager' | 'viewer'

export interface Tenant {
  id: string
  name: string
  slug: string
  stripe_customer_id: string | null
  stripe_subscription_id: string | null
  subscription_status: SubscriptionStatus
  trial_ends_at: string
  created_at: string
  updated_at: string
}

export interface UserProfile {
  id: string
  tenant_id: string
  full_name: string | null
  role: UserRole
  phone: string | null
  created_at: string
}

export interface Location {
  id: string
  tenant_id: string
  name: string
  address: string | null
  city: string | null
  state: string | null
  zip: string | null
  phone: string | null
  contact_name: string | null
  contact_email: string | null
  active: boolean
  created_at: string
  updated_at: string
}

export interface Vendor {
  id: string
  tenant_id: string
  name: string
  phone: string | null
  email: string | null
  license_number: string | null
  active: boolean
  created_at: string
}

export interface Hood {
  id: string
  tenant_id: string
  location_id: string
  name: string
  description: string | null
  frequency_days: number
  qr_code: string
  active: boolean
  created_at: string
  updated_at: string
  // joined
  last_cleaned_at?: string | null
  next_due_at?: string | null
  status?: HoodStatus
}

export type HoodStatus = 'green' | 'yellow' | 'red' | 'unknown'

export interface CleaningRecord {
  id: string
  tenant_id: string
  hood_id: string
  vendor_id: string | null
  vendor_name: string
  tech_name: string
  cleaned_at: string
  notes: string | null
  before_photo_url: string | null
  after_photo_url: string | null
  signature_url: string | null
  next_due_at: string
  created_at: string
}

export interface NotificationSetting {
  id: string
  tenant_id: string
  location_id: string | null
  hood_id: string | null
  phone: string | null
  email: string | null
  notify_days_before: number[]
  enabled: boolean
}

export interface AuditPacket {
  id: string
  tenant_id: string
  location_id: string | null
  generated_by: string | null
  date_from: string
  date_to: string
  pdf_url: string | null
  share_token: string
  created_at: string
}

// Computed hood status based on next_due_at
export function computeHoodStatus(nextDueAt: string | null): HoodStatus {
  if (!nextDueAt) return 'unknown'
  const now = new Date()
  const due = new Date(nextDueAt)
  const daysUntilDue = Math.floor((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  if (daysUntilDue < 0) return 'red'
  if (daysUntilDue <= 14) return 'yellow'
  return 'green'
}
