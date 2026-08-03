"use client"

// 咕咕嘎嘎学伴悬浮组件：可拖动形象 + 情绪动作 + 口头禅气泡 + 角色切换/收起。

import { useEffect, useRef, useState } from "react"
import { Minimize2, Volume2, VolumeX, RefreshCw } from "lucide-react"

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
  // 轮换序号：每次情绪变化 +1，附加到素材 URL，让后端重新随机选图（多张时轮换播放）
  const [variant, setVariant] = useState(0)
  // 收起状态（localStorage 记忆）：嫌遮挡时可收成小圆点
  const [minimized, setMinimized] = useState(false)
  // 可拖动位置（null = 默认右下角；拖动后记忆到 localStorage）
  const [pos, setPos] = useState<{ x: number; y: number } | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const dragStart = useRef<{ mx: number; my: number; ox: number; oy: number } | null>(null)
  const [dragging, setDragging] = useState(false)

  useEffect(() => {
    setVariant((v) => v + 1)
    setImgError(false) // 换动作时重置错误，允许新图加载
  }, [mood])

  useEffect(() => {
    if (typeof window === "undefined") return
    if (localStorage.getItem("companion.minimized") === "1") setMinimized(true)
    try {
      const saved = localStorage.getItem("companion.pos")
      if (saved) setPos(JSON.parse(saved))
    } catch {
      /* 忽略损坏的坐标 */
    }
  }, [])

  const toggleMinimize = () => {
    setMinimized((m) => {
      const next = !m
      if (typeof window !== "undefined") {
        localStorage.setItem("companion.minimized", next ? "1" : "0")
      }
      return next
    })
  }

  // 拖动：按住形象移动整个学伴，松开记忆位置。限制在视口内。
  useEffect(() => {
    if (!dragging) return
    const onMove = (e: PointerEvent) => {
      const s = dragStart.current
      if (!s) return
      const w = containerRef.current?.offsetWidth ?? 100
      const h = containerRef.current?.offsetHeight ?? 130
      const x = Math.min(Math.max(0, s.ox + (e.clientX - s.mx)), window.innerWidth - w)
      const y = Math.min(Math.max(0, s.oy + (e.clientY - s.my)), window.innerHeight - h)
      setPos({ x, y })
    }
    const onUp = () => {
      setDragging(false)
      if (typeof window !== "undefined") {
        const p = containerRef.current?.getBoundingClientRect()
        if (p) localStorage.setItem("companion.pos", JSON.stringify({ x: p.left, y: p.top }))
      }
    }
    window.addEventListener("pointermove", onMove)
    window.addEventListener("pointerup", onUp)
    return () => {
      window.removeEventListener("pointermove", onMove)
      window.removeEventListener("pointerup", onUp)
    }
  }, [dragging])

  const startDrag = (e: React.PointerEvent) => {
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return
    dragStart.current = { mx: e.clientX, my: e.clientY, ox: rect.left, oy: rect.top }
    setDragging(true)
  }

  if (!character) return null

  const motion = pickMotion(mood, character.motion_assets)
  const showImage = motion && !imgError
  const assetUrl = motion ? `${getCharacterAssetUrl(character.id, motion)}?v=${variant}` : null
  const posStyle = pos ? { left: pos.x, top: pos.y } : undefined
  const posClass = pos ? "" : "bottom-6 right-6"
  // 拖动时全局 grabbing 光标
  const grabClass = dragging ? "cursor-grabbing" : ""

  // 收起态：只显示小圆头像，点击展开
  if (minimized) {
    return (
      <div
        ref={containerRef}
        className={`pointer-events-auto fixed z-50 ${posClass}`}
        style={posStyle}
      >
        <button
          onClick={toggleMinimize}
          className="flex h-12 w-12 items-center justify-center overflow-hidden rounded-full border-2 border-primary/30 bg-card shadow-lg transition-transform hover:scale-105"
          title="展开学伴"
        >
          {showImage && assetUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={assetUrl} alt={character.name} className="h-full w-full object-cover" />
          ) : (
            <PenguinPlaceholder mood={mood} name={character.name} hasAssets={character.has_assets} />
          )}
        </button>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={`pointer-events-none fixed z-50 flex flex-col items-end gap-2 ${posClass} ${grabClass}`}
      style={posStyle}
    >
      {/* 口头禅气泡 */}
      {bubble && (
        <div className="pointer-events-auto max-w-[240px] rounded-2xl rounded-br-sm border bg-card px-4 py-2.5 text-sm shadow-lg">
          <span className="mr-1 font-medium text-primary">{character.name}：</span>
          {bubble}
        </div>
      )}

      <div className="pointer-events-auto flex flex-col items-center gap-1.5">
        {/* 形象：可拖动手柄；有素材显示图，无素材显示占位 */}
        <div
          onPointerDown={startDrag}
          className={[
            "flex h-24 w-24 cursor-grab select-none items-center justify-center overflow-hidden rounded-full border-2 bg-card shadow-lg transition-transform active:cursor-grabbing",
            mood === "happy" || mood === "celebrate" ? "scale-110 border-green-400" : "border-primary/30",
            mood === "loading" ? "animate-spin-slow" : "",
          ].join(" ")}
          title={`${character.name}（${mood}）· 可拖动`}
        >
          {showImage && assetUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={assetUrl}
              alt={character.name}
              className="h-full w-full object-cover pointer-events-none"
              draggable={false}
              onError={() => setImgError(true)}
            />
          ) : (
            <PenguinPlaceholder mood={mood} name={character.name} hasAssets={character.has_assets} />
          )}
        </div>

        {/* 控制条：停止播报 / 切换角色 / 收起 */}
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
          <button
            onClick={toggleMinimize}
            className="text-muted-foreground hover:text-primary"
            title="收起学伴"
          >
            <Minimize2 className="h-3 w-3" />
          </button>
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
