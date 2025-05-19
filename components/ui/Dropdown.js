
import React from 'react';

const Dropdown = ({ 
  id, 
  name, 
  value, 
  onChange, 
  options = [], 
  placeholder = "Select an option", 
  className = "",
  title,
  children,
  ...props 
}) => {
  // If children are provided, render a dropdown menu component
  if (children) {
    return (
      <div className="dropdown">
        <button 
          className={`btn dropdown-toggle ${className}`} 
          type="button" 
          id={id} 
          data-bs-toggle="dropdown" 
          aria-expanded="false"
        >
          {title || "Dropdown"}
        </button>
        <ul className="dropdown-menu" aria-labelledby={id}>
          {children}
        </ul>
      </div>
    );
  }
  
  // Otherwise render a select component
  return (
    <select
      id={id}
      name={name}
      value={value}
      onChange={onChange}
      className={`form-select ${className}`}
      {...props}
    >
      <option value="" disabled>{placeholder}</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
};

// Add Item subcomponent for dropdown menus
Dropdown.Item = ({ children, onClick, className = "" }) => {
  return (
    <li>
      <button 
        className={`dropdown-item ${className}`} 
        type="button" 
        onClick={onClick}
      >
        {children}
      </button>
    </li>
  );
};

export default Dropdown;
