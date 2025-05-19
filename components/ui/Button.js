
import React from 'react';
import { Button as FluentButton } from '@fluentui/react-components';

const Button = ({ 
  children, 
  appearance = 'primary',
  size = 'medium', 
  iconPosition = 'before', 
  icon,
  disabled = false,
  ...props 
}) => {
  return (
    <FluentButton
      appearance={appearance}
      size={size}
      icon={icon}
      iconPosition={iconPosition}
      disabled={disabled}
      {...props}
    >
      {children}
    </FluentButton>
  );
};

export default Button;
