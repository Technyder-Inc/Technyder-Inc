'use client'
import { useState } from 'react'
import QRCode from 'qrcode'

interface Props { hoodId: string; hoodName: string; qrCode: string }

export function QrPrintButton({ hoodName, qrCode }: Props) {
  const [loading, setLoading] = useState(false)

  async function handlePrint() {
    setLoading(true)
    const vendorUrl = `${window.location.origin}/vendor/${qrCode}`
    const dataUrl = await QRCode.toDataURL(vendorUrl, { width: 300, margin: 2 })

    const win = window.open('', '_blank')
    if (!win) { setLoading(false); return }

    win.document.write(`
      <!DOCTYPE html>
      <html>
        <head><title>QR Sticker — ${hoodName}</title>
        <style>
          body { font-family: sans-serif; text-align: center; padding: 40px; }
          img { width: 200px; height: 200px; }
          h2 { margin: 16px 0 4px; font-size: 18px; }
          p { color: #666; font-size: 13px; margin: 0; }
          .border { border: 2px dashed #ccc; padding: 24px; display: inline-block; border-radius: 12px; }
        </style>
        </head>
        <body>
          <div class="border">
            <img src="${dataUrl}" alt="QR Code" />
            <h2>${hoodName}</h2>
            <p>Scan to record cleaning</p>
            <p style="font-size:10px;margin-top:8px;color:#aaa">Hood Cleaning Log · Technyder</p>
          </div>
          <script>window.print(); window.close();<\/script>
        </body>
      </html>
    `)
    win.document.close()
    setLoading(false)
  }

  return (
    <button
      onClick={handlePrint}
      disabled={loading}
      className="text-xs border border-zinc-200 px-2 py-1 rounded hover:bg-zinc-50 disabled:opacity-50"
    >
      {loading ? 'Generating…' : 'Print QR'}
    </button>
  )
}
