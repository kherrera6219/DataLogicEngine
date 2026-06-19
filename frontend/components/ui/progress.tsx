"use client"

import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"

import { cn } from "@/lib/utils"

/** Props for the Progress component. */
interface ProgressProps extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> {
  /** The current progress value (0-100). */
  value?: number
  /** The maximum value (typically 100). */
  max?: number
  /** Size variant of the progress bar. */
  size?: "sm" | "default" | "lg"
  /** Color variant of the progress bar. */
  variant?: "default" | "success" | "warning" | "destructive"
  /** Whether to animate the progress bar. */
  animated?: boolean
}

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(({ className, value = 0, max = 100, size = "default", variant = "default", animated = true, ...props }, ref) => {
  const sizeClasses = {
    sm: "h-2",
    default: "h-4",
    lg: "h-6",
  }

  const variantClasses = {
    default: "bg-primary",
    success: "bg-green-500",
    warning: "bg-yellow-500",
    destructive: "bg-red-500",
  }

  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  return (
    <ProgressPrimitive.Root
      ref={ref}
      className={cn(
        "relative w-full overflow-hidden rounded-full bg-secondary",
        sizeClasses[size],
        className
      )}
      value={value}
      max={max}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className={cn(
          "h-full w-full flex-1 transition-all",
          variantClasses[variant],
          animated && "animate-pulse"
        )}
        style={{ transform: `translateX(-${100 - percentage}%)` }}
      />
    </ProgressPrimitive.Root>
  )
})
Progress.displayName = ProgressPrimitive.Root.displayName

export { Progress }
export type { ProgressProps }
