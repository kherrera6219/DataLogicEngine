import React from 'react';
import { Text as FluentText } from '@fluentui/react-components';

const sizeMap = {
  xs: 100,
  sm: 200,
  md: 300,
  lg: 400,
  xl: 500,
  '2xl': 600,
  '3xl': 700,
};

const weightMap = {
  light: 'regular',
  normal: 'regular',
  medium: 'medium',
  semibold: 'semibold',
  bold: 'bold',
};

const colorMap = {
  default: undefined,
  muted: 'var(--colorNeutralForeground3)',
  success: 'var(--colorPaletteGreenForeground2)',
  warning: 'var(--colorPaletteGoldForeground2)',
  danger: 'var(--colorPaletteRedForeground2)',
  info: 'var(--colorPaletteBlueForeground2)',
};

const Text = ({
  children,
  fontSize = 'md',
  fontWeight = 'normal',
  color = 'default',
  as,
  truncate = false,
  style,
  ...props
}) => {
  const size = sizeMap[fontSize] || sizeMap.md;
  const weight = weightMap[fontWeight] || 'regular';
  const resolvedColor = colorMap[color] || undefined;

  return (
    <FluentText
      as={as}
      size={size}
      weight={weight}
      truncate={truncate}
      style={{ color: resolvedColor, ...style }}
      {...props}
    >
      {children}
    </FluentText>
  );
};

export default Text;
