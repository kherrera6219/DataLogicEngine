'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Plus, Search, Calendar,
  Settings, Mic, Paperclip, Zap, ArrowRight, Target, Bot, User
} from "lucide-react";
import { ChatMessage, TracePipeline } from './types';
import { ApiChatMessage, ChatSession } from '@/lib/api/chat';
import { api, request, ApiError } from '@/lib/api';
import { socketClient, useSocket } from '@/lib/socket';
import {
  sanitizeFileName,
  sanitizeTextInput,
  validateUploadFile,
} from '@/lib/security/input-sanitization';
import { useFeatureFlags } from '@/contexts/FeatureFlagContext';
import { reportClientError } from '@/lib/telemetry/client-errors';
import { useToast } from '@/components/ui/use-toast';
import { LiveTracePanel } from './LiveTracePanel';
import { DetailedResponseView } from './DetailedResponseView';
import { TraceVisualizer } from './TraceVisualizer';
import { AdvancedControls } from './AdvancedControls';
import { ChatTracePanel } from './ChatTracePanel';

interface ChatInterfaceProps {
  autoOpenUpload?: boolean;
}

const MAX_CHAT_INPUT_LENGTH = 8_000;

type GatewayTracePayload = {
  run_id?: string | null;
  trace_id?: string | null;
  audit_trail?: ChatMessage['auditTrail'];
  provider_used?: string | null;
  model_used?: string | null;
};

type ChatTraceFields = Pick<ChatMessage, 'runId' | 'providerUsed' | 'modelUsed' | 'auditTrail'>;

function extractGatewayTraceFields(payload?: GatewayTracePayload | null): Partial<ChatTraceFields> {
  if (!payload) return {};
  const runId = payload.run_id || payload.trace_id || undefined;
  return {
    runId,
    providerUsed: payload.provider_used ?? undefined,
    modelUsed: payload.model_used ?? undefined,
    auditTrail: payload.audit_trail,
  };
}

function getGatewayErrorPayload(error: unknown): GatewayTracePayload | undefined {
  if (!(error instanceof ApiError) || !error.payload || typeof error.payload !== 'object') {
    return undefined;
  }
  return error.payload as GatewayTracePayload;
}

function formatMessageTimestamp(value?: string): string {
  if (!value) {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function normalizeApiMessage(message: ApiChatMessage): ChatMessage {
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    finalAnswer: message.role === 'assistant' ? message.content : undefined,
    timestamp: formatMessageTimestamp(message.timestamp),
    isEnhanced: message.is_enhanced ?? message.role === 'assistant',
    runId: message.run_id ?? undefined,
  };
}

export function ChatInterface({ autoOpenUpload = false }: ChatInterfaceProps) {
  const { isEnabled } = useFeatureFlags();
  const { toast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<'chat' | 'quad'>('chat');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const composerRef = useRef<HTMLTextAreaElement>(null);

  const strictInputSanitization = isEnabled('strictInputSanitization');

  // WebSocket Integration
  useSocket({
    onChatResponse: (data) => {
      if (data.session_id === currentSessionId) {
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.response,
          finalAnswer: data.response,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isEnhanced: true,
          ...extractGatewayTraceFields(data as GatewayTracePayload),
        };
        setMessages(prev => [...prev, assistantMsg]);
        setIsLoading(false);
      }
    },
    onChatTyping: (data) => {
      if (data.session_id === currentSessionId) {
        // Handle typing indicator if needed
      }
    }
  });

  // Load User Sessions on mount
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const data = await api.chat.listSessions();
        setSessions(data.sessions || []);
      } catch (err) {
        reportClientError(err, {
          module: 'ChatInterface',
          action: 'listSessions',
        });
      }
    };
    fetchSessions();
  }, []);

  // Auto-select first session when sessions are loaded (render-time derivation).
  if (sessions.length > 0 && !currentSessionId) {
    setCurrentSessionId(sessions[0].id);
  }

  // Hydrate history when session changes
  useEffect(() => {
    if (!currentSessionId) return;
    
    // Join WebSocket room for this session
    socketClient.joinRoom(`chat_${currentSessionId}`);

    const fetchHistory = async () => {
      try {
        const data = await api.chat.getSessionMessages(currentSessionId);
        if (data.messages?.length) {
          setMessages(data.messages.map(normalizeApiMessage));
        } else {
          setMessages([]);
        }
      } catch (err) {
        console.warn("Failed to load history, starting fresh.", err);
        setMessages([]);
      }
    };
    fetchHistory();

    return () => {
      socketClient.leaveRoom(`chat_${currentSessionId}`);
    };
  }, [currentSessionId]);

  const handleSend = async () => {
    const normalizedInput = strictInputSanitization
      ? sanitizeTextInput(inputValue, { maxLength: MAX_CHAT_INPUT_LENGTH })
      : inputValue.trim();

    if (!normalizedInput || isLoading) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: normalizedInput,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);

    try {
      // Use the centralized API
      const data = await api.chat.sendMessage({
        messages: [{ role: 'user', content: userMsg.content }],
        mode: mode,
        session_id: currentSessionId ?? undefined,
        run_ukg_pipeline: true
      });
      
      // If the API returns a direct response (not just via WS)
      if (data && data.response) {
        const traceFields = extractGatewayTraceFields(data);
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.response,
          finalAnswer: data.response,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isEnhanced: true,
          traces: data.trace_summary as TracePipeline | undefined,
          ...traceFields,
        };
        setMessages(prev => [...prev, assistantMsg]);
        setIsLoading(false);
      } else if ((data as { queued?: boolean }).queued) {
        const traceFields = extractGatewayTraceFields(data as GatewayTracePayload);
        const queuedMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'The local desktop queue saved this request for replay when providers are reachable.',
          finalAnswer: 'The local desktop queue saved this request for replay when providers are reachable.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          ...traceFields,
        };
        setMessages(prev => [...prev, queuedMsg]);
        setIsLoading(false);
      }
      
      // Refresh session list in case a new session was created
      const sessionData = await api.chat.listSessions();
      setSessions(sessionData.sessions || []);

    } catch (error) {
      reportClientError(error, {
        module: 'ChatInterface',
        action: 'sendMessage',
      });
      const errorPayload = getGatewayErrorPayload(error);

      // Rate-limit errors from the gateway (HTTP 429) must not be silently
      // queued offline — the provider is reachable, just throttled.  Show the
      // user a clear, actionable message instead.
      if (error instanceof ApiError && error.status === 429) {
        const rateLimitMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: 'The AI provider is currently rate limited. Please wait a moment and try again.',
          finalAnswer: 'The AI provider is currently rate limited. Please wait a moment and try again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          ...extractGatewayTraceFields(errorPayload),
        };
        setMessages(prev => [...prev, rateLimitMsg]);
        setIsLoading(false);
        return;
      }

      // For other errors, queue offline and show a generic message.
      await request('/gateway/offline-queue', {
        method: 'POST',
        body: JSON.stringify({
          reason: 'renderer_send_failure',
          payload: {
            messages: [{ role: 'user', content: userMsg.content }],
            mode,
            session_id: currentSessionId ?? undefined,
            run_ukg_pipeline: true,
          },
        }),
      }).catch(() => undefined);
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Your request could not be completed. In desktop mode it was added to the local offline queue when possible.',
        finalAnswer: 'Your request could not be completed. In desktop mode it was added to the local offline queue when possible.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        ...extractGatewayTraceFields(errorPayload),
      };
      setMessages(prev => [...prev, errorMsg]);
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setCurrentSessionId(crypto.randomUUID());
    setMessages([]);
  };

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!autoOpenUpload) return;
    const timer = window.setTimeout(() => {
      fileInputRef.current?.click();
    }, 150);

    return () => {
      window.clearTimeout(timer);
    };
  }, [autoOpenUpload]);

  useEffect(() => {
    if (autoOpenUpload) {
      return;
    }

    composerRef.current?.focus();
  }, [autoOpenUpload]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const validation = validateUploadFile(file);
    if (!validation.valid) {
      const validationErrorMessage = validation.reason || 'Unsupported file upload.';
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: validationErrorMessage,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
      event.target.value = '';
      return;
    }

    const safeFileName = sanitizeFileName(file.name);
    setIsLoading(true);
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: `Uploaded file: ${safeFileName}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const endpoint = file.type.startsWith('video/') 
        ? '/multimodal/video/analyze' 
        : '/multimodal/document/process';

      const data = await request<{ message?: string; result?: unknown; analysis?: unknown }>(endpoint, {
        method: 'POST',
        body: formData
      });
      
      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `File processed successfully. Analysis: ${data.message || JSON.stringify(data.result || data.analysis)}`,
        finalAnswer: `File processed successfully. Analysis: ${data.message || JSON.stringify(data.result || data.analysis)}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isEnhanced: true
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      reportClientError(error, {
        module: 'ChatInterface',
        action: 'fileUpload',
      });
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Failed to process the uploaded file.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      event.target.value = '';
    }
  };

  const latestTrace = useMemo<TracePipeline | null>(() => {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      const trace = messages[i].traces;
      if (trace?.steps?.length) {
        return trace;
      }
    }
    return null;
  }, [messages]);

  const hasExecutedQuery = useMemo(
    () => messages.some((message) => message.role === 'user'),
    [messages]
  );

  return (
    <div className="flex h-full text-gray-900 dark:text-white font-sans overflow-hidden">
      
      {/* ðŸ“ Conversational Sidebar */}
      <aside className="w-64 border-r border-white/5 flex flex-col fluent-acrylic z-20" aria-label="Recent chat sessions">
         <div className="p-4 border-b border-white/5 space-y-4">
            <Button 
              className="w-full justify-start gap-2 bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-900/20"
              onClick={handleNewChat}
              data-testid="new-chat-button"
            >
               <Plus className="h-4 w-4" /> New Chat
            </Button>
            <div className="relative">
               <Search className="absolute left-2 top-2.5 h-4 w-4 text-slate-500 dark:text-gray-400" aria-hidden="true" />
               <Input
                 placeholder="Search..."
                 aria-label="Search chat sessions"
                 className="pl-8 bg-white/80 dark:bg-black/20 border-slate-300/70 dark:border-white/5 h-9 focus:bg-white dark:focus:bg-black/40 transition-colors"
               />
            </div>
         </div>
         
         <ScrollArea className="flex-1">
            <div className="p-4 space-y-6">
               <div>
                  <h3 className="text-xs font-bold text-slate-500 dark:text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                     <Calendar className="h-3 w-3" /> Recent Sessions
                  </h3>
                  <div className="space-y-1">
                     {sessions.length > 0 ? (
                       sessions.map((s) => (
                        <Button 
                          key={s.id} 
                          variant="ghost" 
                          className={cn(
                            "w-full justify-start text-sm h-10 px-2 font-normal hover:bg-slate-200/70 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-white rounded-md truncate",
                            currentSessionId === s.id ? "bg-slate-200 dark:bg-white/10 text-slate-900 dark:text-white font-medium border border-slate-300/70 dark:border-white/5" : "text-slate-600 dark:text-gray-400"
                          )}
                          onClick={() => setCurrentSessionId(s.id)}
                        >
                           {s.title || "Untitled Session"}
                        </Button>
                       ))
                     ) : (
                       <div className="text-xs text-slate-500 dark:text-gray-600 px-2 italic py-4">No recent sessions found</div>
                     )}
                  </div>
               </div>
            </div>
         </ScrollArea>
         
         <div className="p-4 border-t border-white/5">
            <div className="flex justify-between">
               <Button variant="ghost" size="sm" className="text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-white/5">Export</Button>
               <Button variant="ghost" size="sm" className="text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-white/5">Clear All</Button>
            </div>
         </div>
      </aside>

      {/* ðŸ’¬ Main Chat Area */}
      <main className="flex-1 flex flex-col relative z-10 bg-transparent" data-testid="main-chat-area" role="main" aria-label="Chat interface">
         {/* Header */}
         <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 fluent-acrylic sticky top-0 z-30">
            <h1 className="font-bold text-sm tracking-wide flex items-center gap-2 text-slate-900 dark:text-gray-100" data-testid="app-header">
               <Target className="h-4 w-4 text-blue-500" /> UKG Enterprise AI Assistant
            </h1>
            <div className="flex items-center gap-3">
               <span className="text-xs text-slate-600 dark:text-gray-400">
                 {currentSessionId ? `Session ${currentSessionId.slice(0, 8)}` : 'No active session'}
               </span>
               <Button variant="ghost" size="sm" className="h-8 gap-2 border border-slate-300/70 dark:border-white/10 hover:bg-slate-200/70 dark:hover:bg-white/5 text-slate-700 dark:text-gray-300">
                  <Settings className="h-3.5 w-3.5" /> Settings
               </Button>
               <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-slate-200/70 dark:hover:bg-white/5 relative group">
                  <span className="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)] group-hover:shadow-[0_0_15px_rgba(34,197,94,0.8)] transition-all"></span>
               </Button>
            </div>
         </div>

         {/* Messages */}
         <div className="flex-1 overflow-y-auto p-6 space-y-6" data-testid="messages-container" aria-live="polite" aria-busy={isLoading}>
            {messages.map((msg) => (
                <div key={msg.id} data-testid="message-item" className={`flex gap-4 animate-in ...`}>
                   <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-lg ${msg.role === 'assistant' ? 'bg-blue-600' : 'bg-slate-200 dark:bg-[#2a2a2a] border border-slate-300/70 dark:border-white/10'}`}>
                      {msg.role === 'assistant' ? <Bot className="h-4 w-4 text-white" /> : <User className="h-4 w-4 text-slate-600 dark:text-gray-300" />}
                   </div>
                   <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                         <span className="font-bold text-sm text-slate-900 dark:text-gray-200">{msg.role === 'assistant' ? 'UKG Assistant' : 'User'}</span>
                         <span className="text-xs text-slate-500 dark:text-gray-500">{msg.timestamp}</span>
                      </div>
                      
                      {msg.role === 'assistant' && msg.isEnhanced && (
                         <div className="flex items-center gap-2 text-xs text-blue-400 bg-blue-500/10 px-2 py-1 rounded-md w-fit mb-2 border border-blue-500/20">
                            <Zap className="h-3 w-3" /> Enhanced Mode Active
                         </div>
                      )}

                      {msg.role === 'assistant' && (msg.providerUsed || msg.modelUsed) && (
                         <div className="flex items-center gap-1.5 text-xs text-violet-400 bg-violet-500/10 px-2 py-1 rounded-md w-fit mb-2 border border-violet-500/20 font-mono">
                            <Target className="h-3 w-3 shrink-0" />
                            <span>
                              {msg.providerUsed && msg.modelUsed
                                ? `${msg.providerUsed} / ${msg.modelUsed}`
                                : msg.modelUsed ?? msg.providerUsed}
                            </span>
                         </div>
                      )}

                      <div className="text-sm leading-relaxed text-slate-700 dark:text-gray-300">
                         {msg.role === 'assistant' ? (
                            <div className="space-y-4">
                               <div>{msg.finalAnswer || msg.content}</div>

                               {/* Detailed Response Analysis */}
                               <DetailedResponseView message={msg} />

                               {(msg.runId || msg.auditTrail) && (
                                  <ChatTracePanel runId={msg.runId} auditTrail={msg.auditTrail} />
                               )}
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
            <div className="max-w-4xl mx-auto bg-white/80 dark:bg-black/40 border border-slate-300/70 dark:border-white/10 rounded-2xl p-2 relative shadow-2xl backdrop-blur-md transition-all focus-within:ring-1 focus-within:ring-blue-500/30 focus-within:bg-white dark:focus-within:bg-black/60">
               <textarea 
                  ref={composerRef}
                  className="w-full bg-transparent border-none focus:ring-0 text-slate-900 dark:text-gray-200 text-sm p-3 min-h-[60px] resize-none pr-32 placeholder:text-slate-400 dark:placeholder:text-gray-600"
                  placeholder="Ask a compliance question..."
                  aria-label="Message composer"
                  aria-keyshortcuts="Control+Enter Meta+Enter"
                  value={inputValue}
                  onChange={(e) => {
                    const nextValue = strictInputSanitization
                      ? sanitizeTextInput(e.target.value, {
                          maxLength: MAX_CHAT_INPUT_LENGTH,
                          trim: false,
                        })
                      : e.target.value;
                    setInputValue(nextValue);
                  }}
                  onKeyDown={(event) => {
                    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
                      event.preventDefault();
                      void handleSend();
                    }
                  }}
               />
                <div className="absolute bottom-2 left-3 flex gap-1">
                  <input 
                    type="file" 
                    className="hidden" 
                    ref={fileInputRef} 
                    onChange={handleFileUpload}
                    aria-label="Upload file for analysis"
                    title="Upload file"
                  />
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8 text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-white/5 rounded-lg"
                    onClick={() => fileInputRef.current?.click()}
                    aria-label="Attach file"
                  >
                    <Paperclip className="h-4 w-4" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="h-8 w-8 text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-white/5 rounded-lg"
                    onClick={() => toast("Voice input is not available in this deployment.", "info", 3000)}
                    aria-label="Start voice input"
                  >
                    <Mic className="h-4 w-4" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className={`h-8 w-8 rounded-lg transition-colors ${mode === 'quad' ? 'text-yellow-400 bg-yellow-400/10' : 'text-yellow-500/80 hover:text-yellow-400 hover:bg-yellow-400/10'}`}
                    onClick={() => setMode(prev => prev === 'chat' ? 'quad' : 'chat')}
                    aria-label="Toggle Quad Persona Mode"
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
            
            <p className="max-w-4xl mx-auto mt-2 text-[11px] leading-relaxed text-slate-500 dark:text-gray-500">
              AI requests require internet access and may send your prompt, attachments, and selected context to the configured provider. Verify generated responses before using them for critical decisions.
            </p>

             <div className="max-w-4xl mx-auto mt-4">
               <TraceVisualizer trace={latestTrace} hasExecutedQuery={hasExecutedQuery} />
             </div>

            <div className="text-center text-[10px] text-slate-500 dark:text-gray-600 mt-2 font-mono">DataLogicEngine AI workspace</div>
         </div>
      </main>

      {/* ðŸ”¬ Live Trace Sidebar */}
      <aside className="w-72 border-l border-white/5 flex flex-col fluent-acrylic z-20" aria-label="Live trace panel">
         <LiveTracePanel />
      </aside>

    </div>
  );
}
