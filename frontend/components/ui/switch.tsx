import * as React from "react"
import { cn } from "@/lib/utils"

/** Props for the Switch component. */
interface SwitchProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Whether the switch is checked. */
  checked?: boolean
  /** Callback when the checked state changes. */
  onCheckedChange?: (checked: boolean) => void
  /** Size variant of the switch. */
  size?: "sm" | "default" | "lg"
  /** Accessible label for the switch. */
  "aria-label"?: string
  /** ID of element describing the switch. */
  "aria-describedby"?: string
}

const Switch = React.forwardRef<HTMLButtonElement, SwitchProps>(
  ({ className, checked, onCheckedChange, size = "default", ...props }, ref) => {
    const sizeClasses = {
      sm: "h-5 w-9",
      default: "h-6 w-11",
      lg: "h-7 w-14",
    }

    const thumbClasses = {
      sm: "h-4 w-4",
      default: "h-5 w-5",
      lg: "h-6 w-6",
    }

    const thumbTranslate = {
      sm: checked ? "translate-x-4" : "translate-x-0",
      default: checked ? "translate-x-5" : "translate-x-0",
      lg: checked ? "translate-x-7" : "translate-x-0",
    }

    const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault()
        onCheckedChange?.(!checked)
      } else if (e.key === 'ArrowRight') {
        e.preventDefault()
        if (!checked) onCheckedChange?.(true)
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault()
        if (checked) onCheckedChange?.(false)
      }
    }

    return (
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onCheckedChange?.(!checked)}
        onKeyDown={handleKeyDown}
        className={cn(
          "peer inline-flex shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:cursor-not-allowed disabled:opacity-50 dark:focus-visible:ring-offset-gray-950",
          sizeClasses[size],
          checked ? "bg-blue-600" : "bg-gray-200 dark:bg-gray-800",
          className
        )}
        ref={ref}
        {...props}
      >
        <span
          className={cn(
            "pointer-events-none block rounded-full bg-white shadow-lg ring-0 transition-transform dark:bg-gray-950",
            thumbClasses[size],
            thumbTranslate[size]
          )}
          aria-hidden="true"
        />
      </button>
    )
  }
)
Switch.displayName = "Switch"

export { Switch }
export type { SwitchProps }
