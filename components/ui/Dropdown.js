import React from 'react';
import { Dropdown as FluentDropdown, Option } from '@fluentui/react-components';

const Dropdown = ({
  id,
  name,
  value,
  onChange,
  options = [],
  placeholder = 'Select an option',
  multiselect = false,
  children,
  ...props
}) => {
  const selectedOptions = Array.isArray(value) ? value : value ? [value] : [];

  const handleChange = (event, data) => {
    if (onChange) {
      if (multiselect) {
        onChange(data.selectedOptions);
      } else {
        onChange(data.optionValue || data.optionText || '');
      }
    }
  };

  const dropdownProps = {
    id,
    'aria-label': placeholder,
    name,
    multiselect,
    selectedOptions,
    placeholder,
    onOptionSelect: handleChange,
    ...props,
  };

  if (children) {
    return <FluentDropdown {...dropdownProps}>{children}</FluentDropdown>;
  }

  return (
    <FluentDropdown {...dropdownProps}>
      {options.map((option) => (
        <Option key={option.value} value={option.value} text={option.label}>
          {option.label}
        </Option>
      ))}
    </FluentDropdown>
  );
};

Dropdown.Option = Option;

export default Dropdown;
