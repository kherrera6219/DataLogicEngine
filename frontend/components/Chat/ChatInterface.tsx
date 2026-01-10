'use client';

import { useState, useRef, useEffect } from 'react';
import { Message, sendChat } from '@/lib/api';
import { MessageBubble } from './MessageBubble';

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
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
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] max-w-5xl mx-auto w-full">
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto mb-6 p-6 rounded-2xl bg-gray-50/50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 shadow-inner"
      >
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center text-gray-500 p-8">
            <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold mb-2 text-gray-800 dark:text-gray-100">DataLogicEngine UKG</h2>
            <p className="max-w-md mx-auto mb-8">
              Enterprise Knowledge Graph system with 17-axis reasoning. 
              Ask about compliance, pillar definitions, or expert personas.
            </p>
            <div className="grid grid-cols-2 gap-2 max-w-lg w-full">
              {[
                "What are the 17 axes of knowledge?",
                "Analyze GDPR compliance for healthcare",
                "Explain the Honeycomb expansion algorithm",
                "Simulate a regulatory expert debate"
              ].map(q => (
                <button 
                  key={q}
                  onClick={() => setInput(q)}
                  className="text-sm p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 hover:text-blue-600 transition-colors text-left"
                >
                  {q}
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

      <div className="bg-white dark:bg-gray-900 p-2 rounded-xl border border-gray-200 dark:border-gray-800 shadow-lg">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            disabled={isLoading}
            className="flex-1 p-4 bg-transparent outline-none text-gray-800 dark:text-gray-100 placeholder-gray-400"
          />
          <button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            <span>Send</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
