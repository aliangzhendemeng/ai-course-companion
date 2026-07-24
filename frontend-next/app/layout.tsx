import type { Metadata } from "next"
import "./globals.css"
import { Providers } from "./providers"
import { Sidebar } from "@/components/Sidebar"

export const metadata: Metadata = {
  title: "AI 慕课学伴",
  description: "AI 驱动的课程学习与知识问答平台",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="ml-64 flex-1 bg-background">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
