"use client"

import { useEffect, useRef } from "react"
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
import { useCourse, useSummary, useChatHistory, useAskQuestion } from "@/hooks/use-api"
import { getSubtitlesUrl } from "@/lib/api"
import { useCompanion } from "@/components/companion/CompanionContext"

export default function CourseDetailPage() {
  const params = useParams()
  const courseId = Number(params.id)
  const router = useRouter()
  const videoRef = useRef<VideoPlayerRef>(null)

  const { data: course, isLoading: courseLoading } = useCourse(courseId)
  const { data: summary, isLoading: summaryLoading } = useSummary(courseId)
  const { data: history, isLoading: historyLoading } = useChatHistory(courseId)
  const askMutation = useAskQuestion()
  const { react } = useCompanion()

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
          <div className="flex-1 rounded-xl border bg-card p-4 shadow-sm">
            <Tabs defaultValue="summary" className="flex h-full flex-col">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="summary">总结</TabsTrigger>
                <TabsTrigger value="quiz">测验</TabsTrigger>
                <TabsTrigger value="flashcard">闪卡</TabsTrigger>
                <TabsTrigger value="notes">笔记</TabsTrigger>
              </TabsList>
              <TabsContent value="summary" className="mt-4 flex-1">
                <SummaryTabs summary={summary} isLoading={summaryLoading} onSeek={handleSeek} />
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

        <div className="lg:col-span-2">
          <ChatPanel
            courseId={courseId}
            messages={history || []}
            isLoading={historyLoading || askMutation.isPending}
            onSend={(question, scope, courseIds) =>
              askMutation.mutate({ courseId, question, scope, courseIds })
            }
            onSeek={handleSeek}
          />
        </div>
      </div>
    </div>
  )
}
