import * as React from "react"
import { cn } from "@/lib/utils"

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** Show error state styling. */
  error?: boolean
  /** Show loading state. */
  loading?: boolean
  /** Icon to display on the right side. */
  icon?: React.ReactNode
  /** Size variant. */
  sizeVariant?: "sm" | "default" | "lg"
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, loading, icon, sizeVariant = "default", ...props }, ref) => {
    const sizeClasses = {
      sm: "h-8 px-2 text-xs",
      default: "h-10 px-3 py-2 text-sm",
      lg: "h-12 px-4 py-3 text-base",
    }

    return (
      <div className="relative w-full">
        <input
          type={type}
          className={cn(
            "flex w-full rounded-lg border bg-white px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-[#2d2d2d] dark:ring-offset-black dark:placeholder:text-gray-400 transition-all duration-200 shadow-sm",
            sizeClasses[sizeVariant],
            error 
              ? "border-red-500 dark:border-red-400 focus-visible:ring-red-500/30 focus-visible:border-red-500" 
              : "border-gray-300 dark:border-[#383838] focus-visible:border-blue-500 focus-visible:ring-blue-500/30 dark:focus-visible:border-blue-500",
            icon && "pr-10",
            className
          )}
          ref={ref}
          disabled={loading || props.disabled}
          {...props}
        />
        {icon && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
            {icon}
          </div>
        )}
      </div>
    )
  }
)
Input.displayName = "Input"

export { Input, type InputProps }
