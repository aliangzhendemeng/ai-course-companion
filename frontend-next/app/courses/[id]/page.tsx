"use client"

import { useEffect, useRef, useState } from "react"
import { ArrowLeft, Loader2, Stethoscope } from "lucide-react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { VideoPlayer, type VideoPlayerRef } from "@/components/VideoPlayer"
import { SummaryTabs } from "@/components/SummaryTabs"
import { ChatPanel } from "@/components/ChatPanel"
import { QuizPanel } from "@/components/QuizPanel"
import { FlashcardPanel } from "@/components/FlashcardPanel"
import { NotesPanel } from "@/components/NotesPanel"
import { SegmentSummary } from "@/components/SegmentSummary"
import { ConversationSwitcher } from "@/components/ConversationSwitcher"
import {
  useCourse,
  useSummary,
  useAskQuestion,
  useConversationMessages,
  useConversations,
} from "@/hooks/use-api"
import { getSubtitlesUrl } from "@/lib/api"
import { useCompanion } from "@/components/companion/CompanionContext"

export default function CourseDetailPage() {
  const params = useParams()
  const courseId = Number(params.id)
  const router = useRouter()
  const videoRef = useRef<VideoPlayerRef>(null)

  const { data: course, isLoading: courseLoading } = useCourse(courseId)
  const { data: summary, isLoading: summaryLoading } = useSummary(courseId)
  const askMutation = useAskQuestion()
  const { react } = useCompanion()

  // 会话制：当前会话 id（null = 新会话）
  const [activeConvId, setActiveConvId] = useState<number | null>(null)
  const { data: conversations } = useConversations(courseId)
  const { data: convMessages, isLoading: convLoading } = useConversationMessages(activeConvId)

  // 进入课程/会话列表就绪时，默认选最近一个会话
  useEffect(() => {
    if (activeConvId === null && conversations && conversations.length > 0) {
      setActiveConvId(conversations[0].id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversations])

  // 进入课程页，学伴打招呼（仅文字气泡，不语音打扰）
  useEffect(() => {
    react("happy", "greeting", false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId])

  const handleSeek = (timestamp: number, targetCourseId?: number) => {
    if (targetCourseId && targetCourseId !== courseId) {
      router.push(`/courses/${targetCourseId}?timestamp=${timestamp}`)
      return
    }
    videoRef.current?.seek(timestamp)
  }

  const currentConv = conversations?.find((c) => c.id === activeConvId)

  if (courseLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!course) {
    return (
      <div className="container mx-auto p-6">
        <p>课程不存在</p>
        <Link href="/courses">
          <Button variant="ghost">返回课程库</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="container mx-auto flex h-[calc(100vh-1rem)] flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link href="/courses">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-1 h-4 w-4" />
              返回
            </Button>
          </Link>
          <h1 className="text-xl font-bold">{course.title}</h1>
        </div>
        <Link href={`/courses/${courseId}/debug`}>
          <Button variant="outline" size="sm">
            <Stethoscope className="mr-1 h-4 w-4" />
            诊断
          </Button>
        </Link>
      </div>

      <div className="grid flex-1 gap-4 lg:grid-cols-5">
        <div className="flex flex-col gap-4 lg:col-span-3">
          <VideoPlayer
            ref={videoRef}
            src={course.video_url}
            subtitlesUrl={getSubtitlesUrl(courseId)}
            className="aspect-video w-full overflow-hidden rounded-xl bg-black"
          />
          <SegmentSummary courseId={courseId} getCurrentTime={() => videoRef.current?.getCurrentTime() ?? 0} />
          <div className="flex-1 rounded-xl border bg-card p-4 shadow-sm">
            <Tabs defaultValue="summary" className="flex h-full flex-col">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="summary">总结</TabsTrigger>
                <TabsTrigger value="quiz">测验</TabsTrigger>
                <TabsTrigger value="flashcard">闪卡</TabsTrigger>
                <TabsTrigger value="notes">笔记</TabsTrigger>
              </TabsList>
              <TabsContent value="summary" className="mt-4 flex-1 min-h-0">
                <SummaryTabs
                  summary={summary}
                  isLoading={summaryLoading}
                  courseId={courseId}
                  onSeek={handleSeek}
                />
              </TabsContent>
              <TabsContent value="quiz" className="mt-4 flex-1">
                <QuizPanel scope={{ courseId }} onSeek={handleSeek} />
              </TabsContent>
              <TabsContent value="flashcard" className="mt-4 flex-1">
                <FlashcardPanel scope={{ courseId }} onSeek={handleSeek} />
              </TabsContent>
              <TabsContent value="notes" className="mt-4 flex-1">
                <NotesPanel
                  courseId={courseId}
                  getCurrentTime={() => videoRef.current?.getCurrentTime() ?? 0}
                  onSeek={handleSeek}
                />
              </TabsContent>
            </Tabs>
          </div>
        </div>

        <div className="flex flex-col gap-2 pb-40 lg:col-span-2">
          <ConversationSwitcher courseId={courseId} activeId={activeConvId} onSelect={setActiveConvId} />
          <div className="min-h-0 flex-1">
            <ChatPanel
              courseId={courseId}
              messages={convMessages ?? []}
              isLoading={convLoading || askMutation.isPending}
              sessionMode
              title={currentConv?.title ?? "新对话"}
              onSend={(question, _scope, _courseIds, image) =>
                askMutation.mutate(
                  {
                    courseId,
                    question,
                    scope: "course",
                    image,
                    conversationId: activeConvId ?? undefined,
                  },
                  {
                    onSuccess: (data) => {
                      // 首次提问创建了新会话，切换到它
                      if (activeConvId === null && data.conversation_id) {
                        setActiveConvId(data.conversation_id)
                      }
                    },
                  }
                )
              }
              onSeek={handleSeek}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
