import React from "react"
import { cn } from "@/lib/utils"

/** Props for the Skeleton component. */
interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Size variant of the skeleton. */
  size?: "sm" | "default" | "lg"
  /** Number of skeleton lines to render (for text placeholders). */
  lines?: number
  /** Whether the skeleton is circular (for avatar placeholders). */
  circular?: boolean
}

function Skeleton({
  className,
  size = "default",
  lines,
  circular = false,
  ...props
}: SkeletonProps) {
  const sizeClasses = {
    sm: "h-4 rounded-sm",
    default: "h-12 rounded-md",
    lg: "h-24 rounded-lg",
  }

  if (circular) {
    return (
      <div
        role="status"
        aria-busy="true"
        aria-label="Loading..."
        className={cn("animate-pulse rounded-full bg-muted/50", className)}
        {...props}
      />
    )
  }

  if (lines && lines > 1) {
    return (
      <div role="status" aria-busy="true" aria-label="Loading..." className="space-y-2" {...props}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "animate-pulse bg-muted/50",
              sizeClasses[size],
              i === lines - 1 && "w-2/3",
              className
            )}
          />
        ))}
      </div>
    )
  }

  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="Loading..."
      className={cn("animate-pulse rounded-md bg-muted/50", sizeClasses[size], className)}
      {...props}
    />
  )
}

export { Skeleton }
export type { SkeletonProps }
