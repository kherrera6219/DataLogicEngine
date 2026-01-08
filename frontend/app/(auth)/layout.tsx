export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-[80vh] flex items-center justify-center bg-gray-50/50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white dark:bg-gray-950 p-8 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-800">
        {children}
      </div>
    </div>
  );
}
