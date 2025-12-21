'use client';
import * as React from 'react';
import { useFluent_unstable as useFluent } from '@fluentui/react-shared-contexts';
const setTimeoutNoop = (_callback)=>-1;
const clearTimeoutNoop = (_handle)=>undefined;
/**
 * @internal
 * @param triggerElementRef - Reference to the trigger element
 * @returns A pair of [setTimeout, clearTimeout] that are stable between renders.
 */ export function useTooltipTimeout(// eslint-disable-next-line @typescript-eslint/no-deprecated
triggerElementRef) {
    const { targetDocument } = useFluent();
    const win = targetDocument === null || targetDocument === void 0 ? void 0 : targetDocument.defaultView;
    const setTimerFn = win ? win.setTimeout : setTimeoutNoop;
    const clearTimerFn = win ? win.clearTimeout : clearTimeoutNoop;
    const id = React.useRef(undefined);
    const set = React.useCallback((fn, delay)=>{
        if (id.current !== undefined) {
            clearTimerFn(id.current);
        }
        id.current = setTimerFn(fn, delay !== null && delay !== void 0 ? delay : 0);
        return id.current;
    }, [
        clearTimerFn,
        setTimerFn
    ]);
    const cancel = React.useCallback(()=>{
        if (id.current !== undefined) {
            clearTimerFn(id.current);
            id.current = undefined;
        }
    }, [
        clearTimerFn
    ]);
    // StrictMode-aware cleanup: only clear timeout if element has no parent (real unmount)
    React.useEffect(()=>{
        const el = triggerElementRef.current;
        return ()=>{
            const isRealUnmount = !el || !el.isConnected;
            if (isRealUnmount) {
                cancel();
            }
        };
    }, [
        cancel,
        triggerElementRef
    ]);
    return [
        set,
        cancel
    ];
}
