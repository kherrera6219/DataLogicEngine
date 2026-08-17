import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import MemoryManagementSettings from './MemoryManagementSettings';
import { api } from '@/lib/api';

const mocks = vi.hoisted(() => ({
  toast: vi.fn(),
  review: vi.fn(),
  exportGraph: vi.fn(),
  remove: vi.fn(),
  compact: vi.fn(),
  recover: vi.fn(),
}));

vi.mock('@/components/ui/use-toast', () => ({ useToast: () => ({ toast: mocks.toast }) }));
vi.mock('@/lib/api', () => ({
  api: {
    memory: {
      review: mocks.review,
      exportGraph: mocks.exportGraph,
      remove: mocks.remove,
      compact: mocks.compact,
      recover: mocks.recover,
    },
  },
}));

const item = {
  vertex_id: 'memory-1',
  content: 'A validated memory record',
  validation_state: 'validated',
  retention_class: 'durable',
  policy_result: 'allow',
  source_run_id: 'run 1',
};

beforeEach(() => {
  vi.clearAllMocks();
  mocks.review.mockResolvedValue({
    items: [item],
    stats: { memory_vertices: 1, memory_edges: 2, last_recall_timestamp: '2026-08-16T20:00:00Z' },
  });
  mocks.exportGraph.mockResolvedValue({ vertices: [item] });
  mocks.remove.mockResolvedValue({ removed: true });
  mocks.compact.mockResolvedValue({ removed: 3 });
  mocks.recover.mockResolvedValue({ recovered: true });
  vi.spyOn(window, 'confirm').mockReturnValue(true);
  Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:test') });
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
});

describe('MemoryManagementSettings', () => {
  it('loads stats and records and toggles the working-memory filter', async () => {
    render(<MemoryManagementSettings />);
    expect(await screen.findByText('A validated memory record')).toBeInTheDocument();
    expect(screen.getByText('1 records')).toBeInTheDocument();
    expect(screen.getByText('2 edges')).toBeInTheDocument();
    expect(screen.getByText(/Last recall:/)).not.toHaveTextContent('never');
    expect(screen.getByRole('link', { name: 'Source trace' })).toHaveAttribute(
      'href',
      '/runs/view?id=run%201',
    );
    fireEvent.click(screen.getByRole('switch', { name: 'Include working memory' }));
    await waitFor(() => expect(mocks.review).toHaveBeenCalledWith(true));
    fireEvent.click(screen.getByRole('button', { name: /Refresh/i }));
    await waitFor(() => expect(mocks.review).toHaveBeenCalledTimes(3));
  });

  it('exports deletes compacts and recovers after confirmation', async () => {
    render(<MemoryManagementSettings />);
    await screen.findByText('A validated memory record');
    fireEvent.click(screen.getByRole('button', { name: /Export/i }));
    await waitFor(() => expect(mocks.exportGraph).toHaveBeenCalled());
    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:test');

    fireEvent.click(screen.getByRole('button', { name: 'Delete memory memory-1' }));
    await waitFor(() => expect(mocks.remove).toHaveBeenCalledWith('memory-1'));
    fireEvent.click(screen.getByRole('button', { name: /Compact/i }));
    await waitFor(() => expect(mocks.compact).toHaveBeenCalledWith(500));
    fireEvent.click(screen.getByRole('button', { name: /Recover/i }));
    await waitFor(() => expect(mocks.recover).toHaveBeenCalled());
    expect(mocks.toast).toHaveBeenCalledWith('Memory export created.', 'success');
    expect(mocks.toast).toHaveBeenCalledWith('Memory record deleted.', 'success');
    expect(mocks.toast).toHaveBeenCalledWith('Memory compacted: 3 working records removed.', 'success');
    expect(mocks.toast).toHaveBeenCalledWith('Memory recovered from the verified backup.', 'success');
  });

  it('honors cancelled destructive actions', async () => {
    vi.mocked(window.confirm).mockReturnValue(false);
    render(<MemoryManagementSettings />);
    await screen.findByText('A validated memory record');
    fireEvent.click(screen.getByRole('button', { name: 'Delete memory memory-1' }));
    fireEvent.click(screen.getByRole('button', { name: /Compact/i }));
    fireEvent.click(screen.getByRole('button', { name: /Recover/i }));
    expect(mocks.remove).not.toHaveBeenCalled();
    expect(mocks.compact).not.toHaveBeenCalled();
    expect(mocks.recover).not.toHaveBeenCalled();
  });

  it('renders empty, default-stat, Error, and non-Error failure states', async () => {
    mocks.review.mockResolvedValueOnce({
      items: [],
      stats: { memory_vertices: 0, memory_edges: 0, last_recall_timestamp: null },
    });
    const { unmount } = render(<MemoryManagementSettings />);
    expect(await screen.findByText('No memory records match this review filter.')).toBeInTheDocument();
    expect(screen.getByText('Last recall: never')).toBeInTheDocument();
    unmount();

    mocks.review.mockRejectedValueOnce(new Error('review failed'));
    const second = render(<MemoryManagementSettings />);
    expect(await screen.findByText('review failed')).toBeInTheDocument();
    second.unmount();

    mocks.review.mockRejectedValueOnce('offline');
    render(<MemoryManagementSettings />);
    expect(await screen.findByText('Memory review is unavailable.')).toBeInTheDocument();
  });

  it('does not update state after an in-flight initial request is unmounted', async () => {
    let resolveReview!: (value: unknown) => void;
    mocks.review.mockReturnValueOnce(new Promise((resolve) => { resolveReview = resolve; }));
    const view = render(<MemoryManagementSettings />);
    view.unmount();
    resolveReview({ items: [], stats: null });
    await Promise.resolve();
    expect(api.memory.review).toHaveBeenCalledWith(false);
  });
});
