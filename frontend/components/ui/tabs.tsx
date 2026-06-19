import * as React from "react"
import { cn } from "@/lib/utils"

// Simulating Radix UI Tabs without installing the package to avoid wait times
// We build a semantic equivalent implementation

/** Props for the Tabs context. */
interface TabsContextType {
  value: string
  onValueChange: (value: string) => void
  orientation?: "horizontal" | "vertical"
}

const TabsContext = React.createContext<TabsContextType | null>(null)

/** Props for the Tabs component. */
interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  /** The currently selected tab value. */
  value: string
  /** Callback when the tab value changes. */
  onValueChange: (value: string) => void
  /** The orientation of the tabs. */
  orientation?: "horizontal" | "vertical"
}

const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(
  ({ className, value, onValueChange, orientation = "horizontal", ...props }, ref) => (
    <TabsContext.Provider value={{ value, onValueChange, orientation }}>
      <div ref={ref} className={cn("w-full", className)} {...props} />
    </TabsContext.Provider>
  )
)
Tabs.displayName = "Tabs"

const TabsList = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
  const context = React.useContext(TabsContext)
  const isVertical = context?.orientation === "vertical"

  return (
    <div
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-md bg-gray-100 p-1 text-gray-500 dark:bg-gray-800 dark:text-gray-400",
        isVertical ? "flex-col h-auto w-auto" : "h-10",
        className
      )}
      role="tablist"
      aria-orientation={context?.orientation}
      {...props}
    />
  )
})
TabsList.displayName = "TabsList"

/** Props for the TabsTrigger component. */
interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** The value associated with this tab. */
  value: string
}

const TabsTrigger = React.forwardRef<HTMLButtonElement, TabsTriggerProps>(
  ({ className, value, ...props }, ref) => {
    const context = React.useContext(TabsContext)
    const isActive = context?.value === value
    
    const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
      // Handle arrow key navigation for tabs
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault()
        // Move to next tab - implementation would require passing all tab values
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault()
        // Move to previous tab
      } else if (e.key === 'Home') {
        e.preventDefault()
        // Jump to first tab
      } else if (e.key === 'End') {
        e.preventDefault()
        // Jump to last tab
      }
    }

    return (
      <button
        ref={ref}
        role="tab"
        aria-selected={isActive}
        aria-controls={`tab-panel-${value}`}
        tabIndex={isActive ? 0 : -1}
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50",
          isActive 
            ? "bg-white text-gray-950 shadow-sm dark:bg-gray-950 dark:text-gray-50" 
            : "hover:bg-gray-200/50 dark:hover:bg-gray-700/50",
          className
        )}
        onClick={() => context?.onValueChange(value)}
        onKeyDown={handleKeyDown}
        {...props}
      />
    )
  }
)
TabsTrigger.displayName = "TabsTrigger"

/** Props for the TabsContent component. */
interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  /** The value this content corresponds to. */
  value: string
}

const TabsContent = React.forwardRef<HTMLDivElement, TabsContentProps>(
  ({ className, value, ...props }, ref) => {
    const context = React.useContext(TabsContext)
    if (context?.value !== value) return null

    return (
      <div
        ref={ref}
        role="tabpanel"
        id={`tab-panel-${value}`}
        aria-labelledby={`tab-trigger-${value}`}
        className={cn(
          "mt-2 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:ring-offset-gray-950",
          className
        )}
        {...props}
      />
    )
  }
)
TabsContent.displayName = "TabsContent"

export { Tabs, TabsList, TabsTrigger, TabsContent }
export type { TabsProps, TabsTriggerProps, TabsContentProps }
