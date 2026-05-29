'use client';

import { useEffect, useState } from 'react';
import { socketClient, useSocket, type TraceStageUpdate } from '@/lib/socket';

export function useTraceStream(runId: string | null) {
  const [layers, setLayers] = useState<TraceStageUpdate[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      setLayers((prev) => {
        const next = [...prev];
        const idx = next.findIndex((item) => item.stage_id && item.stage_id === data.stage_id);
        if (idx >= 0) {
          next[idx] = { ...next[idx], ...data };
        } else {
          next.push(data);
        }
        return next;
      });
    },
  });

  useEffect(() => {
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
