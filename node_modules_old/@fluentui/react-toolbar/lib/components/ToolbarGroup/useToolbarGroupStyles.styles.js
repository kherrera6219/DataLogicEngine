'use client';

import { __styles, mergeClasses } from '@griffel/react';
export const toolbarGroupClassNames = {
  root: 'fui-ToolbarGroup'
};
const useStyles = /*#__PURE__*/__styles({
  root: {
    mc9l5x: "f22iagw",
    Bt984gj: "f122n59"
  },
  vertical: {
    Beiy3e4: "f1vx9l62",
    a9b677: "f1acs6jw"
  }
}, {
  d: [".f22iagw{display:flex;}", ".f122n59{align-items:center;}", ".f1vx9l62{flex-direction:column;}", ".f1acs6jw{width:fit-content;}"]
});
/**
 * Apply styling to the Toolbar slots based on the state
 */
export const useToolbarGroupStyles_unstable = state => {
  'use no memo';

  const {
    vertical
  } = state;
  const styles = useStyles();
  state.root.className = mergeClasses(toolbarGroupClassNames.root, styles.root, vertical && styles.vertical, state.root.className);
  return state;
};