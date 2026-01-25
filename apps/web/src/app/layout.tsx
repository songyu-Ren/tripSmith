import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'TripSmith',
  description: '开源旅行规划 Copilot'
}

export default function RootLayout({
  children
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="bg-zinc-950 text-zinc-100">
        <div className="min-h-screen">
          <header className="border-b border-zinc-800">
            <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
              <div className="text-sm font-semibold tracking-wide">TripSmith</div>
              <div className="text-xs text-zinc-400">旅行规划 Copilot（MVP）</div>
            </div>
          </header>
          <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
        </div>
      </body>
    </html>
  )
}

