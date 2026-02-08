'use client';

import dynamic from 'next/dynamic';
import { useSearchParams } from 'next/navigation';

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
  const searchParams = useSearchParams();
  const autoOpenUpload = searchParams.get('intent') === 'upload';

  return (
    <div className="h-full relative overflow-hidden">
      <ChatInterface autoOpenUpload={autoOpenUpload} />
    </div>
  );
}
