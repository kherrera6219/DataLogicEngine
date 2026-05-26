
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Shield } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function PrivacyPolicyPage() {
  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-12">
      <div className="container mx-auto max-w-4xl">
        <div className="mb-8 flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
            <Shield className="h-6 w-6" />
            <span className="font-bold tracking-tight">DataLogic Legal</span>
          </div>
        </div>

        <Card className="glass-card border-none shadow-xl bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl">
          <CardHeader className="pb-8 border-b border-gray-100 dark:border-gray-800">
            <CardTitle className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-400">
              Privacy Policy
            </CardTitle>
            <p className="text-muted-foreground mt-2 font-medium">
              Effective Date: January 16, 2026
            </p>
          </CardHeader>
          <CardContent className="prose prose-gray dark:prose-invert max-w-none pt-8 space-y-8">
            <section>
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 text-sm">1</span>
                Introduction
              </h2>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                DataLogicEngine is a local-first knowledge graph workspace for governed AI reasoning. This Privacy Policy explains how the App collects, uses, and discloses information across the current Windows desktop build and the same Windows application running inside a Windows virtual machine.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 text-sm">2</span>
                Information We Collect
              </h2>
              <ul className="grid gap-3 list-none pl-0">
                <li className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800">
                  <strong className="text-gray-900 dark:text-white">Local Identity Information:</strong> Windows account identity metadata used to create the local desktop or Windows VM user profile.
                </li>
                <li className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800">
                  <strong className="text-gray-900 dark:text-white">Usage Data:</strong> Logs of application usage, including timestamps and feature interactions, for security auditing and performance monitoring.
                </li>
                <li className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800">
                  <strong className="text-gray-900 dark:text-white">Content Data:</strong> The text queries, documents, and data sources you explicitly upload or input into the App for processing (&quot;User Content&quot;).
                </li>
                <li className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800">
                  <strong className="text-gray-900 dark:text-white">Technical Data:</strong> IP address, device type, and operating system information required for secure connection and session management.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 text-sm">3</span>
                How We Use Information
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mb-4">We use your information exclusively for the following purposes:</p>
              <ul className="list-disc pl-5 space-y-1 text-gray-600 dark:text-gray-300">
                <li>To provide the core functionality of the App (knowledge synthesis and reasoning).</li>
                <li>To authenticate your local Windows identity.</li>
                <li>To prevent fraud, abuse, and security threats (e.g., adversarial prompt detection).</li>
                <li>To comply with legal obligations and enforce our Terms of Service.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 text-sm">4</span>
                Cloud Processing & Third Parties
              </h2>
              <div className="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-900/50 text-sm">
                <p className="font-semibold text-blue-900 dark:text-blue-200 mb-2">Cloud Dependency Disclosure</p>
                <p className="text-blue-800 dark:text-blue-300 leading-relaxed">
                  AI reasoning features require internet access. Prompts, selected context, and provider/model metadata may be sent to the configured third-party AI provider for response generation.
                  Supported provider families include <strong>OpenAI, Anthropic, Google Gemini / Vertex AI, and Microsoft Azure OpenAI</strong>.
                </p>
                <p className="mt-2 text-blue-800 dark:text-blue-300">
                  Provider retention, training, regional handling, and logging are governed by the provider account, contract, and API settings you configure.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 text-sm">5</span>
                Data Retention
              </h2>
              <ul className="grid gap-3 list-none pl-0">
                <li className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 flex justify-between items-center">
                  <span className="font-medium">Session Data</span>
                  <span className="text-sm text-muted-foreground">Retained until explicit delete</span>
                </li>
                <li className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 flex justify-between items-center">
                  <span className="font-medium">Audit Logs</span>
                  <span className="text-sm text-muted-foreground">90 Days (Forensic security)</span>
                </li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 text-sm">6</span>
                Your Rights
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                 <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/50">
                    <h3 className="font-bold mb-1">Access & Export</h3>
                    <p className="text-xs text-muted-foreground">Download a full JSON archive of your data via Settings.</p>
                 </div>
                 <div className="p-4 rounded-xl border border-red-200 dark:border-red-900/30 bg-red-50/50 dark:bg-red-900/10">
                    <h3 className="font-bold text-red-600 dark:text-red-400 mb-1">Deletion</h3>
                    <p className="text-xs text-red-600/70 dark:text-red-400/70">Request deletion of the local profile and application data controlled by this installation.</p>
                 </div>
                 <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/50">
                    <h3 className="font-bold mb-1">AI Controls</h3>
                    <p className="text-xs text-muted-foreground">Opt-out of history storage and select providers.</p>
                 </div>
              </div>
            </section>

            <section className="pt-8 border-t border-gray-100 dark:border-gray-800">
              <p className="text-center text-sm text-muted-foreground">
                Questions? Contact us at <a href="mailto:privacy@datalogicengine.com" className="text-blue-500 hover:underline">privacy@datalogicengine.com</a>
              </p>
            </section>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
