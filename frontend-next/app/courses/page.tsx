import { listCourses } from "@/lib/api"
import { CoursesClient } from "./CoursesClient"

export default async function CoursesPage() {
  const courses = await listCourses()
  return <CoursesClient initialCourses={courses} />
}
