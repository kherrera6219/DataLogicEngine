import { KnowledgePillar, KnowledgeStats } from './types';
import { request } from './index';

export const knowledge = {
    pillars: () => request<KnowledgePillar[]>('/knowledge/pillars'),
    stats: () => request<KnowledgeStats>('/knowledge/stats')
.then(d => d.length).catch(() => 0)
};
