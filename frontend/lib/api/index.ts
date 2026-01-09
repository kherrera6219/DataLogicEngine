import { auth } from './auth';
import { simulation } from './simulation';
import { knowledge } from './knowledge';
import { trace } from './trace';
import { system, chat, sendChat } from './system_chat';

export * from './types';
export { sendChat };

export const api = {
    chat,
    auth,
    trace,
    knowledge,
    simulation,
    system
};
