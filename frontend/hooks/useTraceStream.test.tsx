import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useTraceStream } from './useTraceStream';

const socketState = vi.hoisted(() => ({
  handlers: {} as Record<string, ((payload?: unknown) => void) | undefined>,
  joinRunRoom: vi.fn(),
  leaveRunRoom: vi.fn(),
}));

vi.mock('@/lib/socket', () => ({
  socketClient: {
    isConnected: true,
    joinRunRoom: socketState.joinRunRoom,
    leaveRunRoom: socketState.leaveRunRoom,
  },
  useSocket: (handlers: Record<string, ((payload?: unknown) => void) | undefined>) => {
    socketState.handlers = handlers;
  },
}));

describe('useTraceStream', () => {
  beforeEach(() => {
    socketState.handlers = {};
    socketState.joinRunRoom.mockReset();
    socketState.leaveRunRoom.mockReset();
  });

  it('orders events, ignores duplicates, and keeps the newest stage receipt', () => {
    const { result } = renderHook(() => useTraceStream('run-1'));
    const onUpdate = socketState.handlers.onTraceStageUpdate as (payload: unknown) => void;

    act(() => {
      onUpdate({
        schema_version: 'dle.public-trace-event.v1',
        event_id: 'event-2',
        sequence: 2,
        run_id: 'run-1',
        stage_id: 'stage-1',
        name: 'Retrieve context',
        status: 'completed',
        narrative: 'Retrieved 2 evidence records.',
      });
      onUpdate({
        schema_version: 'dle.public-trace-event.v1',
        event_id: 'event-1',
        sequence: 1,
        run_id: 'run-1',
        stage_id: 'stage-1',
        name: 'Retrieve context',
        status: 'running',
        narrative: 'Started Retrieve context.',
      });
      onUpdate({
        schema_version: 'dle.public-trace-event.v1',
        event_id: 'event-2',
        sequence: 2,
        run_id: 'run-1',
        stage_id: 'stage-1',
        name: 'Retrieve context',
        status: 'completed',
        narrative: 'Retrieved 2 evidence records.',
      });
    });

    expect(result.current.layers).toHaveLength(1);
    expect(result.current.layers[0]).toMatchObject({
      event_id: 'event-2',
      sequence: 2,
      stage_id: 'stage-1',
      status: 'completed',
    });
  });

  it('rejoins after reconnect and filters events from another run', () => {
    const { result } = renderHook(() => useTraceStream('run-1'));
    const onUpdate = socketState.handlers.onTraceStageUpdate as (payload: unknown) => void;

    act(() => {
      socketState.handlers.onConnected?.({ status: 'connected', sid: 'socket-1' });
      onUpdate({
        schema_version: 'dle.public-trace-event.v1',
        event_id: 'other-event',
        sequence: 1,
        run_id: 'run-2',
        stage_id: 'other-stage',
        name: 'Other',
        status: 'running',
        narrative: 'Started Other.',
      });
    });

    expect(socketState.joinRunRoom).toHaveBeenCalledWith('run-1');
    expect(result.current.layers).toEqual([]);
  });
});
