
import React from 'react';

const Card = ({
  children,
  className = "",
  title = "",
  footer = null,
  shadow = "md",
  border = false,
  ...props
}) => {
  const shadowClasses = {
    none: "",
    sm: "shadow-sm",
    md: "shadow",
    lg: "shadow-lg",
    xl: "shadow-xl"
  };
  
  const shadowClass = shadowClasses[shadow] || shadowClasses.md;
  
  return (
    <div 
      className={`bg-white rounded-lg overflow-hidden ${shadowClass} ${border ? 'border border-gray-200' : ''} ${className}`}
      {...props}
    >
      {title && (
        <div className="px-4 py-3 border-b border-gray-200">
          <h3 className="font-medium text-gray-900">{title}</h3>
        </div>
      )}
      <div className="p-4">
        {children}
      </div>
      {footer && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;
