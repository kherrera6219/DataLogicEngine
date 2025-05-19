
import { createDarkTheme, createLightTheme } from '@fluentui/react-components';

// Define brand colors
const brandColors = {
  primary: {
    base: '#0078d4', // Microsoft blue
    darker: '#106ebe',
    darkest: '#004578',
    lighter: '#2b88d8',
    lightest: '#c7e0f4',
  },
  secondary: {
    base: '#2b579a', // Deep blue
    darker: '#204072',
    darkest: '#162950',
    lighter: '#4c6ea9',
    lightest: '#dce1ef',
  },
  accent: {
    base: '#5c2d91', // Purple
    darker: '#4a2376',
    darkest: '#32175b',
    lighter: '#7c56a6',
    lightest: '#e5ddf5',
  },
  neutral: {
    black: '#000000',
    gray190: '#171717',
    gray180: '#252525',
    gray170: '#2e2e2e',
    gray160: '#3a3a3a',
    gray150: '#474747',
    gray140: '#565656',
    gray130: '#656565',
    gray120: '#767676',
    gray110: '#898989',
    gray100: '#9c9c9c',
    gray90: '#b1b1b1',
    gray80: '#c4c4c4',
    gray70: '#d7d7d7',
    gray60: '#e6e6e6',
    gray50: '#f0f0f0',
    gray40: '#f5f5f5',
    gray30: '#f8f8f8',
    gray20: '#fbfbfb',
    gray10: '#fefefe',
    white: '#ffffff',
  }
};

// Create themes
export const lightTheme = createLightTheme(brandColors.primary.base);
export const darkTheme = createDarkTheme(brandColors.primary.base);

// Common spacing values
export const spacing = {
  xxs: '2px',
  xs: '4px',
  s: '8px',
  m: '12px',
  l: '16px',
  xl: '20px',
  xxl: '24px',
  xxxl: '32px',
  xxxxl: '40px',
  xxxxxl: '48px',
  xxxxxxl: '64px',
};

// Common typography styles
export const typography = {
  fontFamily: "'Segoe UI', 'Segoe UI Web (West European)', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', sans-serif",
  fontSizes: {
    tiny: '10px',
    xSmall: '12px',
    small: '13px',
    medium: '14px',
    large: '16px',
    xLarge: '18px',
    xxLarge: '20px',
    xxxLarge: '24px',
    xxxxLarge: '28px',
    xxxxxLarge: '32px',
    xxxxxxLarge: '40px',
  },
  fontWeights: {
    regular: 400,
    semibold: 600,
    bold: 700,
  },
  lineHeights: {
    default: 1.5,
    heading: 1.25,
  },
};

// Responsive breakpoints
export const breakpoints = {
  xs: 0,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1400,
};

// Custom z-index values
export const zIndices = {
  base: 0,
  above: 1,
  dialog: 1000,
  dropdown: 1100,
  flyout: 1200,
  tooltip: 1300,
  modal: 1400,
  overlay: 9000,
};

// Shadow styles
export const shadows = {
  none: 'none',
  small: '0 2px 4px rgba(0, 0, 0, 0.1)',
  medium: '0 4px 8px rgba(0, 0, 0, 0.15)',
  large: '0 8px 16px rgba(0, 0, 0, 0.20)',
  xlarge: '0 16px 24px rgba(0, 0, 0, 0.25)',
};

// Border radiuses
export const borderRadius = {
  none: '0',
  xs: '2px',
  sm: '4px',
  md: '6px',
  lg: '8px',
  xl: '12px',
  pill: '999px',
  circle: '50%',
};
