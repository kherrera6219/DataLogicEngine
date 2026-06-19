import * as React from "react"
import { cn } from "@/lib/utils"

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Visual style variant. */
  variant?: "default" | "secondary" | "destructive" | "outline" | "success"
  /** Size of the badge. */
  size?: "sm" | "default" | "lg"
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    const sizeClasses = {
      sm: "px-2 py-0.5 text-xs",
      default: "px-2.5 py-0.5 text-xs",
      lg: "px-3 py-1 text-sm",
    }

    return (
      <div
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full border font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
          sizeClasses[size],
          {
            "border-transparent bg-blue-600 text-white hover:bg-blue-700": variant === "default",
            "border-transparent bg-gray-100 text-gray-900 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-50": variant === "secondary",
            "border-transparent bg-red-500 text-white hover:bg-red-600": variant === "destructive",
            "border-transparent bg-green-500 text-white hover:bg-green-600": variant === "success",
            "text-gray-950 dark:text-gray-50": variant === "outline",
          },
          className
        )}
        {...props}
      />
    )
  }
)
Badge.displayName = "Badge"

export { Badge }
export type { BadgeProps }
