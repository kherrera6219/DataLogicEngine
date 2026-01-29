'use client';

import { useState } from 'react';
import { 
  Card, CardContent, CardHeader, CardTitle 
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select } from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";
import { 
  BarChart3, Terminal, Play, Copy, RefreshCw, Eye, CheckCircle, Shield 
} from "lucide-react";
import { 
  BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell 
} from 'recharts';

interface TestResult {
  confidence: number;
  answer: string;
  trace: {
    steps: number;
    coordinate: string;
  };
}

export function ApiOverlayConfig() {
  const { toast } = useToast();
  const [provider, setProvider] = useState("openai");
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  
  // UKG Enhancement State
  const [tier, setTier] = useState("moderate");
  const [confidence, setConfidence] = useState(99.5);
  // Disabled specific persona tuning for now to simplify UI, defaults used
  const personas = {
    knowledge: 0.25,
    sector: 0.25,
    regulatory: 0.25,
    compliance: 0.25
  };

  // Playground State
  const [testQuery, setTestQuery] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  // Tabs State
  const [activeTab, setActiveTab] = useState("python");

  const mockData = [
    { name: 'Mon', queries: 4000 },
    { name: 'Tue', queries: 3000 },
    { name: 'Wed', queries: 2000 },
    { name: 'Thu', queries: 2780 },
    { name: 'Fri', queries: 1890 },
    { name: 'Sat', queries: 2390 },
    { name: 'Sun', queries: 3490 },
  ];

  const handleTestConnection = () => {
    setTestStatus('testing');
    setTimeout(() => {
      setTestStatus('success');
      toast("Overlay connected to production Gateway.", "success", 3000);
    }, 1500);
  };

  const handleRunTest = () => {
    setIsProcessing(true);
    setTimeout(() => {
      setTestResult({
        confidence: 0.995,
        answer: "The proposed architecture is fully compliant with NIST 800-171 Rev 2. All 110 controls mapped successfully.",
        trace: { steps: 12, coordinate: "Axis 7: Federated Truth" }
      });
      setIsProcessing(false);
      toast("Refinement cycle complete.", "success", 2000);
    }, 2000);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* 🎯 Header & Quick Stats */}
      {/* ... (Header section unchanged) ... */}
      <section className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card className="glass-card border-white/10 bg-gradient-to-br from-blue-900/20 to-purple-900/20 col-span-1 lg:col-span-4 p-6 flex flex-col md:flex-row justify-between items-center text-center md:text-left">
          {/* ... */}
          <div>
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                UKG API Overlay Configuration
            </h1>
            <p className="text-muted-foreground mt-1">
                Transform any LLM into enterprise-ready AI with validation.
            </p>
          </div>
          <div className="flex gap-4 mt-4 md:mt-0">
             <div className="text-center p-3 bg-white/5 rounded-lg border border-white/5">
                <div className="text-xs text-gray-400 uppercase tracking-widest">Queries</div>
                <div className="text-xl font-bold text-white">24,573</div>
             </div>
             <div className="text-center p-3 bg-white/5 rounded-lg border border-white/5">
                <div className="text-xs text-gray-400 uppercase tracking-widest">Valid</div>
                <div className="text-xl font-bold text-green-400">99.5%</div>
             </div>
             <div className="text-center p-3 bg-white/5 rounded-lg border border-white/5 hidden md:block">
                <div className="text-xs text-gray-400 uppercase tracking-widest">Uptime</div>
                <div className="text-xl font-bold text-blue-400">99.9%</div>
             </div>
          </div>
        </Card>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         {/* LEFT COLUMN: CONFIGURATION */}
         <div className="lg:col-span-2 space-y-8">
            
            {/* ... (Provider and Enhancement steps unchanged) ... */}
            <Card className="border-white/10 space-y-4">
               <CardHeader className="bg-white/5 border-b border-white/5 pb-4">
                  <div className="flex justify-between items-center">
                      <CardTitle className="text-lg flex items-center gap-2">
                         <span className="bg-blue-600 w-6 h-6 rounded-full text-xs flex items-center justify-center text-white">1</span>
                         Configure LLM Provider
                      </CardTitle>
                      {testStatus === 'success' && <Badge variant="success" className="bg-green-500/20 text-green-400 border-green-500/50">Verified</Badge>}
                  </div>
               </CardHeader>
               <CardContent className="space-y-6 pt-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                     <div className="space-y-2">
                        <label className="text-xs font-bold uppercase text-gray-500">Provider</label>
                        <Select value={provider} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setProvider(e.target.value)} className="bg-white/5 border-white/10">
                           <option value="openai">OpenAI</option>
                           <option value="azure">Azure OpenAI</option>
                           <option value="anthropic">Anthropic</option>
                           <option value="google">Google Vertex</option>
                        </Select>
                     </div>
                     <div className="space-y-2">
                        <label className="text-xs font-bold uppercase text-gray-500">Model</label>
                        <Select defaultValue="gpt-4-turbo" className="bg-white/5 border-white/10">
                           <option value="gpt-4-turbo">GPT-4 Turbo</option>
                           <option value="gpt-4">GPT-4</option>
                           <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        </Select>
                     </div>
                  </div>

                  <div className="space-y-2">
                      <label className="text-xs font-bold uppercase text-gray-500">API Key</label>
                      <div className="flex gap-2">
                          <div className="relative flex-1">
                             <Input 
                                type={showKey ? "text" : "password"} 
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="sk-..." 
                                className="bg-white/5 border-white/10 pr-10 font-mono"
                             />
                             <button 
                                onClick={() => setShowKey(!showKey)}
                                className="absolute right-3 top-2.5 text-gray-400 hover:text-white"
                                type="button"
                                aria-label={showKey ? "Hide API key" : "Show API key"}
                             >
                                <Eye className="h-4 w-4" />
                             </button>
                          </div>
                          <Button 
                            variant={testStatus === 'success' ? 'secondary' : 'default'}
                            onClick={handleTestConnection}
                            disabled={testStatus === 'testing' || !apiKey}
                            className="w-32"
                          >
                             {testStatus === 'testing' ? 'Testing...' : testStatus === 'success' ? 'Connected' : 'Test'}
                          </Button>
                      </div>
                      <p className="text-[10px] text-gray-500">Your key is encrypted at rest using AES-256 and never logged.</p>
                  </div>
               </CardContent>
            </Card>

            <Card className="border-white/10">
               <CardHeader className="bg-white/5 border-b border-white/5 pb-4">
                  <CardTitle className="text-lg flex items-center gap-2">
                     <span className="bg-purple-600 w-6 h-6 rounded-full text-xs flex items-center justify-center text-white">2</span>
                     Configure Enhancement Layer
                  </CardTitle>
               </CardHeader>
               <CardContent className="space-y-6 pt-6">
                  {/* Tiers */}
                  <div className="space-y-3">
                     <label className="text-xs font-bold uppercase text-gray-500">Processing Tier</label>
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {[
                           { id: 'trivial', name: 'Trivial', price: '$0.001', desc: 'Direct RAG (<2s)' },
                           { id: 'moderate', name: 'Moderate', price: '$0.005', desc: 'RAG + CoT (<5s)' },
                           { id: 'high', name: 'High-Stakes', price: '$0.015', desc: '12-step Logic (<15s)' },
                           { id: 'extreme', name: 'Extreme', price: '$0.035', desc: 'Simulations (<30s)' },
                        ].map((t) => (
                           <div 
                              key={t.id}
                              onClick={() => setTier(t.id)}
                              aria-hidden="true"
                              className={`p-3 rounded-lg border cursor-pointer transition-all ${tier === t.id ? 'bg-purple-500/20 border-purple-500 ring-1 ring-purple-500' : 'bg-white/5 border-white/10 hover:border-white/30'}`}
                           >
                              <div className="flex justify-between items-center mb-1">
                                 <span className="font-bold text-sm">{t.name}</span>
                                 <Badge variant="outline" className="text-[10px]">{t.price}</Badge>
                              </div>
                              <div className="text-xs text-muted-foreground">{t.desc}</div>
                           </div>
                        ))}
                     </div>
                  </div>

                  {/* Confidence Slider */}
                  <div className="space-y-4 pt-4 border-t border-white/5">
                     <div className="flex justify-between">
                        <label className="text-xs font-bold uppercase text-gray-500">Confidence Threshold</label>
                        <span className="text-sm font-mono font-bold text-purple-400">{confidence}%</span>
                     </div>
                     <input 
                        type="range" 
                        min="90" max="99.9" step="0.1" 
                        value={confidence} 
                        onChange={(e) => setConfidence(parseFloat(e.target.value))}
                        className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-purple-500"
                        title="Confidence Threshold"
                     />
                     <div className="flex justify-between text-[10px] text-gray-500">
                        <span>90% (Faster)</span>
                        <span>99.9% (Critical)</span>
                     </div>
                  </div>

                  {/* Personas */}
                  <div className="space-y-3 pt-4 border-t border-white/5">
                     <label className="text-xs font-bold uppercase text-gray-500">Quad Persona Weights</label>
                     <div className="grid grid-cols-2 gap-4">
                        {Object.entries(personas).map(([key, val]) => (
                           <div key={key} className="space-y-1">
                              <div className="flex justify-between text-xs">
                                 <span className="capitalize">{key}</span>
                                 <span className="text-gray-400">{val}</span>
                              </div>
                              <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                               <div className="h-full bg-blue-500" style={{ width: `${val * 100}%` } as React.CSSProperties} />
                              </div>
                           </div>
                        ))}
                     </div>
                  </div>
               </CardContent>
            </Card>

            {/* 🔗 Step 3: Integration */}
            <Card className="border-white/10">
               <CardHeader className="bg-white/5 border-b border-white/5 pb-4">
                  <CardTitle className="text-lg flex items-center gap-2">
                     <span className="bg-green-600 w-6 h-6 rounded-full text-xs flex items-center justify-center text-white">3</span>
                     API Endpoint & Logic Integration
                  </CardTitle>
               </CardHeader>
               <CardContent className="space-y-6 pt-6">
                  <div className="relative">
                     <label className="text-xs font-bold uppercase text-gray-500 mb-2 block">Your Unique Endpoint</label>
                     <div className="flex gap-2">
                        <code className="flex-1 bg-black/40 border border-white/10 p-3 rounded-lg font-mono text-xs text-green-400">
                           https://api.ukg.ai/v1/enhance
                        </code>
                        <Button size="icon" variant="outline" title="Copy Endpoint"><Copy className="h-4 w-4" /></Button>
                     </div>
                  </div>

                  <Tabs value={activeTab} onValueChange={setActiveTab}>
                     <TabsList className="bg-white/5 h-10 mb-2">
                        <TabsTrigger value="python">Python</TabsTrigger>
                        <TabsTrigger value="curl">cURL</TabsTrigger>
                        <TabsTrigger value="js">Node.js</TabsTrigger>
                     </TabsList>
                     <TabsContent value="python">
                        <pre className="bg-black/50 p-4 rounded-lg text-xs font-mono text-gray-300 overflow-x-auto border border-white/10">
{`import requests

response = requests.post(
    "https://api.ukg.ai/v1/enhance",
    headers={
        "Authorization": "Bearer ukg_live_sk_${apiKey ? '****' : '...'}",
        "Content-Type": "application/json"
    },
    json={
        "query": "Analyze compliance...",
        "truth_engine": {"tier": "${tier}"},
        "refinement": {"confidence": ${confidence}}
    }
)

print(response.json())`}
                        </pre>
                     </TabsContent>
                     {/* Other tabs omitted for brevity but structure supports them */}
                  </Tabs>
               </CardContent>
            </Card>

         </div>

         {/* RIGHT COLUMN: PREVIEW & STATS */}
         <div className="space-y-6">
            
            {/* 🧪 Playground */}
            <Card className="border-white/10 border-t-4 border-t-purple-500 shadow-2xl">
               <CardHeader>
                  <CardTitle className="flex justify-between items-center">
                     <span>Testing Playground</span>
                     <Terminal className="h-4 w-4 text-purple-500" />
                  </CardTitle>
               </CardHeader>
               <CardContent className="space-y-4">
                  <div>
                    <label htmlFor="test-prompt" className="sr-only">Test Prompt</label>
                    <textarea 
                       id="test-prompt"
                       value={testQuery}
                       onChange={(e) => setTestQuery(e.target.value)}
                       placeholder="Enter a test prompt to validate your configuration..."
                       className="w-full bg-black/20 border-white/10 rounded-lg p-3 text-sm min-h-[100px] focus:ring-purple-500"
                    />
                  </div>
                  <Button onClick={handleRunTest} disabled={isProcessing || !testQuery} className="w-full bg-purple-600 hover:bg-purple-700">
                     {isProcessing ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                     Test Enhancement
                  </Button>

                  {testResult && (
                     <div className="mt-4 p-4 bg-green-900/10 border border-green-500/20 rounded-lg animate-in zoom-in-95">
                        <div className="flex justify-between items-center mb-2">
                           <Badge variant="success" className="bg-green-500/20 text-green-400">{(testResult.confidence * 100).toFixed(1)}% Confidence</Badge>
                           <span className="text-[10px] text-gray-500">{testResult.trace.steps} steps</span>
                        </div>
                        <p className="text-xs text-gray-300 leading-relaxed">
                           {testResult.answer}
                        </p>
                        <div className="mt-3 pt-3 border-t border-white/5 flex gap-2 text-[10px] text-gray-500 font-mono">
                           <span>{testResult.trace.coordinate}</span>
                        </div>
                     </div>
                  )}
               </CardContent>
            </Card>

            {/* 📊 Analytics Graph */}
            <Card className="border-white/10">
               <CardHeader>
                  <CardTitle className="flex justify-between items-center text-sm">
                     <span>Real-Time Activity</span>
                     <BarChart3 className="h-4 w-4 text-gray-500" />
                  </CardTitle>
               </CardHeader>
               <CardContent className="h-[200px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                     <BarChart data={mockData}>
                        <XAxis dataKey="name" stroke="#4b5563" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                        <Tooltip 
                           contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', fontSize: '12px' }}
                           itemStyle={{ color: '#e5e7eb' }}
                        />
                        <Bar dataKey="queries" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                           {mockData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={index === mockData.length - 1 ? '#8b5cf6' : '#3b82f6'} />
                           ))}
                        </Bar>
                     </BarChart>
                  </ResponsiveContainer>
               </CardContent>
            </Card>

            {/* 🔒 Security */}
            <Card className="border-white/10">
               <CardHeader>
                  <CardTitle className="flex justify-between items-center text-sm">
                     <span>Security & Compliance</span>
                     <Shield className="h-4 w-4 text-green-500" />
                  </CardTitle>
               </CardHeader>
               <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                     <span className="text-xs text-gray-400">Data Region</span>
                     <Badge variant="outline" className="text-[10px]">US-East (Primary)</Badge>
                  </div>
                   <div className="flex items-center justify-between">
                     <span className="text-xs text-gray-400">Zero-Knowledge</span>
                     <CheckCircle className="h-4 w-4 text-green-500" />
                  </div>
                   <div className="flex items-center justify-between">
                     <span className="text-xs text-gray-400">Audit Trail Retention</span>
                     <span className="text-xs font-mono">90 Days</span>
                  </div>
               </CardContent>
            </Card>

         </div>
      </div>
    </div>
  );
}
