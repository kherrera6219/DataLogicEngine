import React from 'react';

// Render a deliberately small Markdown subset as React text, never as HTML.
function inline(text: string): React.ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.startsWith('*') && part.endsWith('*')) return <em key={index}>{part.slice(1, -1)}</em>;
    if (part.startsWith('`') && part.endsWith('`')) return <code key={index}>{part.slice(1, -1)}</code>;
    return part;
  });
}

export function AnswerContent({ text }: { text: string }) {
  const lines = text.split(/\r?\n/);
  const blocks: React.ReactNode[] = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) { index += 1; continue; }
    if (line.trim() === '$$') {
      const closing = lines.findIndex((value, position) => position > index && value.trim() === '$$');
      if (closing !== -1) {
        const expression = lines.slice(index + 1, closing).join('\n');
        blocks.push(<pre key={blocks.length} aria-label="Equation in LaTeX" className="overflow-x-auto whitespace-pre-wrap rounded bg-slate-100 p-3 dark:bg-black/30">{expression}</pre>);
        index = closing + 1;
        continue;
      }
    }
    if (line.trim().startsWith('```')) {
      const code: string[] = [];
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith('```')) code.push(lines[index++]);
      if (index < lines.length) index += 1;
      blocks.push(<pre key={blocks.length} className="overflow-x-auto whitespace-pre-wrap rounded bg-slate-100 p-3 dark:bg-black/30"><code>{code.join('\n')}</code></pre>);
      continue;
    }
    const heading = /^(#{1,6})\s+(.+)$/.exec(line);
    if (heading) {
      blocks.push(<p role="heading" aria-level={heading[1].length} key={blocks.length} className="font-semibold">{inline(heading[2])}</p>);
      index += 1;
      continue;
    }
    if (/^\s*[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length && /^\s*[-*]\s+/.test(lines[index])) items.push(lines[index++].replace(/^\s*[-*]\s+/, ''));
      blocks.push(<ul key={blocks.length} className="list-disc space-y-1 pl-5">{items.map((item, i) => <li key={i}>{inline(item)}</li>)}</ul>);
      continue;
    }
    if (/^\s*\d+[.)]\s+/.test(line)) {
      const items: string[] = [];
      while (index < lines.length && /^\s*\d+[.)]\s+/.test(lines[index])) items.push(lines[index++].replace(/^\s*\d+[.)]\s+/, ''));
      blocks.push(<ol key={blocks.length} className="list-decimal space-y-1 pl-5">{items.map((item, i) => <li key={i}>{inline(item)}</li>)}</ol>);
      continue;
    }
    const paragraph: string[] = [];
    while (index < lines.length && lines[index].trim() && !/^(#{1,6})\s+(.+)$/.test(lines[index]) && !/^\s*[-*]\s+/.test(lines[index]) && !/^\s*\d+[.)]\s+/.test(lines[index]) && !lines[index].trim().startsWith('```')) paragraph.push(lines[index++]);
    blocks.push(<p key={blocks.length} className="whitespace-pre-wrap">{inline(paragraph.join('\n'))}</p>);
  }
  return <div className="space-y-3 break-words">{blocks}</div>;
}
