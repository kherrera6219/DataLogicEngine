import { KnowledgePillar, KnowledgeStats, GraphNode, GraphEdge } from './types';
import { request } from '@/lib/api/client';

type GraphApiNode = {
    id: string | number;
    label?: string;
    name?: string;
    node_type?: string;
    size?: number;
    value?: number;
    pillar?: string;
    axis_number?: number;
    attributes?: Record<string, unknown>;
};

type GraphApiEdge = {
    source: string | number;
    target: string | number;
    label?: string;
    edge_type?: string;
    value?: number;
    weight?: number;
};

type GraphApiResponse = {
    nodes?: GraphApiNode[];
    links?: GraphApiEdge[];
};

function normalizeGraph(payload: GraphApiResponse): { nodes: GraphNode[]; links: GraphEdge[] } {
    return {
        nodes: (payload.nodes || []).map((node) => ({
            ...node,
            id: String(node.id),
            name: node.name || node.label || String(node.id),
            val: node.value ?? node.size ?? 1,
        })),
        links: (payload.links || []).map((edge) => ({
            ...edge,
            source: String(edge.source),
            target: String(edge.target),
            edge_type: edge.edge_type || edge.label,
            weight: edge.weight ?? edge.value,
        })),
    };
}

export const knowledge = {
    pillars: () => request<KnowledgePillar[]>('/pillar-levels'),
    stats: () => request<KnowledgeStats>('/analytics/overview'),
    graph: (axis?: number) => request<GraphApiResponse>(axis ? `/graph?axis=${axis}` : '/graph').then(normalizeGraph),
    getNodes: () => request<GraphApiResponse>('/graph').then((payload) => normalizeGraph(payload).nodes),
    getEdges: () => request<GraphApiResponse>('/graph').then((payload) => normalizeGraph(payload).links),
};
