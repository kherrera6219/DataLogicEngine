'use client';

import { __styles, mergeClasses } from '@griffel/react';
import { createCustomFocusIndicatorStyle } from '@fluentui/react-tabster';
import { useTableRowStyles_unstable } from '../TableRow/useTableRowStyles.styles';
import { useDataGridContext_unstable } from '../../contexts/dataGridContext';
import { tableSelectionCellClassNames } from '../TableSelectionCell/useTableSelectionCellStyles.styles';
export const dataGridRowClassNames = {
  root: 'fui-DataGridRow',
  selectionCell: 'fui-DataGridRow__selectionCell'
};
const useStyles = /*#__PURE__*/__styles({
  subtleSelection: {
    Bconypa: "f1jazu75",
    ff6mpl: "fw60kww"
  }
}, {
  d: [".f1jazu75[data-fui-focus-within]:focus-within .fui-TableSelectionCell{opacity:1;}"],
  h: [".fw60kww:hover .fui-TableSelectionCell{opacity:1;}"]
});
/**
 * Apply styling to the DataGridRow slots based on the state
 */
export const useDataGridRowStyles_unstable = state => {
  'use no memo';

  const isSubtle = useDataGridContext_unstable(ctx => ctx.subtleSelection);
  const styles = useStyles();
  useTableRowStyles_unstable(state);
  state.root.className = mergeClasses(dataGridRowClassNames.root, state.root.className, isSubtle && styles.subtleSelection);
  if (state.selectionCell) {
    state.selectionCell.className = mergeClasses(dataGridRowClassNames.selectionCell, state.selectionCell.className);
  }
  return state;
};