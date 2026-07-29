"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { CheckCircle2, Loader2, RefreshCw } from "lucide-react"

import { SettingsForm } from "@/components/SettingsForm"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useSaveSettings, useSettings } from "@/hooks/use-api"
import type { Settings } from "@/lib/api"

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"

export default function SettingsPage() {
  const router = useRouter()
  const { data: settings, isLoading } = useSettings()
  const save = useSaveSettings()
  const [savedAt, setSavedAt] = useState<number | null>(null)
  const [restarting, setRestarting] = useState(false)

  const handleSubmit = (values: Partial<Settings>) => {
    save.mutate(values, {
      onSuccess: () => {
        setSavedAt(Date.now())
        // 首次配置成功后直接进入课程库
        if (!settings?.is_configured) {
          router.push("/courses")
        }
      },
    })
  }

  const handleRestart = async () => {
    setRestarting(true)
    try {
      await fetch(`${API_BASE}/api/settings/restart`, { method: "POST" })
    } catch {
      // 重启会断开连接，忽略错误
    }
    // 等待后端重新拉起
    setTimeout(() => setRestarting(false), 5000)
  }

  return (
    <div className="mx-auto max-w-2xl p-6">
      <Card>
        <CardHeader>
          <CardTitle>模型与 API 配置</CardTitle>
          <CardDescription>
            配置 AI 模型和 API Key。配置保存在本地 .env 文件中。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {savedAt && (
            <div className="flex items-start gap-2 rounded-lg bg-green-50 p-3 text-sm text-green-800 dark:bg-green-950 dark:text-green-200">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              <div className="flex-1">
                <p className="font-medium">配置已保存</p>
                <p className="mt-0.5 text-green-700 dark:text-green-300">
                  模型/Key 的修改需要重启后端才能完全生效。
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2 border-green-300 bg-transparent hover:bg-green-100 dark:border-green-800 dark:hover:bg-green-900"
                  onClick={handleRestart}
                  disabled={restarting}
                >
                  {restarting ? (
                    <>
                      <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
                      正在重启…
                    </>
                  ) : (
                    <>
                      <RefreshCw className="mr-1 h-3.5 w-3.5" />
                      重启后端使配置生效
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {isLoading ? (
            <div className="h-64 animate-pulse rounded-lg bg-muted" />
          ) : (
            <SettingsForm
              initial={settings}
              onSubmit={handleSubmit}
              isLoading={save.isPending}
              submitLabel="保存配置"
              showRestartHint
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
