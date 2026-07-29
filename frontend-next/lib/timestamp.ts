import type { Source } from "@/lib/api"

export function formatTimestamp(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}:${pad(m)}:${pad(s)}`
  return `${m}:${pad(s)}`
}

function pad(n: number): string {
  return n.toString().padStart(2, "0")
}

export interface DeduplicatedSource {
  timestamp: number
  sources: Source[]
  courseTitle?: string | null
}

export function deduplicateSources(sources: Source[], thresholdSeconds = 5): DeduplicatedSource[] {
  if (sources.length === 0) return []

  const sorted = [...sources].sort((a, b) => a.timestamp - b.timestamp)
  const groups: DeduplicatedSource[] = []

  for (const source of sorted) {
    const lastGroup = groups[groups.length - 1]
    if (lastGroup && Math.abs(source.timestamp - lastGroup.timestamp) <= thresholdSeconds) {
      lastGroup.sources.push(source)
      if (source.course_title) {
        lastGroup.courseTitle = source.course_title
      }
    } else {
      groups.push({
        timestamp: source.timestamp,
        sources: [source],
        courseTitle: source.course_title,
      })
    }
  }

  return groups
}
