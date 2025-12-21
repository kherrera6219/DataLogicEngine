'use client';
import * as React from 'react';
import { getIntrinsicElementProps, useMergedRefs, slot } from '@fluentui/react-utilities';
import { useFocusWithin } from '@fluentui/react-tabster';
import { ArrowUpRegular, ArrowDownRegular } from '@fluentui/react-icons';
import { useARIAButtonProps } from '@fluentui/react-aria';
import { useTableContext } from '../../contexts/tableContext';
const sortIcons = {
    ascending: /*#__PURE__*/ React.createElement(ArrowUpRegular, {
        fontSize: 12
    }),
    descending: /*#__PURE__*/ React.createElement(ArrowDownRegular, {
        fontSize: 12
    })
};
/**
 * Create the state required to render TableHeaderCell.
 *
 * The returned state can be modified with hooks such as useTableHeaderCellStyles_unstable,
 * before being passed to renderTableHeaderCell_unstable.
 *
 * @param props - props from this instance of TableHeaderCell
 * @param ref - reference to root HTMLElement of TableHeaderCell
 */ export const useTableHeaderCell_unstable = (props, ref)=>{
    const { noNativeElements, sortable: contextSortable } = useTableContext();
    const { sortable = contextSortable } = props;
    var _props_as;
    const rootComponent = ((_props_as = props.as) !== null && _props_as !== void 0 ? _props_as : noNativeElements) ? 'div' : 'th';
    // The sort button is rendered as a div when not sortable, and as an ARIA button when sortable.
    const buttonSlot = slot.always(props.button, {
        elementType: 'div',
        defaultProps: {
            as: 'div'
        }
    });
    const ariaButtonProps = useARIAButtonProps(buttonSlot.as, buttonSlot);
    var _props_sortDirection;
    return {
        components: {
            root: rootComponent,
            button: 'div',
            sortIcon: 'span',
            aside: 'span'
        },
        root: slot.always(getIntrinsicElementProps(rootComponent, {
            // FIXME:
            // `ref` is wrongly assigned to be `HTMLElement` instead of `HTMLDivElement`
            // but since it would be a breaking change to fix it, we are casting ref to it's proper type
            ref: useMergedRefs(ref, useFocusWithin()),
            role: rootComponent === 'div' ? 'columnheader' : undefined,
            'aria-sort': sortable ? (_props_sortDirection = props.sortDirection) !== null && _props_sortDirection !== void 0 ? _props_sortDirection : 'none' : undefined,
            ...props
        }), {
            elementType: rootComponent
        }),
        aside: slot.optional(props.aside, {
            elementType: 'span'
        }),
        sortIcon: slot.optional(props.sortIcon, {
            renderByDefault: !!props.sortDirection,
            defaultProps: {
                children: props.sortDirection ? sortIcons[props.sortDirection] : undefined
            },
            elementType: 'span'
        }),
        button: sortable ? ariaButtonProps : buttonSlot,
        sortable,
        noNativeElements
    };
};
