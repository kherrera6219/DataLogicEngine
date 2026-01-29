import { ChatInterface } from '@/components/chat/ChatInterface';

export const metadata = {
  title: 'UKG Enterprise AI Assistant',
  description: 'Advanced reasoning and compliance chatbots for enterprise.',
};

export default function ChatPage() {
  return (
    <div className="h-full relative overflow-hidden">
      <ChatInterface />
    </div>
  );
}
