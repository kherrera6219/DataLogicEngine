import { ChatInterface } from '@/components/chat/ChatInterface';

export const metadata = {
  title: 'UKG Enterprise AI Assistant',
  description: 'Advanced reasoning and compliance chatbots for enterprise.',
};

export default function ChatPage() {
  return (
    <div className="flex h-screen bg-[#111111] text-white font-sans overflow-hidden bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">
      <ChatInterface />
    </div>
  );
}
