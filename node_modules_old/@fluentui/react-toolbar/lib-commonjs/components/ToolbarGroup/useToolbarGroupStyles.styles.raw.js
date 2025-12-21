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
    toolbarGroupClassNames: function() {
        return toolbarGroupClassNames;
    },
    useToolbarGroupStyles_unstable: function() {
        return useToolbarGroupStyles_unstable;
    }
});
const _react = require("@griffel/react");
const toolbarGroupClassNames = {
    root: 'fui-ToolbarGroup'
};
const useStyles = (0, _react.makeStyles)({
    root: {
        display: 'flex',
        alignItems: 'center'
    },
    vertical: {
        flexDirection: 'column',
        width: 'fit-content'
    }
});
const useToolbarGroupStyles_unstable = (state)=>{
    'use no memo';
    const { vertical } = state;
    const styles = useStyles();
    state.root.className = (0, _react.mergeClasses)(toolbarGroupClassNames.root, styles.root, vertical && styles.vertical, state.root.className);
    return state;
};
