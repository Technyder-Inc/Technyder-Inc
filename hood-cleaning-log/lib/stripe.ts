import Stripe from 'stripe'

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2026-04-22.dahlia',
})

export const PRICE_PER_LOCATION = 8900 // $89.00 in cents

export async function createCheckoutSession(tenantId: string, locationCount: number, successUrl: string, cancelUrl: string) {
  return stripe.checkout.sessions.create({
    mode: 'subscription',
    line_items: [{
      price_data: {
        currency: 'usd',
        product_data: { name: 'Hood Cleaning Log — Per Location' },
        unit_amount: PRICE_PER_LOCATION,
        recurring: { interval: 'month' },
      },
      quantity: locationCount,
    }],
    success_url: successUrl,
    cancel_url: cancelUrl,
    metadata: { tenant_id: tenantId },
  })
}

export async function createBillingPortalSession(customerId: string, returnUrl: string) {
  return stripe.billingPortal.sessions.create({
    customer: customerId,
    return_url: returnUrl,
  })
}
