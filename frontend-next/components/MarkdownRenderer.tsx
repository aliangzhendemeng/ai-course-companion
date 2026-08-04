"use client"

import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface MarkdownRendererProps {
  children: string
  /** 可选：把正文中的 [N] 渲染为可点击的引用角标 */
  renderCitation?: (num: number, key: string) => React.ReactNode
}

/** 把文本里的 [N] 切成 文本/引用 片段（不在代码片段里处理）。 */
function withCitations(
  node: React.ReactNode,
  renderCitation: (num: number, key: string) => React.ReactNode,
  keyPrefix: string
): React.ReactNode {
  if (typeof node === "string") {
    const parts = node.split(/(\[\d+\])/)
    if (parts.length === 1) return node
    return parts.map((part, i) => {
      const m = part.match(/^\[(\d+)\]$/)
      if (m) return renderCitation(parseInt(m[1], 10), `${keyPrefix}-${i}`)
      return <React.Fragment key={`${keyPrefix}-${i}`}>{part}</React.Fragment>
    })
  }
  if (Array.isArray(node)) {
    return node.map((child, i) => (
      <React.Fragment key={`${keyPrefix}-${i}`}>
        {withCitations(child, renderCitation, `${keyPrefix}-${i}`)}
      </React.Fragment>
    ))
  }
  return node
}

export function MarkdownRenderer({ children, renderCitation }: MarkdownRendererProps) {
  // 包装文本类组件，把 [N] 转为引用角标
  const wrap = (content: React.ReactNode, keyPrefix: string) =>
    renderCitation ? withCitations(content, renderCitation, keyPrefix) : content

  let seq = 0
  const nextKey = () => `c${seq++}`

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{wrap(children, nextKey())}</p>,
        strong: ({ children }) => <strong className="font-semibold text-foreground">{wrap(children, nextKey())}</strong>,
        ul: ({ children }) => <ul className="mb-2 list-inside list-disc space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="mb-2 list-inside list-decimal space-y-1">{children}</ol>,
        li: ({ children }) => <li className="leading-relaxed">{wrap(children, nextKey())}</li>,
        code: ({ children }) => (
          <code className="rounded bg-muted px-1 py-0.5 text-xs font-mono">{children}</code>
        ),
        h1: ({ children }) => <h1 className="mb-2 text-lg font-bold">{wrap(children, nextKey())}</h1>,
        h2: ({ children }) => <h2 className="mb-2 text-base font-semibold">{wrap(children, nextKey())}</h2>,
        h3: ({ children }) => <h3 className="mb-1 text-sm font-semibold">{wrap(children, nextKey())}</h3>,
        a: ({ children, href }) => (
          <a href={href} className="text-primary underline" target="_blank" rel="noreferrer">
            {children}
          </a>
        ),
      }}
    >
      {children}
    </ReactMarkdown>
  )
}
