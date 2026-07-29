"use client"

import { useRouter } from "next/navigation"
import { SettingsForm } from "@/components/SettingsForm"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useSaveSettings, useSettings } from "@/hooks/use-api"
import type { Settings } from "@/lib/api"

export default function SettingsPage() {
  const router = useRouter()
  const { data: settings, isLoading } = useSettings()
  const save = useSaveSettings()

  const handleSubmit = (values: Partial<Settings>) => {
    save.mutate(values, {
      onSuccess: () => {
        if (!settings?.is_configured) {
          router.push("/courses")
        }
      },
    })
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
        <CardContent>
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
