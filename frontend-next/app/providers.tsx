"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"

import { CompanionProvider } from "@/components/companion/CompanionContext"
import { Companion } from "@/components/companion/Companion"

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 10,
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      <CompanionProvider>
        {children}
        <Companion />
      </CompanionProvider>
    </QueryClientProvider>
  )
}
