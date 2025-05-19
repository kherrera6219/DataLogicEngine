
import React from 'react';

const Textarea = ({ 
  id, 
  name, 
  value, 
  onChange, 
  placeholder = "", 
  rows = 4,
  className = "", 
  ...props 
}) => {
  return (
    <textarea
      id={id}
      name={name}
      value={value}
      onChange={onChange}
      rows={rows}
      placeholder={placeholder}
      className={`w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 ${className}`}
      {...props}
    />
  );
};

export default Textarea;
