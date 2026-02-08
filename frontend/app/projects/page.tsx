'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Folder, Plus, Search, Filter, MoreVertical,
  Clock, FileText, Star, MessageSquare, Layers
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { api } from '@/lib/api';
import { type ChatSession } from '@/lib/api/chat';

function formatRelative(dateString?: string): string {
  if (!dateString) return 'Unknown';
  const target = new Date(dateString).getTime();
  if (Number.isNaN(target)) return 'Unknown';
  const diffMs = Date.now() - target;
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function statusFromMode(mode?: string): string {
  if (!mode) return 'Active';
  if (mode.toLowerCase() === 'quad') return 'Enhanced';
  return 'Active';
}

export default function ProjectsPage() {
  const router = useRouter();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messageCounts, setMessageCounts] = useState<Record<string, number>>({});
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void api.chat
      .listSessions()
      .then((response) => {
        if (cancelled) return;
        setSessions(response.sessions || []);
        setMessageCounts({});
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load sessions');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const targetSessions = sessions.slice(0, 20);
    if (!targetSessions.length) return;

    let cancelled = false;
    void Promise.all(
      targetSessions.map(async (session) => {
        try {
          const response = await api.chat.getSessionMessages(session.id);
          return [session.id, response.messages?.length || 0] as const;
        } catch {
          return [session.id, 0] as const;
        }
      })
    ).then((entries) => {
      if (cancelled) return;
      setMessageCounts(Object.fromEntries(entries));
    });

    return () => {
      cancelled = true;
    };
  }, [sessions]);

  const filteredSessions = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return sessions;
    return sessions.filter((session) =>
      `${session.title || ''} ${session.id}`.toLowerCase().includes(needle)
    );
  }, [query, sessions]);

  return (
    <div className="flex-1 flex flex-col bg-transparent text-gray-900 dark:text-foreground animate-in fade-in duration-700">
      <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8">
        <div className="flex items-center gap-3">
          <div className="bg-blue-500/10 p-2 rounded-lg border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]">
            <Folder className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-gray-100 tracking-tight">Projects</h1>
            <div className="text-[10px] text-slate-500 dark:text-gray-500 font-mono uppercase tracking-widest">Chat Session Workspace</div>
          </div>
        </div>
        <Button
          className="bg-blue-600 hover:bg-blue-500 text-white font-bold shadow-lg shadow-blue-900/20 transition-all hover:scale-105 active:scale-95"
          onClick={() => router.push('/chat')}
        >
          <Plus className="h-4 w-4 mr-2" /> New Session
        </Button>
      </div>

      <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8">
        <div className="flex items-center justify-between bg-white/70 dark:bg-white/5 p-2 rounded-2xl border border-slate-200 dark:border-white/5 backdrop-blur-md shadow-inner">
          <div className="relative w-96">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500 dark:text-gray-500" />
            <Input
              aria-label="Search projects"
              placeholder="Search sessions..."
              className="pl-9 bg-white dark:bg-black/20 border-slate-200 dark:border-transparent hover:bg-slate-50 dark:hover:bg-black/40 focus:bg-slate-50 dark:focus:bg-black/50 transition-colors h-9 text-sm"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" className="text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-white/5 h-8 text-xs px-3">
              <Clock className="h-3.5 w-3.5 mr-2" /> Recent
            </Button>
            <Button variant="ghost" size="sm" className="text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-white/5 h-8 text-xs px-3">
              <Star className="h-3.5 w-3.5 mr-2" /> Favorites
            </Button>
            <div className="w-px h-6 bg-white/10 mx-1 my-auto"></div>
            <Button variant="ghost" size="sm" className="text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-white/5 h-8 text-xs px-3">
              <Filter className="h-3.5 w-3.5 mr-2" /> Filter
            </Button>
          </div>
        </div>

        {loading && (
          <div className="text-sm text-muted-foreground">Loading workspaces...</div>
        )}

        {!loading && error && (
          <div className="text-sm text-red-600 dark:text-red-400">Failed to load projects: {error}</div>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredSessions.map((session, index) => {
              const status = statusFromMode(session.mode);
              const icon = session.mode === 'quad' ? Layers : MessageSquare;
              const title = session.title || `Session ${session.id.slice(0, 8)}`;
              const messageCount = messageCounts[session.id] ?? 0;
              const accent = index % 2 === 0 ? 'bg-blue-600' : 'bg-green-600';
              const Icon = icon;

              return (
                <Link href={`/projects/view?id=${encodeURIComponent(session.id)}`} key={session.id} className="block group">
                  <Card className="fluent-acrylic border-slate-200 dark:border-white/10 h-full transition-all duration-500 hover:-translate-y-2 relative overflow-hidden group hover:shadow-[0_20px_40px_rgba(0,0,0,0.4)]">
                    <div className={`absolute -top-24 -right-24 h-48 w-48 ${accent} opacity-0 group-hover:opacity-10 transition-opacity blur-[60px] pointer-events-none`}></div>
                    <div className={`absolute top-0 left-0 right-0 h-1 ${accent} opacity-50`}></div>

                    <CardContent className="p-6">
                      <div className="flex justify-between items-start mb-6">
                        <div className={`h-12 w-12 rounded-2xl ${accent} bg-opacity-20 flex items-center justify-center border border-slate-200 dark:border-white/10 shadow-lg group-hover:scale-110 transition-transform duration-500`}>
                          <Icon className={`h-6 w-6 ${accent.replace('bg-', 'text-').replace('-600', '-400')}`} />
                        </div>
                        <Button variant="ghost" size="icon" className="h-8 w-8 -mr-2 text-slate-500 dark:text-gray-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-white/10 rounded-lg">
                          <span className="sr-only">More options for {title}</span>
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </div>

                      <h3 className="font-bold text-xl mb-1 text-slate-900 dark:text-gray-100 group-hover:text-blue-400 transition-colors tracking-tight">{title}</h3>
                      <div className="flex items-center gap-2 mb-6">
                        <Badge className="bg-white/70 dark:bg-white/5 border-none text-slate-600 dark:text-gray-400 text-[9px] font-bold uppercase tracking-widest px-2 py-0">
                          {status}
                        </Badge>
                        <span className="text-[10px] text-slate-500 dark:text-gray-600 font-mono">#{session.id.slice(0, 8)}</span>
                      </div>

                      <div className="space-y-4 pt-4 border-t border-white/5">
                        <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-gray-500">
                          <div className="flex items-center gap-2">
                            <FileText className="h-3.5 w-3.5" />
                            <span>{messageCount} Messages</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Clock className="h-3.5 w-3.5" />
                            <span>{formatRelative(session.updated_at || session.created_at)}</span>
                          </div>
                        </div>
                        <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                          <div className={`h-full ${accent} opacity-60 w-2/3`}></div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}

            {!filteredSessions.length && (
              <div className="col-span-full text-sm text-muted-foreground">No sessions matched your search.</div>
            )}

            <button
              className="border border-dashed border-slate-300 dark:border-white/10 rounded-2xl flex flex-col items-center justify-center p-8 text-slate-500 dark:text-gray-500 hover:text-blue-400 hover:border-blue-500/40 hover:bg-blue-500/5 transition-all group h-full min-h-[260px] relative overflow-hidden"
              onClick={() => router.push('/chat')}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
              <div className="h-16 w-16 rounded-full bg-white/70 dark:bg-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-all duration-500 shadow-xl group-hover:shadow-blue-500/10 border border-slate-200 dark:border-white/5 group-hover:border-blue-500/20">
                <Plus className="h-8 w-8" />
              </div>
              <div className="font-bold text-sm tracking-wide uppercase">New Workspace</div>
              <div className="text-[10px] text-slate-500 dark:text-gray-600 mt-2 font-mono">OPEN CHAT</div>
            </button>
          </div>
        )}
      </div>

      <div className="mt-auto border-t border-white/5 px-8 py-4 bg-white/70 dark:bg-white/5 flex justify-between items-center text-[10px] text-slate-500 dark:text-gray-600 font-mono">
        <div className="flex gap-6">
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-blue-500"></div>
            TOTAL_SESSIONS: {sessions.length}
          </div>
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-green-500"></div>
            HEALTH: {error ? 'DEGRADED' : 'OPTIMAL'}
          </div>
        </div>
        <div className="flex gap-4">
          <span>LATEST_SYNC: {new Date().toLocaleTimeString()}</span>
          <span>MODE: LOCAL</span>
        </div>
      </div>
    </div>
  );
}
