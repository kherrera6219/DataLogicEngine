import React from 'react';
import { Label as FluentLabel } from '@fluentui/react-components';

const Label = React.forwardRef(function EnterpriseLabel(
  { children, required = false, size = 'medium', className, ...props },
  ref
) {
  return (
    <FluentLabel ref={ref} required={required} size={size} className={className} {...props}>
      {children}
    </FluentLabel>
  );
});

export default Label;
