'use client';

import { useState, useRef, useEffect } from 'react';
import { Message, sendChat } from '@/lib/api';
import { MessageBubble } from './MessageBubble';
import { Sparkles, Send, Terminal, ShieldCheck, Bot } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await sendChat({
        messages: [...messages, userMsg],
        run_ukg_pipeline: true,
        mode: 'chat'
      });

      const assistantMsg: Message = { role: 'assistant', content: response.response };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error(error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to connect to Gateway';
      const errorMsg: Message = {
        role: 'system',
        content: `Error: ${errorMessage}. \n\nCheck if the backend is running at localhost:5000.`
      };
      setMessages(prev => [...prev, errorMsg]);
      toast("Intelligence Pipeline Disrupted", "error", 4000);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-5xl mx-auto w-full" role="application" aria-label="Intelligence Chat Interface">
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto mb-6 p-6 rounded-3xl bg-black/10 backdrop-blur-sm border border-white/5 scroll-smooth no-scrollbar"
        role="log"
        aria-live="polite"
        aria-label="Conversation history"
      >
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 scale-in-center">
            <div className="w-20 h-20 bg-blue-500/20 rounded-3xl flex items-center justify-center mb-6 border border-blue-500/30 animate-pulse shadow-2xl shadow-blue-500/20">
               <Sparkles className="h-10 w-10 text-blue-500" aria-hidden="true" />
            </div>
            <h2 className="text-3xl font-bold mb-3 tracking-tighter">Intelligence <span className="text-blue-500">Gateway</span></h2>
            <p className="max-w-md mx-auto mb-10 text-muted-foreground text-sm font-medium">
              Enterprise Knowledge Graph system with hardened 17-axis reasoning. 
              Ask about compliance benchmarks, pillar definitions, or expert personas.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl w-full" role="group" aria-label="Suggested queries">
              {[
                { label: "17-Axis reasoning guide", icon: Terminal },
                { label: "Analyze GDPR vs NIST 800-171", icon: ShieldCheck },
                { label: "Honeycomb expansion logic", icon: Sparkles },
                { label: "Simulate audit persona", icon: Bot }
              ].map(({ label, icon: Icon }) => (
                <button 
                  key={label}
                  onClick={() => setInput(label)}
                  className="group flex items-center gap-3 p-4 bg-white/5 border border-white/5 rounded-2xl hover:bg-blue-600/10 hover:border-blue-500/30 transition-all text-left outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                  aria-label={`Ask: ${label}`}
                >
                  <div className="p-2 bg-gray-800/50 rounded-lg group-hover:text-blue-500 transition-colors">
                    <Icon className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <span className="text-sm font-semibold">{label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
        
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        
        {isLoading && (
          <MessageBubble 
            message={{ role: 'assistant', content: 'Processing knowledge graph...' }} 
            isThinking 
          />
        )}
      </div>

      <div className="bg-black/20 backdrop-blur-xl p-2 rounded-2xl border border-white/5 shadow-2xl">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Interrogate the graph..."
            disabled={isLoading}
            className="flex-1 p-4 bg-transparent outline-none text-foreground placeholder-gray-500 text-sm md:text-base font-medium"
            aria-label="Ask the knowledge graph a question"
          />
          <button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-lg shadow-blue-500/20 font-bold disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center gap-2 outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="Send message"
          >
            <span className="hidden sm:inline">Dispatch</span>
            <Send className="w-4 h-4" aria-hidden="true" />
          </button>
        </form>
      </div>
    </div>
  );
}
