
import React from 'react';

const Label = ({ 
  children, 
  htmlFor, 
  className = "", 
  required = false, 
  ...props 
}) => {
  return (
    <label 
      htmlFor={htmlFor} 
      className={`block text-sm font-medium text-gray-700 ${className}`} 
      {...props}
    >
      {children}
      {required && <span className="text-red-500 ml-1">*</span>}
    </label>
  );
};

export default Label;
