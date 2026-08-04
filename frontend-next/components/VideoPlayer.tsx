"use client"

import { useRef, useEffect, useState, forwardRef, useImperativeHandle } from "react"
import { Captions, CaptionsOff, Maximize } from "lucide-react"

interface VideoPlayerProps {
  src: string
  className?: string
  /** 字幕 WebVTT URL（可选，提供则显示字幕开关） */
  subtitlesUrl?: string
}

export interface VideoPlayerRef {
  seek: (time: number) => void
  getCurrentTime: () => number
}

export const VideoPlayer = forwardRef<VideoPlayerRef, VideoPlayerProps>(
  function VideoPlayer({ src, className, subtitlesUrl }, ref) {
    const videoRef = useRef<HTMLVideoElement>(null)
    const containerRef = useRef<HTMLDivElement>(null)
    const [showSubtitles, setShowSubtitles] = useState(true)
    const [cueText, setCueText] = useState("")

    useImperativeHandle(ref, () => ({
      seek: (time: number) => {
        const video = videoRef.current
        if (!video) return
        video.currentTime = time
        if (video.paused) {
          void video.play()
        }
      },
      getCurrentTime: () => videoRef.current?.currentTime ?? 0,
    }))

    useEffect(() => {
      if (videoRef.current) {
        videoRef.current.load()
      }
    }, [src])

    // 字幕：track 用 hidden（不原生渲染，避免 controls+track 渲染两次），
    // 用 timeupdate 读当前 cue 自己渲染一个字幕层（比 cuechange 更可靠，不受 track 异步加载影响）
    useEffect(() => {
      const video = videoRef.current
      if (!video || !subtitlesUrl) return
      const onTime = () => {
        const track = video.textTracks?.[0]
        if (!track) return
        if (track.mode !== "hidden") track.mode = "hidden" // 触发加载但不原生渲染
        const c = track.activeCues?.[0] as VTTCue | undefined
        setCueText(c?.text || "")
      }
      video.addEventListener("timeupdate", onTime)
      // 首次 + 延迟各跑一次，覆盖 track 异步加载
      onTime()
      const t = setTimeout(onTime, 800)
      return () => {
        clearTimeout(t)
        video.removeEventListener("timeupdate", onTime)
      }
    }, [src, subtitlesUrl])

    const toggleFullscreen = () => {
      const el = containerRef.current
      if (!el) return
      if (document.fullscreenElement) {
        void document.exitFullscreen()
      } else {
        void el.requestFullscreen?.()
      }
    }

    return (
      <div ref={containerRef} className={`group relative bg-black ${className ?? ""}`}>
        {/* 隐藏原生全屏按钮（各浏览器伪元素不同），统一用右上角自定义控制 */}
        <style>{`
          .ggg-video::-webkit-media-controls-fullscreen-button { display: none !important; }
        `}</style>
        <video
          ref={videoRef}
          controls
          controlsList="nofullscreen"
          className="ggg-video h-full w-full rounded-xl bg-black"
          preload="metadata"
          crossOrigin="anonymous"
        >
          <source src={src} />
          {subtitlesUrl && (
            <track
              kind="subtitles"
              label="中文字幕"
              srcLang="zh"
              src={subtitlesUrl}
            />
          )}
          你的浏览器不支持 HTML5 视频。
        </video>

        {/* 自定义字幕层（替代原生渲染，避免重复） */}
        {showSubtitles && cueText && (
          <div className="pointer-events-none absolute bottom-4 left-1/2 max-w-[90%] -translate-x-1/2 rounded bg-black/75 px-3 py-1.5 text-center text-sm text-white shadow">
            {cueText}
          </div>
        )}

        {/* 悬浮控制：字幕开关 + 全屏（原生 controls 无全屏/字幕入口时补充） */}
        <div className="absolute right-2 top-2 flex gap-1.5 opacity-0 transition-opacity group-hover:opacity-100">
          {subtitlesUrl && (
            <button
              onClick={() => setShowSubtitles((v) => !v)}
              className="rounded-md bg-black/60 p-1.5 text-white backdrop-blur hover:bg-black/80"
              title={showSubtitles ? "隐藏字幕" : "显示字幕"}
            >
              {showSubtitles ? (
                <Captions className="h-4 w-4" />
              ) : (
                <CaptionsOff className="h-4 w-4" />
              )}
            </button>
          )}
          <button
            onClick={toggleFullscreen}
            className="rounded-md bg-black/60 p-1.5 text-white backdrop-blur hover:bg-black/80"
            title="全屏"
          >
            <Maximize className="h-4 w-4" />
          </button>
        </div>
      </div>
    )
  }
)
VideoPlayer.displayName = "VideoPlayer"
