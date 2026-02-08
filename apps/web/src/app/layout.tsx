import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'TripSmith | Travel planning',
  description: 'Enter trip preferences and generate 3 explainable travel options'
}

export default function RootLayout({
  children
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <header className="border-b" style={{ borderColor: 'var(--ts-border)' }}>
            <div className="ts-container flex items-center justify-between py-4">
              <div className="text-sm font-semibold tracking-wide">TripSmith</div>
              <div className="text-xs ts-muted">Travel planning Copilot (MVP)</div>
            </div>
          </header>
          <main className="ts-container py-6">{children}</main>
        </div>
      </body>
    </html>
  )
}

