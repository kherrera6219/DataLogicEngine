import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Plus, Search, Pin, Calendar, Folder, 
  Settings, Mic, Paperclip, Zap, ArrowRight 
} from "lucide-react";
import { ChatMessage } from './types';
import { LiveTracePanel } from './LiveTracePanel';
import { DetailedResponseView } from './DetailedResponseView';
import { TraceVisualizer } from './TraceVisualizer';
import { AdvancedControls } from './AdvancedControls';

// API call helper
async function callGateway(content: string, mode: string = 'chat') {
  const response = await fetch('/api/v1/gateway/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: [{ role: 'user', content }],
      mode: mode,
      run_ukg_pipeline: true
    })
  });
  if (!response.ok) throw new Error('Gateway request failed');
  return response.json();
}

async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const endpoint = file.type.startsWith('video/') 
    ? '/api/v1/multimodal/video/analyze' 
    : '/api/v1/multimodal/document/process';

  const response = await fetch(endpoint, {
    method: 'POST',
    body: formData
  });
  if (!response.ok) throw new Error('File processing failed');
  return response.json();
}

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<'chat' | 'quad'>('chat');

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);

    try {
      const data = await callGateway(userMsg.content, mode);
      
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        finalAnswer: data.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isEnhanced: true,
        traces: data.trace_summary // Optional trace data
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error(error);
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I encountered an error while processing your request. Please check your connection and try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: `Uploaded file: ${file.name}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const data = await uploadFile(file);
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        finalAnswer: `File processed successfully. Analysis: ${JSON.stringify(data.result || data.analysis)}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isEnhanced: true
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error(error);
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Failed to process the uploaded file.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full text-white font-sans overflow-hidden">
      
      {/* 📁 Conversational Sidebar */}
      <div className="w-64 border-r border-white/5 flex flex-col fluent-acrylic z-20">
         <div className="p-4 border-b border-white/5 space-y-4">
            <Button className="w-full justify-start gap-2 bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-900/20">
               <Plus className="h-4 w-4" /> New Chat
            </Button>
            <div className="relative">
               <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
               <Input placeholder="Search..." className="pl-8 bg-black/20 border-white/5 h-9 focus:bg-black/40 transition-colors" />
            </div>
         </div>
         
         <ScrollArea className="flex-1">
            <div className="p-4 space-y-6">
               <div>
                  <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                     <Pin className="h-3 w-3" /> Pinned
                  </h3>
                  <div className="space-y-1">
                     <Button variant="ghost" className="w-full justify-start text-sm text-gray-300 h-8 px-2 font-normal hover:bg-white/5 hover:text-white rounded-md">
                        Compliance Q&A
                     </Button>
                     <Button variant="ghost" className="w-full justify-start text-sm text-gray-300 h-8 px-2 font-normal hover:bg-white/5 hover:text-white rounded-md">
                        Risk Analysis
                     </Button>
                  </div>
               </div>

               <div>
                  <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                     <Calendar className="h-3 w-3" /> Recent
                  </h3>
                  <div className="space-y-1">
                     <Button variant="ghost" className="w-full justify-start text-sm text-gray-300 h-8 px-2 font-normal hover:bg-white/5 hover:text-white rounded-md">
                        Today (8)
                     </Button>
                     <Button variant="ghost" className="w-full justify-start text-sm text-gray-300 h-8 px-2 font-normal hover:bg-white/5 hover:text-white rounded-md">
                        Yesterday (12)
                     </Button>
                     <Button variant="ghost" className="w-full justify-start text-sm text-gray-300 h-8 px-2 font-normal hover:bg-white/5 hover:text-white rounded-md">
                        Last Week (45)
                     </Button>
                  </div>
               </div>
               
               <div>
                  <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                     <Folder className="h-3 w-3" /> By Topic
                  </h3>
                  <div className="space-y-1">
                     {['Healthcare', 'Financial', 'Legal', 'Technical', 'Operations'].map(topic => (
                        <Button key={topic} variant="ghost" className="w-full justify-start text-sm text-gray-300 h-8 px-2 font-normal hover:bg-white/5 hover:text-white rounded-md">
                           {topic}
                        </Button>
                     ))}
                  </div>
               </div>
            </div>
         </ScrollArea>
         
         <div className="p-4 border-t border-white/5">
            <div className="flex justify-between">
               <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-white/5">Export</Button>
               <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-white/5">Clear All</Button>
            </div>
         </div>
      </div>

      {/* 💬 Main Chat Area */}
      <div className="flex-1 flex flex-col relative z-10 bg-transparent">
         {/* Header */}
         <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 fluent-acrylic sticky top-0 z-30">
            <h1 className="font-bold text-sm tracking-wide flex items-center gap-2 text-gray-100">
               🎯 UKG Enterprise AI Assistant
            </h1>
            <div className="flex items-center gap-3">
               <span className="text-xs text-gray-400">@username</span>
               <Button variant="ghost" size="sm" className="h-8 gap-2 border border-white/10 hover:bg-white/5 text-gray-300">
                  <Settings className="h-3.5 w-3.5" /> Settings
               </Button>
               <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-white/5 relative group">
                  <span className="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)] group-hover:shadow-[0_0_15px_rgba(34,197,94,0.8)] transition-all"></span>
               </Button>
            </div>
         </div>

         {/* Messages */}
         <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg) => (
                <div key={msg.id} className={`flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-500 ${msg.role === 'assistant' ? 'bg-white/5 p-6 rounded-2xl border border-white/5 backdrop-blur-sm shadow-sm' : ''}`}>
                   <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-lg ${msg.role === 'assistant' ? 'bg-blue-600' : 'bg-[#2a2a2a] border border-white/10'}`}>
                      {msg.role === 'assistant' ? '🤖' : '👤'}
                   </div>
                   <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                         <span className="font-bold text-sm text-gray-200">{msg.role === 'assistant' ? 'UKG Assistant' : 'User'}</span>
                         <span className="text-xs text-gray-500">{msg.timestamp}</span>
                      </div>
                      
                      {msg.role === 'assistant' && msg.isEnhanced && (
                         <div className="flex items-center gap-2 text-xs text-blue-400 bg-blue-500/10 px-2 py-1 rounded-md w-fit mb-2 border border-blue-500/20">
                            <Zap className="h-3 w-3" /> Enhanced Mode Active
                         </div>
                      )}

                      <div className="text-sm leading-relaxed text-gray-300">
                         {msg.role === 'assistant' ? (
                            <div className="space-y-4">
                               <p className="italic text-gray-400">Let me analyze this through the UKG validation framework...</p>
                               <div className="bg-black/20 rounded-lg p-3 text-xs space-y-1 font-mono text-gray-400 border border-white/5 shadow-inner">
                                  <div className="flex items-center gap-2 text-green-400"><span className="text-green-500">✓</span> TruthGate Security Screening</div>
                                  <div className="flex items-center gap-2"><span className="animate-pulse text-yellow-500">⏳</span> 17-Axis Coordinate Resolution</div>
                                  <div className="flex items-center gap-2"><span className="animate-pulse text-yellow-500">⏳</span> Quad Persona Analysis</div>
                                  <div className="flex items-center gap-2"><span className="animate-pulse text-yellow-500">⏳</span> 12-Step Refinement</div>
                               </div>
                               
                               <div className="mt-4 pt-4 border-t border-white/5">
                                  {msg.finalAnswer}
                                </div>

                               {/* Detailed Response Analysis */}
                               <DetailedResponseView message={msg} />
                            </div>
                         ) : (
                            msg.content
                         )}
                      </div>
                   </div>
                </div>
            ))}
         </div>

         {/* Input Area */}
         <div className="p-4 border-t border-white/5 fluent-acrylic z-20">
            <div className="max-w-4xl mx-auto bg-black/40 border border-white/10 rounded-2xl p-2 relative shadow-2xl backdrop-blur-md transition-all focus-within:ring-1 focus-within:ring-blue-500/30 focus-within:bg-black/60">
               <textarea 
                  className="w-full bg-transparent border-none focus:ring-0 text-gray-200 text-sm p-3 min-h-[60px] resize-none pr-32 placeholder:text-gray-600"
                  placeholder="Ask a compliance question..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
               />
                <div className="absolute bottom-2 left-3 flex gap-1">
                  <input 
                    type="file" 
                    className="hidden" 
                    ref={fileInputRef} 
                    onChange={handleFileUpload}
                    aria-label="Upload file for analysis"
                  />
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Paperclip className="h-4 w-4" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg"
                    onClick={() => alert("Audio capture initializing... Production bridge active.")}
                  >
                    <Mic className="h-4 w-4" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className={`h-8 w-8 rounded-lg transition-colors ${mode === 'quad' ? 'text-yellow-400 bg-yellow-400/10' : 'text-yellow-500/80 hover:text-yellow-400 hover:bg-yellow-400/10'}`}
                    onClick={() => setMode(prev => prev === 'chat' ? 'quad' : 'chat')}
                  >
                    <Zap className="h-4 w-4" />
                  </Button>
                  <AdvancedControls />
                </div>
                <Button 
                  className="absolute bottom-2 right-2 bg-blue-600 hover:bg-blue-500 h-8 px-4 text-xs font-bold gap-2 rounded-lg shadow-lg shadow-blue-900/20 transition-all hover:scale-105"
                  onClick={handleSend}
                  disabled={isLoading}
                >
                  {isLoading ? '...' : 'Send'} <ArrowRight className="h-3 w-3" />
                </Button>
            </div>
            
            <div className="max-w-4xl mx-auto mt-4">
               <TraceVisualizer />
            </div>

            <div className="text-center text-[10px] text-gray-600 mt-2 font-mono">UKG AI v2.1.0 • Enterprise Edition • Confidential</div>
         </div>
      </div>

      {/* 🔬 Live Trace Sidebar */}
      <div className="w-72 border-l border-white/5 flex flex-col fluent-acrylic z-20">
         <LiveTracePanel />
      </div>

    </div>
  );
}
