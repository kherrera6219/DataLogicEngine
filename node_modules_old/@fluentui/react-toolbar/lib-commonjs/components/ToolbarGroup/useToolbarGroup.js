'use client';
"use strict";
Object.defineProperty(exports, "__esModule", {
    value: true
});
Object.defineProperty(exports, "useToolbarGroup_unstable", {
    enumerable: true,
    get: function() {
        return useToolbarGroup_unstable;
    }
});
const _interop_require_wildcard = require("@swc/helpers/_/_interop_require_wildcard");
const _reactutilities = require("@fluentui/react-utilities");
const _react = /*#__PURE__*/ _interop_require_wildcard._(require("react"));
const _ToolbarContext = require("../Toolbar/ToolbarContext");
const useToolbarGroup_unstable = (props, ref)=>{
    const vertical = (0, _ToolbarContext.useToolbarContext_unstable)((ctx)=>ctx.vertical);
    return {
        components: {
            root: 'div'
        },
        root: _reactutilities.slot.always((0, _reactutilities.getIntrinsicElementProps)('div', {
            ref,
            role: 'presentation',
            ...props
        }), {
            elementType: 'div'
        }),
        vertical
    };
};
