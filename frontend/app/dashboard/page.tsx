export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-8">
      <div className="container mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">System Dashboard</h1>
          <p className="text-gray-500">Real-time metrics and knowledge graph status</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Stat Cards */}
          <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
            <h3 className="text-sm font-medium text-gray-400 uppercase">Knowledge Pillars</h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">6</p>
            <div className="mt-2 text-sm text-green-500">Active</div>
          </div>
          
          <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
             <h3 className="text-sm font-medium text-gray-400 uppercase">Algorithms</h3>
             <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">114</p>
             <div className="mt-2 text-sm text-blue-500">Registered in MCP</div>
          </div>

          <div className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm">
             <h3 className="text-sm font-medium text-gray-400 uppercase">System Status</h3>
             <div className="flex items-center gap-2 mt-2">
                <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                <span className="text-xl font-bold text-gray-900 dark:text-white">Operational</span>
             </div>
          </div>
        </div>

        <div className="p-12 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 border-dashed flex flex-col items-center justify-center text-center">
           <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full mb-4 flex items-center justify-center text-gray-400">
             <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
           </div>
           <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Metrics Visualization</h3>
           <p className="text-gray-500 max-w-md">
             Real-time graph visualization and trace analysis widgets will be implemented in the next sprint.
           </p>
        </div>
      </div>
    </main>
  );
}
