"use client"

import { useRef, useEffect, forwardRef, useImperativeHandle } from "react"

interface VideoPlayerProps {
  src: string
  className?: string
}

export interface VideoPlayerRef {
  seek: (time: number) => void
}

export const VideoPlayer = forwardRef<VideoPlayerRef, VideoPlayerProps>(
  function VideoPlayer({ src, className }, ref) {
    const videoRef = useRef<HTMLVideoElement>(null)

    useImperativeHandle(ref, () => ({
      seek: (time: number) => {
        const video = videoRef.current
        if (!video) return
        video.currentTime = time
        if (video.paused) {
          void video.play()
        }
      },
    }))

    useEffect(() => {
      if (videoRef.current) {
        videoRef.current.load()
      }
    }, [src])

    return (
      <div className={className}>
        <video
          ref={videoRef}
          controls
          className="h-full w-full rounded-xl bg-black"
          preload="metadata"
          crossOrigin="anonymous"
        >
          <source src={src} />
          你的浏览器不支持 HTML5 视频。
        </video>
      </div>
    )
  }
)
VideoPlayer.displayName = "VideoPlayer"
