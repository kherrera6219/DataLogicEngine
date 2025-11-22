import React from 'react'

export const makeStyles = () => () => ({})
export const shorthands = {
  padding: (...args) => ({}),
  margin: (...args) => ({}),
  borderRadius: (...args) => ({}),
  border: (...args) => ({}),
  gap: (...args) => ({}),
}
export const Text = ({ children, ...props }) => React.createElement('span', props, children)
export const mergeClasses = (...classes) => classes.filter(Boolean).join(' ')
export const Button = ({ children, ...props }) => React.createElement('button', props, children)
export const Input = (props) => React.createElement('input', props)
export const Label = ({ children, ...props }) => React.createElement('label', props, children)
