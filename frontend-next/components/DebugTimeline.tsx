import { Type, ImageIcon, Clock } from "lucide-react"

import { ScrollArea } from "@/components/ui/scroll-area"
import { formatTimestamp } from "@/lib/timestamp"
import type { TranscriptDebug, FrameDebug } from "@/lib/api"

interface DebugTimelineProps {
  transcripts: TranscriptDebug[]
  frames: FrameDebug[]
  onSeek?: (timestamp: number) => void
}

type Side = "speech" | "frame"

interface TimelineItem {
  side: Side
  timestamp: number
  // speech
  text?: string
  // frame
  ocrText?: string | null
  visionDesc?: string | null
  image?: string | null
  thumbnail?: string | null
}

export function DebugTimeline({ transcripts, frames, onSeek }: DebugTimelineProps) {
  const items: TimelineItem[] = []

  for (const t of transcripts) {
    items.push({
      side: "speech",
      timestamp: t.start_time,
      text: t.text,
    })
  }
  for (const f of frames) {
    items.push({
      side: "frame",
      timestamp: f.timestamp,
      ocrText: f.ocr_text,
      visionDesc: f.vision_desc,
      image: f.image_path,
      thumbnail: f.thumbnail_path,
    })
  }

  items.sort((a, b) => a.timestamp - b.timestamp)

  return (
    <div className="flex h-full flex-col">
      <div className="mb-3 flex items-center justify-between border-b pb-2 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <Type className="h-3.5 w-3.5" /> 左：语音转写
        </span>
        <span className="flex items-center gap-1">
          <Clock className="h-3.5 w-3.5" /> 时间轴
        </span>
        <span className="flex items-center gap-1">
          <ImageIcon className="h-3.5 w-3.5" /> 右：课件帧图
        </span>
      </div>

      <ScrollArea className="flex-1">
        <div className="relative grid grid-cols-[1fr_auto_1fr] gap-x-4">
          {/* 中间时间轴线 */}
          <div className="pointer-events-none absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-border" />

          {items.length === 0 && (
            <div className="col-span-3 py-10 text-center text-sm text-muted-foreground">
              暂无时间轴数据。
            </div>
          )}

          {items.map((item, idx) =>
            item.side === "speech" ? (
              <SpeechRow key={`s-${idx}`} item={item} onSeek={onSeek} />
            ) : (
              <FrameRow key={`f-${idx}`} item={item} onSeek={onSeek} />
            )
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

function SpeechRow({ item, onSeek }: { item: TimelineItem; onSeek?: (t: number) => void }) {
  return (
    <>
      {/* 左：语音 */}
      <div className="flex justify-end py-1.5">
        <div className="max-w-full rounded-lg border bg-blue-50/40 p-2 text-sm dark:bg-blue-950/20">
          <p className="whitespace-pre-wrap text-foreground">{item.text}</p>
        </div>
      </div>
      {/* 中：时间轴节点 */}
      <div className="relative flex flex-col items-center justify-center py-1.5">
        <button
          onClick={() => onSeek?.(item.timestamp)}
          className="z-10 whitespace-nowrap rounded-full border bg-card px-1.5 py-0.5 text-[10px] font-medium text-accent hover:bg-accent hover:text-accent-foreground"
          title="跳转到此时间"
        >
          {formatTimestamp(item.timestamp)}
        </button>
      </div>
      {/* 右：占位 */}
      <div className="py-1.5" />
    </>
  )
}

function FrameRow({ item, onSeek }: { item: TimelineItem; onSeek?: (t: number) => void }) {
  return (
    <>
      {/* 左：占位 */}
      <div className="py-1.5" />
      {/* 中：时间轴节点 */}
      <div className="relative flex flex-col items-center justify-center py-1.5">
        <button
          onClick={() => onSeek?.(item.timestamp)}
          className="z-10 whitespace-nowrap rounded-full border bg-card px-1.5 py-0.5 text-[10px] font-medium text-accent hover:bg-accent hover:text-accent-foreground"
          title="跳转到此时间"
        >
          {formatTimestamp(item.timestamp)}
        </button>
      </div>
      {/* 右：帧图 */}
      <div className="flex justify-start py-1.5">
        <div className="max-w-full rounded-lg border bg-amber-50/40 p-2 dark:bg-amber-950/20">
          {(item.thumbnail || item.image) && (
            <img
              src={`http://localhost:8000${item.thumbnail || item.image}`}
              alt="帧图"
              className="mb-1.5 max-h-32 rounded border object-contain"
            />
          )}
          {item.ocrText && (
            <p className="whitespace-pre-wrap text-xs text-foreground">
              <span className="font-medium text-muted-foreground">OCR：</span>
              {item.ocrText}
            </p>
          )}
          {item.visionDesc && (
            <p className="mt-1 whitespace-pre-wrap text-xs text-muted-foreground">
              <span className="font-medium">视觉：</span>
              {item.visionDesc}
            </p>
          )}
          {!item.ocrText && !item.visionDesc && !(item.thumbnail || item.image) && (
            <p className="text-xs text-muted-foreground">（无内容）</p>
          )}
        </div>
      </div>
    </>
  )
}
