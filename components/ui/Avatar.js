import React from 'react';
import { Avatar as FluentAvatar, makeStyles, mergeClasses } from '@fluentui/react-components';

const useStyles = makeStyles({
  avatar: {
    flexShrink: 0,
  },
});

const Avatar = ({
  size = 40,
  name,
  image,
  icon,
  initials,
  color = 'neutral',
  badge,
  shape = 'circular',
  className,
  ...props
}) => {
  const styles = useStyles();

  const iconElement = React.isValidElement(icon) ? icon : undefined;

  return (
    <FluentAvatar
      name={name}
      image={image ? { src: image } : undefined}
      icon={iconElement}
      initials={initials}
      size={size}
      color={color}
      shape={shape}
      badge={badge}
      className={mergeClasses(styles.avatar, className)}
      {...props}
    />
  );
};

export default Avatar;
