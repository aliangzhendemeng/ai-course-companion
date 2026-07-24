import { listCourses } from "@/lib/api"
import { ChatPageClient } from "./ChatPageClient"

export default async function ChatPage() {
  const courses = await listCourses()
  return <ChatPageClient initialCourses={courses} />
}
