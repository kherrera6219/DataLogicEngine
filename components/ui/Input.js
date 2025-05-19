
import React from 'react';
import { Input as FluentInput } from '@fluentui/react-components';

const Input = ({
  type = 'text',
  appearance = 'outline',
  size = 'medium',
  placeholder,
  value,
  onChange,
  disabled = false,
  ...props
}) => {
  return (
    <FluentInput
      type={type}
      appearance={appearance}
      size={size}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      disabled={disabled}
      {...props}
    />
  );
};

export default Input;
