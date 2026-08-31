'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import Link from 'next/link';
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Plus, Search, Calendar,
  Settings, Mic, Paperclip, Zap, ArrowRight, Target, Bot, User, X
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
import { ChatTracePanel } from './ChatTracePanel';
import { OfflineQueueManager } from './OfflineQueueManager';
import { ConfidenceDisplayCard } from './ConfidenceDisplayCard';

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
  completion?: ChatMessage['completion'];
  mode?: ChatMessage['governedMode'];
  confidence_display?: ChatMessage['confidenceDisplay'];
  provider_call_budget?: ChatMessage['providerCallBudget'];
  failure?: {
    kind?: string;
    details?: {
      provider_failure?: { class?: string };
    };
  } | null;
};

type ChatTraceFields = Pick<ChatMessage, 'runId' | 'providerUsed' | 'modelUsed' | 'auditTrail'>;

type ProviderBudgetSnapshot = {
  limits: {
    daily_calls: number;
    monthly_calls: number;
    daily_tokens: number;
    monthly_tokens: number;
  };
  daily: { calls: number; tokens_total: number };
  monthly: { calls: number; tokens_total: number; unknown_price_calls: number };
  remaining: { daily_calls: number; monthly_calls: number; daily_tokens: number; monthly_tokens: number };
  pricing_status: 'available' | 'unknown';
};

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

function replayableFailureClass(
  error: unknown,
  payload?: GatewayTracePayload,
): 'network' | 'provider_outage' | 'timeout' | null {
  const classified = payload?.failure?.details?.provider_failure?.class;
  if (classified === 'network' || classified === 'provider_outage' || classified === 'timeout') {
    return classified;
  }
  if (payload?.failure?.kind === 'timeout') return 'timeout';
  if (!(error instanceof ApiError) && error instanceof Error && /failed to fetch|network|reachable/i.test(error.message)) {
    return 'network';
  }
  return null;
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
    isEnhanced: message.is_enhanced,
    governedMode: message.mode
      ?? (message.role === 'assistant'
        ? (message.is_enhanced ? 'enhanced' : 'standard')
        : undefined),
    runId: message.run_id ?? undefined,
    completion: message.completion,
    confidenceDisplay: message.confidence_display,
    providerCallBudget: message.provider_call_budget,
  };
}

export function ChatInterface({ autoOpenUpload = false }: ChatInterfaceProps) {
  const { isEnabled } = useFeatureFlags();
  const { toast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeRequestId, setActiveRequestId] = useState<string | null>(null);
  const [providerBudget, setProviderBudget] = useState<ProviderBudgetSnapshot | null>(null);
  const [mode, setMode] = useState<'chat' | 'quad'>('chat');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const draftSessionIdRef = useRef<string | null>(null);
  const sessionCreationRef = useRef<Promise<ChatSession> | null>(null);
  const freshSessionIdsRef = useRef<Set<string>>(new Set());

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
          governedMode: data.mode,
          confidenceDisplay: data.confidence_display,
          providerCallBudget: data.provider_call_budget,
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
        const loadedSessions = data.sessions || [];
        setSessions(loadedSessions);
        setCurrentSessionId((selected) => selected ?? loadedSessions[0]?.id ?? null);
      } catch (err) {
        reportClientError(err, {
          module: 'ChatInterface',
          action: 'listSessions',
        });
      }
    };
    fetchSessions();
  }, []);

  useEffect(() => {
    request<ProviderBudgetSnapshot>('/gateway/usage-ledger?days=30')
      .then((result) => setProviderBudget(
        result?.daily && result?.monthly && result?.limits && result?.remaining
          ? result
          : null
      ))
      .catch(() => setProviderBudget(null));
  }, []);

  // Hydrate history when session changes
  useEffect(() => {
    if (!currentSessionId) return;
    
    // Join WebSocket room for this session
    socketClient.joinRoom(`chat_${currentSessionId}`);

    const isFreshSession = freshSessionIdsRef.current.delete(currentSessionId);
    const fetchHistory = async () => {
      if (isFreshSession) return;
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

  const ensureCurrentSession = async (): Promise<string> => {
    if (currentSessionId) return currentSessionId;

    if (!draftSessionIdRef.current) {
      draftSessionIdRef.current = crypto.randomUUID();
    }
    if (!sessionCreationRef.current) {
      sessionCreationRef.current = api.chat.createSession({
        session_id: draftSessionIdRef.current,
        mode,
      }).then(({ session }) => {
        freshSessionIdsRef.current.add(session.id);
        setCurrentSessionId(session.id);
        setSessions((existing) => [
          session,
          ...existing.filter((item) => item.id !== session.id),
        ]);
        return session;
      }).finally(() => {
        sessionCreationRef.current = null;
      });
    }
    return (await sessionCreationRef.current).id;
  };

  const handleSend = async () => {
    const normalizedInput = strictInputSanitization
      ? sanitizeTextInput(inputValue, { maxLength: MAX_CHAT_INPUT_LENGTH })
      : inputValue.trim();

    if (!normalizedInput || isLoading) return;

    const budgetRatios = providerBudget
      ? [
          providerBudget.daily.calls / Math.max(1, providerBudget.limits.daily_calls),
          providerBudget.monthly.calls / Math.max(1, providerBudget.limits.monthly_calls),
          providerBudget.daily.tokens_total / Math.max(1, providerBudget.limits.daily_tokens),
          providerBudget.monthly.tokens_total / Math.max(1, providerBudget.limits.monthly_tokens),
        ]
      : [];
    const budgetWarningRequired = Math.max(0, ...budgetRatios) >= 0.8;
    const budgetWarningConfirmed = budgetWarningRequired
      ? window.confirm('Provider usage has crossed an 80% warning threshold. Send this governed request within the remaining server limit?')
      : false;
    if (budgetWarningRequired && !budgetWarningConfirmed) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: normalizedInput,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);
    const requestId = crypto.randomUUID();
    setActiveRequestId(requestId);
    let sessionId = currentSessionId ?? undefined;

    try {
      sessionId = await ensureCurrentSession();
      // Use the centralized API
      const data = await api.chat.sendMessage({
        messages: [{ role: 'user', content: userMsg.content }],
        request_id: requestId,
        mode: mode,
        session_id: sessionId,
        run_ukg_pipeline: true,
        meta: { budget_warning_confirmed: budgetWarningConfirmed },
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
          governedMode: data.mode,
          traces: data.trace_summary as TracePipeline | undefined,
          ...traceFields,
          completion: data.completion,
          confidenceDisplay: data.confidence_display,
          providerCallBudget: data.provider_call_budget,
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
      const sessionData = await api.chat.listSessions().catch(() => null);
      if (sessionData) {
        setSessions(sessionData.sessions || []);
      }
      setActiveRequestId(null);

    } catch (error) {
      reportClientError(error, {
        module: 'ChatInterface',
        action: 'sendMessage',
      });
      const errorPayload = getGatewayErrorPayload(error);
      const failureClass = replayableFailureClass(error, errorPayload);

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
        setActiveRequestId(null);
        return;
      }

      let queuedLocally = false;
      if (failureClass) {
        queuedLocally = await request('/gateway/offline-queue', {
          method: 'POST',
          body: JSON.stringify({
            failure_class: failureClass,
            payload: {
              request_id: requestId,
              messages: [{ role: 'user', content: userMsg.content }],
              mode,
              session_id: sessionId,
              run_ukg_pipeline: true,
            },
          }),
        }).then(() => true).catch(() => false);
      }
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: queuedLocally
          ? 'Your request could not be completed and was added to the encrypted local replay queue.'
          : failureClass
            ? 'Your request could not be completed. Encrypted replay is disabled or unavailable, so it was not queued.'
            : 'Your request could not be completed. This failure is not safe to replay automatically.',
        finalAnswer: queuedLocally
          ? 'Your request could not be completed and was added to the encrypted local replay queue.'
          : failureClass
            ? 'Your request could not be completed. Encrypted replay is disabled or unavailable, so it was not queued.'
            : 'Your request could not be completed. This failure is not safe to replay automatically.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        ...extractGatewayTraceFields(errorPayload),
      };
      setMessages(prev => [...prev, errorMsg]);
      setIsLoading(false);
      setActiveRequestId(null);
    }
  };

  const handleCancel = async () => {
    if (!activeRequestId) return;
    await request(`/gateway/requests/${activeRequestId}/cancel`, { method: 'POST' })
      .then(() => toast('Cancellation requested.', 'info', 2500))
      .catch(() => toast('The request already finished or could not be cancelled.', 'warning', 3000));
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    draftSessionIdRef.current = null;
    sessionCreationRef.current = null;
    setMessages([]);
  };

  const prepareContinuation = () => {
    setInputValue(
      'Continue the prior answer from where it stopped. Do not repeat completed material. Finish the unanswered parts of my request.',
    );
    window.requestAnimationFrame(() => composerRef.current?.focus());
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
        isEnhanced: false
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
               <Button asChild variant="ghost" size="sm" className="h-8 gap-2 border border-slate-300/70 dark:border-white/10 hover:bg-slate-200/70 dark:hover:bg-white/5 text-slate-700 dark:text-gray-300">
                  <Link href="/settings"><Settings className="h-3.5 w-3.5" /> Settings</Link>
               </Button>
                <span
                 className="flex h-8 items-center gap-2 rounded-md border border-slate-300/70 px-2 text-[10px] text-slate-600 dark:border-white/10 dark:text-gray-400"
                 title={providerBudget ? 'The durable provider usage ledger is available.' : 'Provider usage status is unavailable.'}
               >
                 <span className={`h-2 w-2 rounded-full ${providerBudget ? 'bg-green-500' : 'bg-amber-500'}`} aria-hidden="true" />
                  {providerBudget ? 'Usage available' : 'Usage unavailable'}
                </span>
                <OfflineQueueManager />
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
                      
                      {msg.role === 'assistant' && msg.governedMode && (
                         <div className="flex items-center gap-2 text-xs text-blue-600 dark:text-blue-400 bg-blue-500/10 px-2 py-1 rounded-md w-fit mb-2 border border-blue-500/20">
                            <Zap className="h-3 w-3" />
                            {msg.governedMode === 'enhanced'
                              ? 'Enhanced Mode'
                              : msg.governedMode === 'local_review'
                                ? 'Local Review Mode'
                                : 'Standard Mode'}
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

                               {msg.governedMode && (
                                 <div className="text-xs text-slate-500 dark:text-slate-400">
                                   {msg.providerCallBudget
                                     ? `${msg.providerCallBudget.calls_used} of ${msg.providerCallBudget.max_calls} provider attempts used for this governed run.`
                                     : 'Provider-attempt budget was not recorded for this historical message.'}
                                 </div>
                               )}

                               {msg.confidenceDisplay && (
                                 <ConfidenceDisplayCard display={msg.confidenceDisplay} compact />
                               )}

                               {msg.completion?.disposition === 'length_limited' && (
                                 <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-amber-800 dark:text-amber-200">
                                   <p className="font-medium">Answer reached the provider output limit.</p>
                                   <p className="mt-1 text-xs">
                                     This response is incomplete. Continuing uses another governed provider attempt and remains subject to the displayed usage budget.
                                   </p>
                                   <Button
                                     type="button"
                                     variant="outline"
                                     size="sm"
                                     className="mt-3"
                                     aria-label="Prepare continuation"
                                     onClick={prepareContinuation}
                                   >
                                     Prepare continuation
                                   </Button>
                                 </div>
                               )}

                               {msg.completion?.disposition === 'provider_incomplete' && (
                                 <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-200">
                                   The provider returned content but did not confirm that the response completed normally.
                                 </div>
                               )}

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
                    disabled
                    title="Voice input is not available in this deployment."
                    aria-label="Voice input unavailable"
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
                </div>
                <Button 
                  className="absolute bottom-2 right-2 bg-blue-600 hover:bg-blue-500 h-8 px-4 text-xs font-bold gap-2 rounded-lg shadow-lg shadow-blue-900/20 transition-all hover:scale-105"
                  onClick={() => void (isLoading ? handleCancel() : handleSend())}
                  aria-label={isLoading ? 'Cancel active request' : 'Send message'}
                >
                  {isLoading ? 'Cancel' : 'Send'} {isLoading ? <X className="h-3 w-3" /> : <ArrowRight className="h-3 w-3" />}
                </Button>
            </div>
            
            <p className="max-w-4xl mx-auto mt-2 text-[11px] leading-relaxed text-slate-500 dark:text-gray-500">
              External data preflight: this request sends your prompt and may include attachments, selected retrieved text, persona context, and tool results. {mode === 'quad' ? 'Enhanced mode permits at most 2 counted provider attempts.' : 'Standard chat permits 1 counted provider attempt.'}
            </p>
            <p className="max-w-4xl mx-auto mt-1 text-[11px] leading-relaxed text-slate-500 dark:text-gray-500">
              {providerBudget
                ? `Today: ${providerBudget.daily.calls}/${providerBudget.limits.daily_calls} calls and ${providerBudget.daily.tokens_total.toLocaleString()}/${providerBudget.limits.daily_tokens.toLocaleString()} tokens. ${providerBudget.remaining.daily_calls} calls remain. Pricing is ${providerBudget.pricing_status}; unknown price is never represented as zero.`
                : 'Usage budget is unavailable in the renderer; the server still fails closed if its durable budget ledger cannot be read.'}
              {' '}Verify generated responses before critical use.
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
