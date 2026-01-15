'use client';

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { Button } from './button';
import { useToast } from './use-toast';

interface CopyButtonProps {
  text: string;
  className?: string;
}

export function CopyButton({ text, className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast("Response copied to clipboard", "success", 2000);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast("Failed to copy text", "error", 2000);
    }
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      className={className}
      onClick={handleCopy}
      aria-label={copied ? "Copied to clipboard" : "Copy response to clipboard"}
    >
      {copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
    </Button>
  );
}
