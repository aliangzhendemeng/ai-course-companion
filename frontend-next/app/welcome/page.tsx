"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { GraduationCap, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useSettings } from "@/hooks/use-api"

export default function WelcomePage() {
  const router = useRouter()
  const { data: settings, isLoading } = useSettings()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (settings?.is_configured) {
    router.replace("/courses")
    return null
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-background to-muted p-6">
      <Card className="w-full max-w-xl">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg">
            <GraduationCap className="h-8 w-8" />
          </div>
          <CardTitle className="text-2xl">欢迎来到 AI 慕课学伴</CardTitle>
          <CardDescription className="text-base">
            上传课程视频，即可通过 AI 进行知识问答和学习。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="rounded-lg bg-muted p-4 text-sm leading-relaxed text-muted-foreground">
            <p>使用前需要配置 AI 模型 API Key。推荐使用 DeepSeek，成本和效果都比较适合学生使用。</p>
            <ul className="mt-2 list-inside list-disc space-y-1">
              <li>支持 DeepSeek、Gemini、Claude 等多种模型</li>
              <li>可以只填一个通用 Key，所有模型自动复用</li>
              <li>配置保存在本地，不会上传到任何服务器</li>
            </ul>
          </div>
          <Button asChild size="lg" className="w-full">
            <Link href="/settings">去配置模型</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
