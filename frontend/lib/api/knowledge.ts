import { KnowledgePillar, KnowledgeStats, GraphNode, GraphEdge } from './types';
import { request } from '@/lib/api/index';

export const knowledge = {
    pillars: () => request<KnowledgePillar[]>('/ukg/pillars'),
    stats: () => request<KnowledgeStats>('/analytics/summary'),
    getNodes: () => request<GraphNode[]>('/ukg/nodes'),
    getEdges: () => request<GraphEdge[]>('/ukg/edges')
};
