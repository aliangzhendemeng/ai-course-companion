"use client"

// 语音输入：封装浏览器 Web Speech API（SpeechRecognition），中文识别。

import { useCallback, useEffect, useRef, useState } from "react"

// Web Speech API 类型（TS 默认不含 webkit 前缀版本）
interface SpeechRecognitionResultItem {
  transcript: string
}
interface SpeechRecognitionResultList {
  [index: number]: { [index: number]: SpeechRecognitionResultItem }
}
interface SpeechRecognitionEventLike {
  results: SpeechRecognitionResultList
}
interface SpeechRecognitionLike {
  lang: string
  interimResults: boolean
  continuous: boolean
  onresult: ((e: SpeechRecognitionEventLike) => void) | null
  onerror: ((e: { error?: string }) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
  abort: () => void
}

function getRecognition(): SpeechRecognitionLike | null {
  if (typeof window === "undefined") return null
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike
    webkitSpeechRecognition?: new () => SpeechRecognitionLike
  }
  const Ctor = w.SpeechRecognition || w.webkitSpeechRecognition
  return Ctor ? new Ctor() : null
}

export interface UseSpeechInputOptions {
  /** 识别出最终文本时回调（追加到输入框） */
  onResult: (text: string) => void
}

export function useSpeechInput({ onResult }: UseSpeechInputOptions) {
  const [listening, setListening] = useState(false)
  const [supported, setSupported] = useState(false)
  const recogRef = useRef<SpeechRecognitionLike | null>(null)
  const onResultRef = useRef(onResult)
  onResultRef.current = onResult

  useEffect(() => {
    setSupported(getRecognition() !== null)
    return () => {
      recogRef.current?.abort()
      recogRef.current = null
    }
  }, [])

  const start = useCallback(() => {
    const recog = getRecognition()
    if (!recog) return
    recogRef.current = recog
    recog.lang = "zh-CN"
    recog.interimResults = false
    recog.continuous = false
    recog.onresult = (e) => {
      const text = e.results[0]?.[0]?.transcript ?? ""
      if (text) onResultRef.current(text)
    }
    recog.onerror = () => setListening(false)
    recog.onend = () => setListening(false)
    try {
      recog.start()
      setListening(true)
    } catch {
      setListening(false)
    }
  }, [])

  const stop = useCallback(() => {
    recogRef.current?.stop()
    setListening(false)
  }, [])

  const toggle = useCallback(() => {
    if (listening) stop()
    else start()
  }, [listening, start, stop])

  return { listening, supported, toggle, start, stop }
}
