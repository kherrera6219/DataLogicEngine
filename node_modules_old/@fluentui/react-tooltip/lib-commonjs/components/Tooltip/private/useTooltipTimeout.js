'use client';
"use strict";
Object.defineProperty(exports, "__esModule", {
    value: true
});
Object.defineProperty(exports, "useTooltipTimeout", {
    enumerable: true,
    get: function() {
        return useTooltipTimeout;
    }
});
const _interop_require_wildcard = require("@swc/helpers/_/_interop_require_wildcard");
const _react = /*#__PURE__*/ _interop_require_wildcard._(require("react"));
const _reactsharedcontexts = require("@fluentui/react-shared-contexts");
const setTimeoutNoop = (_callback)=>-1;
const clearTimeoutNoop = (_handle)=>undefined;
function useTooltipTimeout(triggerElementRef) {
    const { targetDocument } = (0, _reactsharedcontexts.useFluent_unstable)();
    const win = targetDocument === null || targetDocument === void 0 ? void 0 : targetDocument.defaultView;
    const setTimerFn = win ? win.setTimeout : setTimeoutNoop;
    const clearTimerFn = win ? win.clearTimeout : clearTimeoutNoop;
    const id = _react.useRef(undefined);
    const set = _react.useCallback((fn, delay)=>{
        if (id.current !== undefined) {
            clearTimerFn(id.current);
        }
        id.current = setTimerFn(fn, delay !== null && delay !== void 0 ? delay : 0);
        return id.current;
    }, [
        clearTimerFn,
        setTimerFn
    ]);
    const cancel = _react.useCallback(()=>{
        if (id.current !== undefined) {
            clearTimerFn(id.current);
            id.current = undefined;
        }
    }, [
        clearTimerFn
    ]);
    // StrictMode-aware cleanup: only clear timeout if element has no parent (real unmount)
    _react.useEffect(()=>{
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
