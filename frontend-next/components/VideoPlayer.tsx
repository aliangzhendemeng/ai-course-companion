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

    // 切换字幕显隐（操作 textTrack，不重新加载视频）
    useEffect(() => {
      const track = videoRef.current?.textTracks?.[0]
      if (track) {
        track.mode = showSubtitles ? "showing" : "hidden"
      }
    }, [showSubtitles, src, subtitlesUrl])

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
              default
            />
          )}
          你的浏览器不支持 HTML5 视频。
        </video>

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
