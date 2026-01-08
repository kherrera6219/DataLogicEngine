import { Message } from '@/lib/api';
import { cn } from '@/lib/utils';

interface Props {
  message: Message;
  isThinking?: boolean;
}

export function MessageBubble({ message, isThinking }: Props) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  
  return (
    <div className={cn("flex w-full mb-4", isUser ? "justify-end" : "justify-start")}>
      <div className={cn(
        "max-w-[85%] p-4 rounded-2xl shadow-sm",
        isUser 
          ? "bg-blue-600 text-white rounded-br-none" 
          : isSystem
            ? "bg-red-50 text-red-800 border border-red-200"
            : "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-100 dark:border-gray-700 rounded-bl-none",
        isThinking && "animate-pulse"
      )}>
        {isSystem && <div className="text-xs font-bold mb-1 uppercase tracking-wider">System Alert</div>}
        <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
        
        {isThinking && (
          <div className="flex items-center gap-2 mt-3 text-xs opacity-70 border-t border-gray-200 dark:border-gray-700 pt-2">
            <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></span>
            <span>Reasoning across 17 knowledge axes...</span>
          </div>
        )}
      </div>
    </div>
  );
}
