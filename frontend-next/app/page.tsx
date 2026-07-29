import { redirect } from "next/navigation"

import { getSettings } from "@/lib/api"

export default async function HomePage() {
  let configured = false
  try {
    const settings = await getSettings()
    configured = settings.is_configured
  } catch {
    configured = false
  }

  if (!configured) {
    redirect("/welcome")
  }

  redirect("/courses")
}
