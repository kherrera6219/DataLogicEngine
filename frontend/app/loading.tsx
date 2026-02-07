export default function AppLoading() {
  return (
    <div className="min-h-[40vh] flex items-center justify-center bg-background text-foreground">
      <div className="flex items-center gap-3 rounded-xl border border-border bg-card px-5 py-3 shadow-sm">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        <span className="text-sm font-medium">Loading workspace...</span>
      </div>
    </div>
  );
}
