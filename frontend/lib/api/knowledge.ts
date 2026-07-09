import { KnowledgePillar, KnowledgeStats, GraphNode, GraphEdge } from './types';
import { request } from '@/lib/api/client';

export const knowledge = {
    pillars: () => request<KnowledgePillar[]>('/pillars'),
    stats: () => request<KnowledgeStats>('/analytics/summary'),
    getNodes: () => request<GraphNode[]>('/nodes'),
    getEdges: () => request<GraphEdge[]>('/edges')
};
