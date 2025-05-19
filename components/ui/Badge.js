
import React from 'react';
import { 
  Badge as FluentBadge,
  makeStyles,
  mergeClasses
} from '@fluentui/react-components';

const useStyles = makeStyles({
  badge: {
    // Custom styling if needed
  },
});

const Badge = ({ 
  children,
  appearance = 'filled',
  color = 'brand', // 'brand', 'danger', 'important', 'informative', 'severe', 'subtle', 'success', 'warning'
  shape = 'rounded',
  size = 'medium',
  icon,
  className,
  ...props 
}) => {
  const styles = useStyles();
  
  let iconElement = null;
  if (icon) {
    iconElement = <i className={`bi bi-${icon}`}></i>;
  }
  
  return (
    <FluentBadge
      appearance={appearance}
      color={color}
      shape={shape}
      size={size}
      icon={iconElement}
      className={mergeClasses(styles.badge, className)}
      {...props}
    >
      {children}
    </FluentBadge>
  );
};

export default Badge;
