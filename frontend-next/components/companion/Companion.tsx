"use client"

// 咕咕嘎嘎学伴悬浮组件：右下角形象 + 情绪动作 + 口头禅气泡 + 角色切换。

import { useState } from "react"
import { Volume2, VolumeX, RefreshCw } from "lucide-react"

import { getCharacterAssetUrl } from "@/lib/api"
import { useCompanion, type CompanionMood } from "./CompanionContext"

/** 各情绪对应的动作素材回退顺序（某动作缺素材时回退到 idle） */
function pickMotion(mood: CompanionMood, motionAssets: Record<string, boolean>): string | null {
  if (motionAssets[mood]) return mood
  if (motionAssets.idle) return "idle"
  return null
}

export function Companion() {
  const { character, characters, mood, bubble, selectCharacter, speaking, stopSpeaking } = useCompanion()
  const [imgError, setImgError] = useState(false)

  if (!character) return null

  const motion = pickMotion(mood, character.motion_assets)
  const showImage = motion && !imgError
  const assetUrl = motion ? getCharacterAssetUrl(character.id, motion) : null

  return (
    <div className="pointer-events-none fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
      {/* 口头禅气泡 */}
      {bubble && (
        <div className="pointer-events-auto max-w-[240px] rounded-2xl rounded-br-sm border bg-card px-4 py-2.5 text-sm shadow-lg">
          <span className="mr-1 font-medium text-primary">{character.name}：</span>
          {bubble}
        </div>
      )}

      <div className="pointer-events-auto flex flex-col items-center gap-1.5">
        {/* 形象：有素材显示图，无素材显示占位 */}
        <div
          className={[
            "flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border-2 bg-card shadow-lg transition-transform",
            mood === "happy" || mood === "celebrate" ? "scale-110 border-green-400" : "border-primary/30",
            mood === "loading" ? "animate-spin-slow" : "",
          ].join(" ")}
          title={`${character.name}（${mood}）`}
        >
          {showImage && assetUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={assetUrl}
              alt={character.name}
              className="h-full w-full object-cover"
              onError={() => setImgError(true)}
            />
          ) : (
            <PenguinPlaceholder mood={mood} name={character.name} hasAssets={character.has_assets} />
          )}
        </div>

        {/* 控制条：停止播报 / 切换角色 */}
        <div className="flex items-center gap-1 rounded-full border bg-card/90 px-2 py-1 shadow">
          {speaking ? (
            <button
              onClick={stopSpeaking}
              className="text-primary hover:opacity-70"
              title="停止播报"
            >
              <VolumeX className="h-3.5 w-3.5" />
            </button>
          ) : (
            <Volume2 className="h-3.5 w-3.5 text-muted-foreground" />
          )}
          <span className="text-[10px] text-muted-foreground">{character.name}</span>
          {characters.length > 1 && (
            <button
              onClick={() => {
                const idx = characters.findIndex((c) => c.id === character.id)
                const next = characters[(idx + 1) % characters.length]
                selectCharacter(next.id)
              }}
              className="text-muted-foreground hover:text-primary"
              title="切换学伴"
            >
              <RefreshCw className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/** 无素材时的企鹅占位（纯 CSS/Emoji，简洁可爱） */
function PenguinPlaceholder({
  mood,
  name,
  hasAssets,
}: {
  mood: CompanionMood
  name: string
  hasAssets: boolean
}) {
  const face =
    mood === "happy" || mood === "celebrate" ? "😄" : mood === "confused" ? "🤔" : mood === "loading" ? "🐧" : "🐧"
  return (
    <div className="flex h-full w-full flex-col items-center justify-center bg-gradient-to-b from-sky-100 to-sky-200 dark:from-sky-950 dark:to-sky-900">
      <span
        className={[
          "text-4xl transition-transform",
          mood === "idle" ? "animate-bounce-subtle" : "",
          mood === "happy" || mood === "celebrate" ? "animate-bounce" : "",
        ].join(" ")}
      >
        {face}
      </span>
      {!hasAssets && (
        <span className="mt-0.5 px-1 text-center text-[8px] leading-tight text-muted-foreground">
          放入素材显示形象
        </span>
      )}
    </div>
  )
}
