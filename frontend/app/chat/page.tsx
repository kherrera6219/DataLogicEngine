import { ChatInterface } from '@/components/Chat/ChatInterface';

export default function ChatPage() {
  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-4 md:p-8">
      <div className="container mx-auto">
        <header className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <span className="text-blue-600">◆</span>
              Enterprise Standards Review
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">LLM Gateway v1.0 • UKG Pipeline Active</p>
          </div>
          <div className="flex gap-2">
             <div className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                Gateway Connected
             </div>
          </div>
        </header>
        
        <ChatInterface />
      </div>
    </main>
  );
}
