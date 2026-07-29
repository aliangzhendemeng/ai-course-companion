"use client"

import { useState } from "react"
import { Loader2, Eye, EyeOff } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import type { Settings } from "@/lib/api"

const MODEL_OPTIONS = [
  { value: "deepseek", label: "DeepSeek (推荐)" },
  { value: "gemini:gemini-1.5-pro", label: "Gemini 1.5 Pro" },
  { value: "gemini:gemini-1.5-flash", label: "Gemini 1.5 Flash" },
  { value: "claude:claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet" },
  { value: "claude:claude-3-haiku-20240307", label: "Claude 3 Haiku" },
]

interface SettingsFormProps {
  initial?: Partial<Settings>
  onSubmit: (values: Partial<Settings>) => void
  isLoading?: boolean
  submitLabel?: string
  showRestartHint?: boolean
  showMainKey?: boolean
}

export function SettingsForm({
  initial,
  onSubmit,
  isLoading,
  submitLabel = "保存配置",
  showRestartHint,
  showMainKey,
}: SettingsFormProps) {
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({})
  const [values, setValues] = useState({
    chat_model: initial?.chat_model || "deepseek",
    chat_api_key: initial?.chat_api_key || "",
    summary_model: initial?.summary_model || "deepseek",
    summary_api_key: initial?.summary_api_key || "",
    vision_model: initial?.vision_model || "deepseek",
    vision_api_key: initial?.vision_api_key || "",
    enable_vision: initial?.enable_vision ?? false,
    main_api_key: initial?.main_api_key || "",
  })

  const toggleKey = (key: string) =>
    setShowKeys((prev) => ({ ...prev, [key]: !prev[key] }))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload: Partial<Settings> = {
      chat_model: values.chat_model,
      chat_api_key: values.chat_api_key,
      summary_model: values.summary_model,
      summary_api_key: values.summary_api_key,
      vision_model: values.vision_model,
      vision_api_key: values.vision_api_key,
      enable_vision: values.enable_vision,
    }
    if (showMainKey && values.main_api_key) {
      payload.main_api_key = values.main_api_key
    }
    onSubmit(payload)
  }

  const renderKeyField = (label: string, key: "chat_api_key" | "summary_api_key" | "vision_api_key" | "main_api_key", placeholder: string) => (
    <div className="space-y-2">
      <Label htmlFor={key}>{label}</Label>
      <div className="relative">
        <Input
          id={key}
          type={showKeys[key] ? "text" : "password"}
          value={values[key]}
          onChange={(e) => setValues((v) => ({ ...v, [key]: e.target.value }))}
          placeholder={placeholder}
          className="pr-10"
        />
        <button
          type="button"
          onClick={() => toggleKey(key)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
        >
          {showKeys[key] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </div>
    </div>
  )

  const renderModelSelect = (label: string, key: "chat_model" | "summary_model" | "vision_model") => (
    <div className="space-y-2">
      <Label htmlFor={key}>{label}</Label>
      <Select
        value={values[key]}
        onValueChange={(value) => setValues((v) => ({ ...v, [key]: value }))}
      >
        <SelectTrigger id={key}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {MODEL_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {showMainKey && (
        <div className="space-y-2">
          <Label htmlFor="main_api_key">通用 API Key（可选）</Label>
          <div className="relative">
            <Input
              id="main_api_key"
              type={showKeys.main_api_key ? "text" : "password"}
              value={values.main_api_key}
              onChange={(e) => setValues((v) => ({ ...v, main_api_key: e.target.value }))}
              placeholder="填一个 Key，所有模型自动使用"
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => toggleKey("main_api_key")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              {showKeys.main_api_key ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>
      )}

      <div className="space-y-4 rounded-lg border border-border p-4">
        <h3 className="text-sm font-semibold">问答模型</h3>
        {renderModelSelect("模型", "chat_model")}
        {renderKeyField("API Key", "chat_api_key", "输入问答模型 API Key")}
      </div>

      <div className="space-y-4 rounded-lg border border-border p-4">
        <h3 className="text-sm font-semibold">总结模型</h3>
        {renderModelSelect("模型", "summary_model")}
        {renderKeyField("API Key", "summary_api_key", "输入总结模型 API Key")}
      </div>

      <div className="space-y-4 rounded-lg border border-border p-4">
        <h3 className="text-sm font-semibold">视觉模型（课件识别）</h3>
        {renderModelSelect("模型", "vision_model")}
        {renderKeyField("API Key", "vision_api_key", "输入视觉模型 API Key")}
        <div className="flex items-center gap-3">
          <Switch
            id="enable_vision"
            checked={values.enable_vision}
            onCheckedChange={(checked) => setValues((v) => ({ ...v, enable_vision: checked }))}
          />
          <Label htmlFor="enable_vision" className="cursor-pointer">
            启用视觉识别（识别 PPT、板书等课件内容）
          </Label>
        </div>
      </div>

      {showRestartHint && (
        <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-200">
          保存配置后需要重启后端服务才能完全生效。
        </div>
      )}

      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {submitLabel}
      </Button>
    </form>
  )
}
