import React from 'react';
import { Badge as FluentBadge, makeStyles, mergeClasses } from '@fluentui/react-components';

const useStyles = makeStyles({
  badge: {},
});

const Badge = ({
  children,
  appearance = 'filled',
  color = 'brand',
  shape = 'rounded',
  size = 'medium',
  icon,
  className,
  ...props
}) => {
  const styles = useStyles();
  const iconElement = React.isValidElement(icon) ? icon : undefined;

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
