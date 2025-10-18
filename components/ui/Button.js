import React from 'react';
import { Button as FluentButton } from '@fluentui/react-components';

const appearanceMap = {
  primary: 'primary',
  secondary: 'secondary',
  outline: 'outline',
  subtle: 'subtle',
  transparent: 'transparent',
};

const sizeMap = {
  sm: 'small',
  md: 'medium',
  lg: 'large',
};

const Button = React.forwardRef(function EnterpriseButton(
  {
    children,
    variant = 'primary',
    size = 'md',
    icon,
    iconPosition = 'before',
    href,
    as,
    ...props
  },
  ref
) {
  const appearance = appearanceMap[variant] || 'primary';
  const resolvedSize = sizeMap[size] || 'medium';
  const component = as || (href ? 'a' : undefined);

  return (
    <FluentButton
      ref={ref}
      appearance={appearance}
      size={resolvedSize}
      icon={icon}
      iconPosition={iconPosition}
      href={href}
      as={component}
      {...props}
    >
      {children}
    </FluentButton>
  );
});

export default Button;
