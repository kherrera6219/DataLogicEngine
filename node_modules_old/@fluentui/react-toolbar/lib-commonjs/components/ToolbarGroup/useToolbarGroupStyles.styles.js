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
const useStyles = /*#__PURE__*/ (0, _react.__styles)({
    root: {
        mc9l5x: "f22iagw",
        Bt984gj: "f122n59"
    },
    vertical: {
        Beiy3e4: "f1vx9l62",
        a9b677: "f1acs6jw"
    }
}, {
    d: [
        ".f22iagw{display:flex;}",
        ".f122n59{align-items:center;}",
        ".f1vx9l62{flex-direction:column;}",
        ".f1acs6jw{width:fit-content;}"
    ]
});
const useToolbarGroupStyles_unstable = (state)=>{
    'use no memo';
    const { vertical } = state;
    const styles = useStyles();
    state.root.className = (0, _react.mergeClasses)(toolbarGroupClassNames.root, styles.root, vertical && styles.vertical, state.root.className);
    return state;
};
