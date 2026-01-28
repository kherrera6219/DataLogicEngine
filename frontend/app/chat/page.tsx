import { PageLayout } from '@/components/ui/page-layout';
import { ChatInterface } from '@/components/Chat/ChatInterface';

export default function ChatPage() {
  return (
    <PageLayout
      title="Enterprise Standards Review"
      description="LLM Gateway v1.0 • UKG Pipeline Active"
      breadcrumbs={[{ label: "Intelligence Interface" }]}
      actions={
        <div className="flex items-center gap-2 px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-xs font-medium">
          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
          Gateway Connected
        </div>
      }
    >
      <ChatInterface />
    </PageLayout>
  );
}
