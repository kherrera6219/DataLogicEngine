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
    createNextFlatCheckedItems: function() {
        return createNextFlatCheckedItems;
    },
    useFlatControllableCheckedItems: function() {
        return useFlatControllableCheckedItems;
    }
});
const _interop_require_wildcard = require("@swc/helpers/_/_interop_require_wildcard");
const _reactutilities = require("@fluentui/react-utilities");
const _ImmutableMap = require("../../utils/ImmutableMap");
const _react = /*#__PURE__*/ _interop_require_wildcard._(require("react"));
const _createCheckedItems = require("../../utils/createCheckedItems");
function useFlatControllableCheckedItems(props, headlessTree) {
    return (0, _reactutilities.useControllableState)({
        initialState: _ImmutableMap.ImmutableMap.empty,
        state: _react.useMemo(()=>props.selectionMode ? props.checkedItems && (0, _createCheckedItems.createCheckedItems)(props.checkedItems) : undefined, [
            props.checkedItems,
            props.selectionMode
        ]),
        defaultState: props.defaultCheckedItems ? ()=>initializeCheckedItems(props, headlessTree) : undefined
    });
}
function createNextFlatCheckedItems(data, previousCheckedItems, headlessTree) {
    if (data.selectionMode === 'single') {
        return _ImmutableMap.ImmutableMap.from([
            [
                data.value,
                data.checked
            ]
        ]);
    }
    const treeItem = headlessTree.get(data.value);
    if (!treeItem) {
        if (process.env.NODE_ENV !== 'production') {
            // eslint-disable-next-line no-console
            console.error(`@fluentui/react-tree [useHeadlessFlatTree]:
Tree item ${data.value} not found.`);
        }
        return previousCheckedItems;
    }
    // Calling `ImmutableMap.set()` creates a new ImmutableMap - avoid this in loops.
    // Instead write all updates to a native Map and create a new ImmutableMap at the end.
    // Note that all descendants of the toggled item are processed even if they are collapsed,
    // making the choice of algorithm more important.
    const nextCheckedItemsMap = new Map(_ImmutableMap.ImmutableMap.dangerouslyGetInternalMap(previousCheckedItems));
    // The toggled item itself
    nextCheckedItemsMap.set(data.value, data.checked);
    // Descendant updates
    for (const children of headlessTree.subtree(data.value)){
        nextCheckedItemsMap.set(children.value, data.checked);
    }
    // Ancestor updates - must be done after adding descendants and the toggle item.
    // If any ancestor is mixed, all ancestors above it are mixed too.
    let isAncestorsMixed = false;
    for (const ancestor of headlessTree.ancestors(treeItem.value)){
        if (isAncestorsMixed) {
            nextCheckedItemsMap.set(ancestor.value, 'mixed');
            continue;
        }
        // For each ancestor, if all of its children now have the same checked state as the toggled item,
        // set the ancestor to that checked state too. Otherwise it is 'mixed'.
        let childrenWithSameState = 0;
        for (const child of headlessTree.children(ancestor.value)){
            if ((nextCheckedItemsMap.get(child.value) || false) === data.checked) {
                childrenWithSameState++;
            }
        }
        if (childrenWithSameState === ancestor.childrenValues.length) {
            nextCheckedItemsMap.set(ancestor.value, data.checked);
        } else {
            nextCheckedItemsMap.set(ancestor.value, 'mixed');
            isAncestorsMixed = true;
        }
    }
    const nextCheckedItems = _ImmutableMap.ImmutableMap.from(nextCheckedItemsMap);
    return nextCheckedItems;
}
function initializeCheckedItems(props, headlessTree) {
    if (!props.selectionMode) {
        return _ImmutableMap.ImmutableMap.empty;
    }
    let state = (0, _createCheckedItems.createCheckedItems)(props.defaultCheckedItems);
    // if selectionMode is multiselect, we need to calculate the checked state of all children
    // and ancestors of the defaultCheckedItems
    if (props.selectionMode === 'multiselect') {
        for (const [value, checked] of state){
            state = createNextFlatCheckedItems({
                value,
                checked,
                selectionMode: props.selectionMode
            }, state, headlessTree);
        }
    }
    return state;
}
