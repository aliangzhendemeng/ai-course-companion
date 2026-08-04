"use client"

// 学伴全局状态：当前角色、情绪状态、TTS 播报。

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react"

import { listCharacters, synthesizeSpeech, type Character } from "@/lib/api"

/** 学伴情绪（对应动作槽） */
export type CompanionMood = "idle" | "happy" | "confused" | "loading" | "celebrate"

interface CompanionContextValue {
  character: Character | null
  characters: Character[]
  mood: CompanionMood
  /** 当前要显示/播报的口头禅气泡文本 */
  bubble: string | null
  /** 切换角色 */
  selectCharacter: (id: string) => void
  /** 触发一次情绪 + 可选口头禅 + 可选语音播报 */
  react: (mood: CompanionMood, phraseKey?: keyof Character["catchphrases"], speak?: boolean) => void
  /** 朗读任意文本（如讲义） */
  speak: (text: string) => void
  /** 停止播报 */
  stopSpeaking: () => void
  speaking: boolean
}

const CompanionContext = createContext<CompanionContextValue | null>(null)

const STORAGE_KEY = "companion.character_id"

export function CompanionProvider({ children }: { children: ReactNode }) {
  const [characters, setCharacters] = useState<Character[]>([])
  const [character, setCharacter] = useState<Character | null>(null)
  const [mood, setMood] = useState<CompanionMood>("idle")
  const [bubble, setBubble] = useState<string | null>(null)
  const [speaking, setSpeaking] = useState(false)

  const audioRef = useRef<HTMLAudioElement | null>(null)
  const audioUrlRef = useRef<string | null>(null)
  const bubbleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const moodTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // 加载角色列表，并恢复上次选择的角色（默认第一个）
  useEffect(() => {
    let cancelled = false
    listCharacters()
      .then((list) => {
        if (cancelled) return
        setCharacters(list)
        const saved = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null
        const initial = list.find((c) => c.id === saved) ?? list[0] ?? null
        setCharacter(initial)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current)
      audioUrlRef.current = null
    }
    setSpeaking(false)
  }, [])

  const speak = useCallback(
    (text: string) => {
      if (!text.trim() || !character) return
      stopSpeaking()
      setSpeaking(true)
      synthesizeSpeech(text, character.id)
        .then((blob) => {
          const url = URL.createObjectURL(blob)
          audioUrlRef.current = url
          const audio = new Audio(url)
          audioRef.current = audio
          audio.onended = () => stopSpeaking()
          audio.onerror = () => stopSpeaking()
          audio.play().catch(() => stopSpeaking())
        })
        .catch(() => stopSpeaking())
    },
    [character, stopSpeaking],
  )

  const react = useCallback(
    (m: CompanionMood, phraseKey?: keyof Character["catchphrases"], doSpeak = true) => {
      setMood(m)
      // 一段时间后回到待机
      if (moodTimerRef.current) clearTimeout(moodTimerRef.current)
      if (m !== "idle") {
        moodTimerRef.current = setTimeout(() => setMood("idle"), 3500)
      }

      const phrase = phraseKey && character ? character.catchphrases[phraseKey] : null
      if (phrase) {
        setBubble(phrase)
        if (bubbleTimerRef.current) clearTimeout(bubbleTimerRef.current)
        bubbleTimerRef.current = setTimeout(() => setBubble(null), 3500)
        if (doSpeak) speak(phrase)
      }
    },
    [character, speak],
  )

  // 暴露到 window 供录屏/调试触发学伴反应（情绪动作 + 口头禅气泡 + TTS）
  useEffect(() => {
    if (typeof window !== "undefined") {
      ;(window as unknown as { __react?: typeof react }).__react = react
    }
  }, [react])

  const selectCharacter = useCallback(
    (id: string) => {
      const next = characters.find((c) => c.id === id) ?? null
      setCharacter(next)
      if (typeof window !== "undefined") localStorage.setItem(STORAGE_KEY, id)
      stopSpeaking()
      setMood("idle")
      setBubble(null)
    },
    [characters, stopSpeaking],
  )

  const value: CompanionContextValue = {
    character,
    characters,
    mood,
    bubble,
    selectCharacter,
    react,
    speak,
    stopSpeaking,
    speaking,
  }

  return <CompanionContext.Provider value={value}>{children}</CompanionContext.Provider>
}

export function useCompanion(): CompanionContextValue {
  const ctx = useContext(CompanionContext)
  if (!ctx) {
    throw new Error("useCompanion 必须在 CompanionProvider 内使用")
  }
  return ctx
}
