'use client';

import dynamic from 'next/dynamic';

const ChatInterface = dynamic(
  () => import('@/components/Chat/ChatInterface').then((mod) => mod.ChatInterface),
  {
    loading: () => (
      <div className="h-full flex items-center justify-center bg-background text-muted-foreground">
        <div className="text-sm font-medium">Loading chat workspace...</div>
      </div>
    ),
  }
);

export default function ChatPage() {
  return (
    <div className="h-full relative overflow-hidden">
      <ChatInterface />
    </div>
  );
}
