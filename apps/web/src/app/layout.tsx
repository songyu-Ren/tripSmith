import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'TripSmith | 旅行方案生成',
  description: '输入出行条件，生成 3 套可解释旅行方案'
}

export default function RootLayout({
  children
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="min-h-screen">
          <header className="border-b" style={{ borderColor: 'var(--ts-border)' }}>
            <div className="ts-container flex items-center justify-between py-4">
              <div className="text-sm font-semibold tracking-wide">TripSmith</div>
              <div className="text-xs ts-muted">旅行规划 Copilot（MVP）</div>
            </div>
          </header>
          <main className="ts-container py-6">{children}</main>
        </div>
      </body>
    </html>
  )
}

