import { ChatInterface } from '@/components/chat/ChatInterface';

export const metadata = {
  title: 'UKG Enterprise AI Assistant',
  description: 'Advanced reasoning and compliance chatbots for enterprise.',
};

export default function ChatPage() {
  return (
    <div className="h-screen w-full bg-black">
      <ChatInterface />
    </div>
  );
}
