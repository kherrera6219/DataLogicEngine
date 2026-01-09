import { auth } from './auth';
import { simulation } from './simulation';
import { knowledge } from './knowledge';
import { trace } from './trace';
import { system, chat, sendChat } from './system_chat';

export * from './types';
export { sendChat };

export * from './mcp';

// Base config
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1';
export const MCP_API_BASE = process.env.NEXT_PUBLIC_MCP_API_URL || 'http://localhost:5000/api/mcp';

import { compliance } from "./compliance";

export const api = {
    chat,
    auth,
    trace,
    knowledge,
    simulation,
    system,
    compliance
};
```
