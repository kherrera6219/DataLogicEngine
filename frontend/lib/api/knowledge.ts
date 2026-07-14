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
    source?: string;
    stats?: {
        source_revision?: string;
        last_loaded_at?: string | null;
    };
};

export type KnowledgeGraph = {
    nodes: GraphNode[];
    links: GraphEdge[];
    source?: string;
    source_revision?: string;
    last_loaded_at?: string | null;
};

function normalizeGraph(payload: GraphApiResponse): KnowledgeGraph {
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
        source: payload.source,
        source_revision: payload.stats?.source_revision,
        last_loaded_at: payload.stats?.last_loaded_at,
    };
}

export const knowledge = {
    pillars: () => request<KnowledgePillar[]>('/pillar-levels'),
    stats: () => request<KnowledgeStats>('/analytics/overview'),
    graph: (axis?: number, options?: { root?: string; depth?: number }) => {
        const params = new URLSearchParams();
        if (axis) params.set('axis', String(axis));
        if (options?.root) params.set('root', options.root);
        if (options?.root && options.depth !== undefined) params.set('depth', String(options.depth));
        const query = params.toString();
        return request<GraphApiResponse>(query ? `/graph?${query}` : '/graph').then(normalizeGraph);
    },
    getNodes: () => request<GraphApiResponse>('/graph').then((payload) => normalizeGraph(payload).nodes),
    getEdges: () => request<GraphApiResponse>('/graph').then((payload) => normalizeGraph(payload).links),
};
