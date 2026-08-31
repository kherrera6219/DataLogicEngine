'use client';

import { useEffect, useRef, useState } from 'react';
import { socketClient, useSocket, type TraceStageUpdate } from '@/lib/socket';

export function useTraceStream(runId: string | null) {
  const [layers, setLayers] = useState<TraceStageUpdate[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const seenEventIds = useRef(new Set<string>());

  useSocket({
    onConnected: () => {
      setConnected(true);
      setError(null);
      if (runId) {
        socketClient.joinRunRoom(runId);
      }
    },
    onDisconnected: () => {
      setConnected(false);
    },
    onTraceStageUpdate: (data) => {
      if (!runId || data.run_id !== runId) return;
      if (seenEventIds.current.has(data.event_id)) return;
      seenEventIds.current.add(data.event_id);
      setLayers((prev) => {
        const next = [...prev];
        const idx = next.findIndex((item) => item.stage_id === data.stage_id);
        if (idx >= 0) {
          if (next[idx].sequence >= data.sequence) return prev;
          next[idx] = data;
        } else {
          next.push(data);
        }
        return next.sort((left, right) => left.sequence - right.sequence);
      });
    },
  });

  useEffect(() => {
    seenEventIds.current.clear();
    if (!runId) {
      return undefined;
    }

    socketClient.joinRunRoom(runId);

    return () => {
      socketClient.leaveRunRoom(runId);
    };
  }, [runId]);

  return { layers: runId ? layers.filter((layer) => layer.run_id === runId) : [], connected: connected || socketClient.isConnected, error };
}
