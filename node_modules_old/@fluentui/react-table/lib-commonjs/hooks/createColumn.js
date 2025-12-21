"use strict";
Object.defineProperty(exports, "__esModule", {
    value: true
});
Object.defineProperty(exports, "createTableColumn", {
    enumerable: true,
    get: function() {
        return createTableColumn;
    }
});
const _interop_require_wildcard = require("@swc/helpers/_/_interop_require_wildcard");
const _react = /*#__PURE__*/ _interop_require_wildcard._(require("react"));
const defaultCompare = ()=>0;
const defaultRenderCell = ()=>{
    if (process.env.NODE_ENV !== 'production') {
        // eslint-disable-next-line no-console
        console.warn('@fluentui/react-table: You are using the default column renderCell function that renders null');
    }
    return null;
};
const defaultRenderHeaderCell = ()=>{
    if (process.env.NODE_ENV !== 'production') {
        // eslint-disable-next-line no-console
        console.warn('@fluentui/react-table: You are using the default column renderHeaderCell function that renders null');
    }
    return null;
};
function createTableColumn(options) {
    const { columnId, renderCell = defaultRenderCell, renderHeaderCell = defaultRenderHeaderCell, compare = defaultCompare } = options;
    return {
        columnId,
        renderCell,
        renderHeaderCell,
        compare
    };
}
