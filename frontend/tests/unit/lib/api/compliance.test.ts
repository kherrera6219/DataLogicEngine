import { describe, it, expect, vi, beforeEach } from 'vitest';
import { compliance } from '@/lib/api/compliance';
import { request, API_BASE } from '@/lib/api/index';

vi.mock('./index', () => ({
    request: vi.fn(),
    API_BASE: 'http://localhost:5000/api'
}));

describe('Compliance API Client', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.stubGlobal('window', { open: vi.fn() });
    });

    it('standards should call /compliance/standards', async () => {
        const mockStandards = [{ id: 's1', name: 'GDPR' }];
        vi.mocked(request).mockResolvedValue(mockStandards);

        const result = await compliance.standards();
        
        expect(request).toHaveBeenCalledWith('/compliance/standards');
        expect(result).toEqual(mockStandards);
    });

    it('standards should support type filter', async () => {
        await compliance.standards('regulatory');
        expect(request).toHaveBeenCalledWith('/compliance/standards?type=regulatory');
    });

    it('exportAuditLogs should open the export endpoint in a new tab', async () => {
        await compliance.exportAuditLogs(15);
        expect(window.open).toHaveBeenCalledWith(
            'http://localhost:5000/api/compliance/audit/export?days=15',
            '_blank'
        );
    });
});
