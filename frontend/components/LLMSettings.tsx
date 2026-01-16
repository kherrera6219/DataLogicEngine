"use strict";

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { Key, ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';


const LLMSettings = () => {
  const [provider, setProvider] = useState('openai');
  const [apiKey, setApiKey] = useState('');
  const [status, setStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSave = async () => {
    setStatus('saving');
    try {
      const response = await fetch('/api/v1/gateway/keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider,
          key: apiKey,
        }),
      });

      if (response.ok) {
        setStatus('success');
        setMessage('API Key saved securely via Windows DPAPI');
        setApiKey('');
      } else {
        const error = await response.json();
        setStatus('error');
        setMessage(error.message || 'Failed to save key');
      }
    } catch {
      setStatus('error');
      setMessage('Network error while saving key');
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto border-premium shadow-lg bg-background/50 backdrop-blur-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-2xl font-bold text-primary">
          <Key className="w-6 h-6" />
          LLM Configuration
        </CardTitle>
        <p className="text-muted-foreground">
          Enter your API keys to enable LLM-augmented simulation. Keys are stored locally and encrypted using Windows DPAPI.
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="provider">Provider</Label>
          <select
            id="provider"
            title="LLM Provider Selector"
            className="w-full p-2 rounded-md border border-input bg-background focus:ring-2 focus:ring-primary outline-none transition-all"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google Gemini</option>
            <option value="huggingface">Hugging Face</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="apiKey">API Key</Label>
          <div className="relative">
            <Input
              id="apiKey"
              type="password"
              placeholder="sk-..."
              className="pr-10"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
            <ShieldCheck className="absolute right-3 top-2.5 w-5 h-5 text-muted-foreground/50" />
          </div>
        </div>

        <Button 
          onClick={handleSave} 
          disabled={status === 'saving' || !apiKey}
          className="w-full py-6 text-lg font-semibold transition-all hover:scale-[1.01]"
        >
          {status === 'saving' ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Saving Encrypted Key...
            </>
          ) : (
            'Save Securely'
          )}
        </Button>

        {status === 'success' && (
          <Alert className="bg-green-500/10 border-green-500/50 text-green-600 dark:text-green-400">
            <ShieldCheck className="h-4 w-4" />
            <AlertDescription>{message}</AlertDescription>
          </Alert>
        )}

        {status === 'error' && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{message}</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default LLMSettings;
