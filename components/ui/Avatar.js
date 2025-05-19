
import React from 'react';
import { 
  Avatar as FluentAvatar,
  makeStyles,
  mergeClasses
} from '@fluentui/react-components';

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
  color = 'neutral', // 'brand', 'neutral', 'danger', etc.
  badge,
  shape = 'circular',
  className,
  ...props 
}) => {
  const styles = useStyles();
  
  let iconElement = null;
  if (icon) {
    iconElement = <i className={`bi bi-${icon}`}></i>;
  }
  
  return (
    <FluentAvatar
      name={name}
      image={{ src: image }}
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
