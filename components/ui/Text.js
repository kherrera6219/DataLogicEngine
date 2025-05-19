
import React from 'react';

const Text = ({ 
  children, 
  fontSize = "md", 
  fontWeight = "normal", 
  color = "default",
  className = "", 
  as = "p",
  ...props 
}) => {
  const sizeClasses = {
    xs: "text-xs",
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg",
    xl: "text-xl",
    "2xl": "text-2xl",
    "3xl": "text-3xl"
  };
  
  const weightClasses = {
    light: "font-light",
    normal: "font-normal",
    medium: "font-medium",
    semibold: "font-semibold",
    bold: "font-bold"
  };
  
  const colorClasses = {
    default: "text-gray-800",
    muted: "text-gray-600",
    light: "text-gray-400",
    primary: "text-blue-600",
    success: "text-green-600",
    warning: "text-yellow-600",
    danger: "text-red-600"
  };
  
  const sizeClass = sizeClasses[fontSize] || sizeClasses.md;
  const weightClass = weightClasses[fontWeight] || weightClasses.normal;
  const colorClass = colorClasses[color] || colorClasses.default;
  
  const Component = as;
  
  return (
    <Component 
      className={`${sizeClass} ${weightClass} ${colorClass} ${className}`} 
      {...props}
    >
      {children}
    </Component>
  );
};

export default Text;
