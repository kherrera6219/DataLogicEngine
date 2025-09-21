import React from 'react';
import { Textarea as FluentTextarea } from '@fluentui/react-components';

const Textarea = React.forwardRef(function EnterpriseTextarea(
  { id, name, value, onChange, placeholder = '', resize = 'vertical', size = 'medium', ...props },
  ref
) {
  return (
    <FluentTextarea
      ref={ref}
      id={id}
      name={name}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      resize={resize}
      size={size}
      {...props}
    />
  );
});

export default Textarea;
