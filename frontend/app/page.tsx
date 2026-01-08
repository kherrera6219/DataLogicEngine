import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-950">
      <h1 className="text-6xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-violet-600">
        DataLogicEngine
      </h1>
      <p className="text-xl text-gray-600 dark:text-gray-300 mb-12 max-w-2xl text-center">
        Enterprise Universal Knowledge Graph System with 17-Axis Reasoning and MCP Integration.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
        <Link 
          href="/chat"
          className="group block p-8 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm hover:shadow-xl hover:border-blue-500 transition-all"
        >
          <div className="mb-4 w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center text-blue-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
          </div>
          <h2 className="text-2xl font-bold mb-2 group-hover:text-blue-600 transition-colors">Chat Interface &rarr;</h2>
          <p className="text-gray-500 dark:text-gray-400">Interaction with the UKG Truth Engine via the LLM Gateway.</p>
        </Link>
        
        <div className="p-8 bg-gray-50 dark:bg-gray-900/50 rounded-2xl border border-gray-200 dark:border-gray-800 opacity-70">
          <div className="mb-4 w-12 h-12 bg-gray-200 dark:bg-gray-800 rounded-xl flex items-center justify-center text-gray-500">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
          </div>
          <h2 className="text-2xl font-bold mb-2">Dashboard</h2>
          <p className="text-gray-500 text-sm mb-2">Coming in next update</p>
          <p className="text-gray-400 text-sm">Real-time statistics and graph visualization.</p>
        </div>
      </div>
      
      <div className="mt-12 text-sm text-gray-400">
        System Status: <span className="text-green-500 font-medium">Gateway Active</span> • Version 1.0.0
      </div>
    </main>
  );
}
