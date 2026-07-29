"use client"

import { useRef, useState } from "react"
import { ArrowLeft, Loader2, Clock, FileText, Image, MessageSquare, ChevronDown } from "lucide-react"
import Link from "next/link"
import { useParams, useRouter, useSearchParams } from "next/navigation"

import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { VideoPlayer, type VideoPlayerRef } from "@/components/VideoPlayer"
import { DebugTimeline } from "@/components/DebugTimeline"
import { DebugSummary } from "@/components/DebugSummary"
import { DebugChat } from "@/components/DebugChat"
import {
  useCourse,
  useCourseTranscriptsDebug,
  useCourseFramesDebug,
  useCourseSummaryDebug,
  useChatDebug,
  useChatHistory,
} from "@/hooks/use-api"

export default function CourseDebugPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const courseId = Number(params.id)
  const selectedMessageId = searchParams.get("message")
    ? Number(searchParams.get("message"))
    : null

  const router = useRouter()
  const videoRef = useRef<VideoPlayerRef>(null)

  const { data: course, isLoading: courseLoading } = useCourse(courseId)
  const { data: transcripts } = useCourseTranscriptsDebug(courseId)
  const { data: frames } = useCourseFramesDebug(courseId)
  const { data: summary } = useCourseSummaryDebug(courseId)
  const { data: history } = useChatHistory(courseId)
  const { data: debugChat } = useChatDebug(selectedMessageId)

  const handleSeek = (timestamp: number) => {
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
          <Link href={`/courses/${courseId}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-1 h-4 w-4" />
              返回学习页
            </Button>
          </Link>
          <h1 className="text-xl font-bold">{course.title} · 诊断</h1>
        </div>
      </div>

      <div className="grid flex-1 gap-4 lg:grid-cols-5">
        <div className="flex flex-col gap-4 lg:col-span-3">
          <VideoPlayer
            ref={videoRef}
            src={course.video_url}
            className="aspect-video w-full overflow-hidden rounded-xl bg-black"
          />
          <Tabs defaultValue="timeline" className="flex min-h-0 flex-1 flex-col">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="timeline">
                <Clock className="mr-1 h-4 w-4" />
                时间轴
              </TabsTrigger>
              <TabsTrigger value="summary">
                <FileText className="mr-1 h-4 w-4" />
                总结
              </TabsTrigger>
              <TabsTrigger value="chat">
                <MessageSquare className="mr-1 h-4 w-4" />
                问答 Debug
              </TabsTrigger>
            </TabsList>

            <ScrollArea className="mt-2 flex-1 rounded-xl border bg-card p-4">
              <TabsContent value="timeline" className="mt-0">
                <DebugTimeline
                  transcripts={transcripts || []}
                  frames={frames || []}
                  onSeek={handleSeek}
                />
              </TabsContent>
              <TabsContent value="summary" className="mt-0">
                <DebugSummary summary={summary} />
              </TabsContent>
              <TabsContent value="chat" className="mt-0">
                <DebugChat
                  history={history || []}
                  debug={debugChat}
                  selectedMessageId={selectedMessageId}
                  onSelect={(id) => router.push(`/courses/${courseId}/debug?message=${id}`)}
                />
              </TabsContent>
            </ScrollArea>
          </Tabs>
        </div>

        <div className="flex flex-col gap-4 lg:col-span-2">
          <DebugDetailPanel debug={debugChat} />
        </div>
      </div>
    </div>
  )
}

function DebugDetailPanel({ debug }: { debug?: import("@/lib/api").ChatDebug }) {
  if (!debug) {
    return (
      <div className="flex h-full flex-col items-center justify-center rounded-xl border bg-card p-6 text-center">
        <MessageSquare className="mb-2 h-8 w-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">在左侧“问答 Debug”中选择一条助手回答，查看完整 prompt、上下文和模型信息。</p>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col gap-3 rounded-xl border bg-card p-4">
      <div className="flex items-center justify-between border-b pb-3">
        <div>
          <p className="text-xs font-medium text-muted-foreground">模型</p>
          <p className="text-sm font-medium">{debug.model}</p>
        </div>
        {debug.question && (
          <div className="max-w-[60%] text-right">
            <p className="text-xs font-medium text-muted-foreground">问题</p>
            <p className="line-clamp-2 text-xs">{debug.question}</p>
          </div>
        )}
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-2 pr-2">
          <CollapsibleBlock title="完整 Prompt" content={debug.prompt} />
          <CollapsibleBlock title="上下文（检索到的课程内容）" content={debug.context} defaultOpen />
          <CollapsibleBlock title="原始回答" content={debug.raw_answer} defaultOpen />
        </div>
      </ScrollArea>
    </div>
  )
}

function CollapsibleBlock({
  title,
  content,
  defaultOpen = false,
}: {
  title: string
  content?: string
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  const text = content?.trim() ? content : "（未记录：该问答是在加入诊断记录之前生成的，重新提问即可看到完整 prompt 与上下文）"
  const charCount = content?.trim() ? content.length : 0

  return (
    <div className="rounded-lg border">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-medium hover:bg-accent/50"
      >
        <span>{title}</span>
        <span className="flex items-center gap-2 text-muted-foreground">
          {charCount > 0 && <span>{charCount.toLocaleString()} 字符</span>}
          <ChevronDown className={`h-3.5 w-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
        </span>
      </button>
      {open && (
        <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap border-t bg-muted/40 px-3 py-2 text-xs leading-relaxed">
          {text}
        </pre>
      )}
    </div>
  )
}

