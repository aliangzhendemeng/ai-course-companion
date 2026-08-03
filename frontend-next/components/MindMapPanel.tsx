"use client"

import { Skeleton } from "@/components/ui/skeleton"
import { useMindMap } from "@/hooks/use-api"
import type { MindMapNode } from "@/lib/api"

interface MindMapPanelProps {
  courseId: number
}

/** 思维导图面板：递归渲染课程知识树（横向 + 连线）。 */
export function MindMapPanel({ courseId }: MindMapPanelProps) {
  const { data: tree, isLoading } = useMindMap(courseId)

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    )
  }
  if (!tree || (!tree.title && !tree.children?.length)) {
    return <p className="py-6 text-center text-sm text-muted-foreground">暂无内容，无法生成思维导图</p>
  }
  return (
    <div className="overflow-x-auto">
      <MindMapTreeNode node={tree} depth={0} />
    </div>
  )
}

function MindMapTreeNode({ node, depth }: { node: MindMapNode; depth: number }) {
  const hasChildren = !!node.children?.length
  // 强对比分层：根（实色块）/ 分支（蓝框）/ 叶（浅色），层次一目了然
  const nodeCls =
    depth === 0
      ? "bg-primary text-primary-foreground text-base font-bold px-4 py-2 shadow-md"
      : depth === 1
      ? "border-2 border-blue-300 bg-blue-50 px-3 py-1.5 font-semibold text-blue-800 dark:border-blue-700 dark:bg-blue-950/60 dark:text-blue-200"
      : "border border-border bg-card px-2.5 py-1 text-sm text-muted-foreground"

  return (
    <div className="flex items-start gap-3">
      <div className={`shrink-0 rounded-lg whitespace-nowrap ${nodeCls}`}>
        {node.title}
      </div>
      {hasChildren && (
        <div className="flex flex-col gap-2 pl-5">
          {node.children!.map((c, i) => (
            <MindMapTreeNode key={i} node={c} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}
