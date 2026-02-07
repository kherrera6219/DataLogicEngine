export default function ChatLoading() {
  return (
    <div className="h-full flex items-center justify-center bg-background text-foreground">
      <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-2">
        <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        <span className="text-sm">Bootstrapping chat session...</span>
      </div>
    </div>
  );
}
