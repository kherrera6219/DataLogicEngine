import { Message } from '@/lib/api';
import { cn } from '@/lib/utils';
import { CopyButton } from '@/components/ui/copy-button';
import { Brain, Shield, User, Bot } from 'lucide-react';

interface Props {
  message: Message;
  isThinking?: boolean;
}

export function MessageBubble({ message, isThinking }: Props) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  
  return (
    <div className={cn("flex w-full mb-6 animate-in fade-in slide-in-from-bottom-2 duration-300", isUser ? "justify-end" : "justify-start")}>
      <div className={cn(
        "flex gap-3 max-w-[85%]",
        isUser ? "flex-row-reverse" : "flex-row"
      )}>
        {/* Avatar */}
        <div className={cn(
          "w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border border-white/10 shadow-lg",
          isUser ? "bg-blue-600 text-white" : isSystem ? "bg-red-500/10 text-red-500" : "bg-gray-800 text-gray-400"
        )}>
          {isUser ? <User className="h-4 w-4" /> : isSystem ? <Shield className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </div>

        <div className={cn(
          "relative p-4 rounded-2xl border backdrop-blur-xl shadow-xl transition-all duration-300 group",
          isUser 
            ? "bg-blue-600/10 text-foreground border-blue-500/20 rounded-tr-none" 
            : isSystem
              ? "bg-red-500/5 text-red-100 border-red-500/20 rounded-tl-none"
              : "bg-white/5 dark:bg-gray-800/20 text-foreground border-white/5 rounded-tl-none",
          isThinking && "animate-pulse"
        )}>
          {isSystem && <div className="text-[10px] font-bold mb-2 uppercase tracking-widest text-red-500">System Trace</div>}
          
          <div className="text-sm md:text-base leading-relaxed whitespace-pre-wrap font-medium">
            {message.content}
          </div>
          
          {!isThinking && !isUser && !isSystem && (
            <div className="absolute -right-12 top-0 opacity-0 group-hover:opacity-100 transition-opacity">
              <CopyButton text={message.content} className="h-8 w-8 rounded-lg bg-gray-800/50 border border-white/10" />
            </div>
          )}

          {isThinking && (
            <div className="mt-4 pt-4 border-t border-white/5 space-y-3">
              <div className="flex items-center gap-2">
                 <div className="flex gap-1">
                    {[1, 2, 3].map(i => (
                      <span key={i} className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: `${i * 150}ms` }} />
                    ))}
                 </div>
                 <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest">Reasoning Logic active</span>
              </div>
              <div className="grid grid-cols-6 gap-0.5 h-1">
                 {Array.from({ length: 17 }).map((_, i) => (
                    <div key={i} className="bg-blue-500/40 rounded-full animate-pulse" style={{ animationDelay: `${i * 50}ms` }} />
                 ))}
              </div>
              <p className="text-[10px] text-gray-500 font-medium">Processing across 17 vectors of truth...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
