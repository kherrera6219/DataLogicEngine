
import * as React from "react"
import { cn } from "@/lib/utils"
import { Cloud, CheckCircle2, AlertCircle } from "lucide-react"



interface CloudStatusProps extends React.HTMLAttributes<HTMLDivElement> {
  provider?: string
  isProcessing?: boolean
  error?: string
}

export function CloudStatusIndicator({ 
  provider = "Auto", 
  isProcessing = false, 
  error,
  className,
  ...props 
}: CloudStatusProps) {
  
  return (
    <div className={cn("flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 border border-border/50 text-xs font-medium backdrop-blur-sm", className)} {...props}>
      <div className="relative">
        <Cloud className={cn("h-3.5 w-3.5", error ? "text-destructive" : "text-muted-foreground")} />
         {isProcessing && (
            <span className="absolute -right-0.5 -top-0.5 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-sky-500"></span>
            </span>
         )}
      </div>
      
      <span className="text-muted-foreground">
        {error ? "Cloud Error" : isProcessing ? "Processing..." : `${provider} Online`}
      </span>

      {!isProcessing && !error && (
        <CheckCircle2 className="h-3 w-3 text-green-500 ml-1" />
      )}
      
      {error && (
        <AlertCircle className="h-3 w-3 text-destructive ml-1" />
      )}
    </div>
  )
}
