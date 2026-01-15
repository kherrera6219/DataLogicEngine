'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Shield, Lock, User as UserIcon } from "lucide-react";
import { useToast } from '@/components/ui/use-toast';

export default function LoginPage() {
  const { login } = useAuth();
  const { toast } = useToast();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setLoading(true);
      setError('');
      try {
          await login({ username: email, password });
          toast("Authentication successful. Welcome back.", "success");
      } catch (err) {
          const msg = err instanceof Error ? err.message : "Invalid credentials";
          setError(msg);
          toast(msg, "error");
      } finally {
          setLoading(false);
      }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black p-4 relative overflow-hidden">
      {/* Dynamic Background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,_rgba(37,99,235,0.1),transparent_50%)]" />
      
      <Card className="w-full max-w-md glass-card border-white/10 shadow-2xl relative z-10 animate-in fade-in zoom-in duration-500">
        <CardHeader className="text-center pb-8 border-b border-white/5 mx-6">
            <div className="mx-auto w-12 h-12 bg-blue-600/20 rounded-2xl flex items-center justify-center mb-4 border border-blue-500/30">
               <Shield className="h-6 w-6 text-blue-500" aria-hidden="true" />
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight">Enterprise Login</CardTitle>
            <CardDescription className="text-muted-foreground font-medium">Verify credentials for DataLogicEngine access</CardDescription>
        </CardHeader>
        <CardContent className="pt-8">
            <form onSubmit={handleSubmit} className="space-y-6">
                {error && (
                    <Alert variant="destructive" className="bg-red-500/10 border-red-500/20 text-red-200" role="alert">
                        <AlertDescription className="font-semibold">{error}</AlertDescription>
                    </Alert>
                )}
                <div className="space-y-3">
                    <Label htmlFor="username" className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Identity Identifier</Label>
                    <div className="relative">
                       <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" aria-hidden="true" />
                       <Input 
                          id="username" 
                          type="text" 
                          placeholder="Employee ID or Email" 
                          className="bg-white/5 border-white/10 h-11 pl-10 rounded-xl focus-visible:ring-blue-500" 
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          required
                          aria-required="true"
                       />
                    </div>
                </div>
                <div className="space-y-3">
                    <Label htmlFor="password" className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Security Token</Label>
                    <div className="relative">
                       <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" aria-hidden="true" />
                       <Input 
                          id="password" 
                          type="password" 
                          placeholder="••••••••" 
                          className="bg-white/5 border-white/10 h-11 pl-10 rounded-xl focus-visible:ring-blue-500" 
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          required
                          aria-required="true"
                       />
                    </div>
                </div>
                <Button type="submit" className="w-full h-11 rounded-xl bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/20 font-bold" disabled={loading}>
                    {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Authenticate"}
                </Button>
            </form>
        </CardContent>
        <CardFooter className="justify-center border-t border-white/5 mt-4 pt-6">
            <p className="text-sm text-muted-foreground font-medium">
                Protected system. <Link href="/register" className="text-blue-500 hover:underline">Request access token</Link>
            </p>
        </CardFooter>
      </Card>
      
      <div className="fixed bottom-8 text-center text-[10px] font-bold uppercase tracking-[0.2em] text-gray-700 pointer-events-none">
         DataLogicEngine Hardened Node • UKG v2.1.1
      </div>
    </div>
  );
}
