import type { Metadata } from "next"
import "./globals.css"
import { Providers } from "./providers"
import { Shell } from "@/components/Shell"

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
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <Providers>
          <Shell>{children}</Shell>
        </Providers>
      </body>
    </html>
  )
}
