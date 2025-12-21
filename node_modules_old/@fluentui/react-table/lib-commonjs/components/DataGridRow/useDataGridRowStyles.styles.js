'use client';
"use strict";
Object.defineProperty(exports, "__esModule", {
    value: true
});
function _export(target, all) {
    for(var name in all)Object.defineProperty(target, name, {
        enumerable: true,
        get: all[name]
    });
}
_export(exports, {
    dataGridRowClassNames: function() {
        return dataGridRowClassNames;
    },
    useDataGridRowStyles_unstable: function() {
        return useDataGridRowStyles_unstable;
    }
});
const _react = require("@griffel/react");
const _useTableRowStylesstyles = require("../TableRow/useTableRowStyles.styles");
const _dataGridContext = require("../../contexts/dataGridContext");
const dataGridRowClassNames = {
    root: 'fui-DataGridRow',
    selectionCell: 'fui-DataGridRow__selectionCell'
};
const useStyles = /*#__PURE__*/ (0, _react.__styles)({
    subtleSelection: {
        Bconypa: "f1jazu75",
        ff6mpl: "fw60kww"
    }
}, {
    d: [
        ".f1jazu75[data-fui-focus-within]:focus-within .fui-TableSelectionCell{opacity:1;}"
    ],
    h: [
        ".fw60kww:hover .fui-TableSelectionCell{opacity:1;}"
    ]
});
const useDataGridRowStyles_unstable = (state)=>{
    'use no memo';
    const isSubtle = (0, _dataGridContext.useDataGridContext_unstable)((ctx)=>ctx.subtleSelection);
    const styles = useStyles();
    (0, _useTableRowStylesstyles.useTableRowStyles_unstable)(state);
    state.root.className = (0, _react.mergeClasses)(dataGridRowClassNames.root, state.root.className, isSubtle && styles.subtleSelection);
    if (state.selectionCell) {
        state.selectionCell.className = (0, _react.mergeClasses)(dataGridRowClassNames.selectionCell, state.selectionCell.className);
    }
    return state;
};
