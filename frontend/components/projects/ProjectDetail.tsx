'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft, MessageSquare, Upload, Download, Trash2,
  MoreHorizontal, Plus, Search, UserCircle2, Bot
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { api } from '@/lib/api';
import { type ApiChatMessage } from '@/lib/api/chat';

interface ProjectDetailProps {
  id: string;
}

function relativeDate(value?: string): string {
  if (!value) return 'Unknown';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
}

export function ProjectDetail({ id }: ProjectDetailProps) {
  const [title, setTitle] = useState<string>(`Session ${id.slice(0, 8)}`);
  const [messages, setMessages] = useState<ApiChatMessage[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const hydrate = async () => {
      try {
        const [sessionsResult, messageResult] = await Promise.all([
          api.chat.listSessions(),
          api.chat.getSessionMessages(id),
        ]);

        if (cancelled) return;

        const matchedSession = (sessionsResult.sessions || []).find((session) => session.id === id);
        setTitle(matchedSession?.title || `Session ${id.slice(0, 8)}`);
        setMessages(messageResult.messages || []);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to load session details');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void hydrate();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const filteredMessages = useMemo(() => {
    const needle = search.trim().toLowerCase();
    if (!needle) return messages;
    return messages.filter((message) =>
      `${message.role} ${message.content}`.toLowerCase().includes(needle)
    );
  }, [messages, search]);

  const assistantMessageCount = useMemo(
    () => messages.filter((message) => message.role === 'assistant').length,
    [messages]
  );
  const assistantRatio = messages.length
    ? Math.round((assistantMessageCount / messages.length) * 100)
    : 0;

  return (
    <div className="min-h-full bg-black text-white font-sans flex flex-col">
      <div className="h-16 border-b border-white/10 bg-gray-900/50 backdrop-blur-md flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-white" onClick={() => window.history.back()}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-sm font-bold tracking-wide flex items-center gap-2">
              {title}
              <Badge variant="outline" className="text-[10px] bg-blue-900/10 text-blue-400 border-blue-500/30">Active</Badge>
            </h1>
            <div className="text-[10px] text-gray-400 font-mono">ID: {id} • Last synced {relativeDate(messages[messages.length - 1]?.timestamp)}</div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="h-8 border-white/10 text-gray-400 hover:text-white gap-2">
            <Upload className="h-3 w-3" /> Upload Files
          </Button>
          <Button size="sm" className="h-8 bg-blue-600 hover:bg-blue-700 font-bold gap-2">
            <Plus className="h-3 w-3" /> New Note
          </Button>
        </div>
      </div>

      <div className="flex-1 flex">
        <div className="flex-1 p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="relative w-64">
              <Search className="absolute left-2 top-2.5 h-3 w-3 text-gray-500" />
              <Input
                placeholder="Filter messages..."
                className="pl-8 bg-white/5 border-white/10 h-8 text-xs"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span>{filteredMessages.length} items</span>
              <Separator orientation="vertical" className="h-4" />
              <span>{messages.length} total</span>
            </div>
          </div>

          {loading && <div className="text-sm text-muted-foreground">Loading session messages...</div>}
          {!loading && error && <div className="text-sm text-red-400">Failed to load session: {error}</div>}

          {!loading && !error && (
            <div className="border border-white/10 rounded-lg overflow-hidden bg-gray-900/20">
              <table className="w-full text-left text-xs">
                <thead className="bg-white/5 text-gray-400 font-mono uppercase">
                  <tr>
                    <th className="p-3 font-medium w-8"></th>
                    <th className="p-3 font-medium">Role</th>
                    <th className="p-3 font-medium">Message Preview</th>
                    <th className="p-3 font-medium">Timestamp</th>
                    <th className="p-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredMessages.map((message) => (
                    <tr key={message.id} className="hover:bg-white/5 transition-colors group cursor-pointer">
                      <td className="p-3 text-center">
                        {message.role === 'assistant' ? (
                          <Bot className="h-4 w-4 text-blue-400" />
                        ) : (
                          <UserCircle2 className="h-4 w-4 text-green-400" />
                        )}
                      </td>
                      <td className="p-3 font-medium text-gray-200 capitalize">{message.role}</td>
                      <td className="p-3 text-gray-300 max-w-[520px] truncate">{message.content}</td>
                      <td className="p-3 text-gray-500">{relativeDate(message.timestamp)}</td>
                      <td className="p-3 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon" className="h-6 w-6 hover:bg-white/10 text-gray-400 hover:text-white">
                            <Download className="h-3 w-3" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-6 w-6 hover:bg-red-900/30 text-gray-400 hover:text-red-400">
                            <Trash2 className="h-3 w-3" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-6 w-6 hover:bg-white/10 text-gray-400 hover:text-white">
                            <MoreHorizontal className="h-3 w-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!loading && !error && !filteredMessages.length && (
            <div className="mt-6 text-sm text-muted-foreground">No messages found for this session filter.</div>
          )}
        </div>

        <div className="w-80 border-l border-white/10 bg-gray-900/30 p-6">
          <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">Session Stats</h3>
          <div className="space-y-4">
            <div className="p-4 bg-white/5 rounded-lg border border-white/5">
              <div className="text-2xl font-bold font-mono text-white">{messages.length}</div>
              <div className="text-xs text-gray-400 mt-1">Total Messages</div>
              <div className="w-full bg-gray-700 h-1 mt-2 rounded-full overflow-hidden">
                <div className="bg-green-500 h-full transition-all duration-300" style={{ width: `${assistantRatio}%` }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs text-gray-400">
                <span>Created</span>
                <span className="text-white">{relativeDate(messages[0]?.timestamp)}</span>
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span>Last Updated</span>
                <span className="text-white">{relativeDate(messages[messages.length - 1]?.timestamp)}</span>
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span>Type</span>
                <span className="text-white flex items-center gap-1"><MessageSquare className="h-3 w-3" /> Chat Session</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
