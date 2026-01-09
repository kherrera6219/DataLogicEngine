
# UKG System Style Guide

This style guide is based on Microsoft's Fluent UI design system and outlines the visual language and components used in the Universal Knowledge Graph (UKG) system.

## Design Principles

- **Accessible**: Ensure all components are accessible to users with disabilities
- **Responsive**: All interfaces should adapt to different screen sizes and devices
- **Consistent**: Maintain visual consistency throughout the application
- **Efficient**: Prioritize efficient workflows and minimal user actions

## Colors

The UKG system uses colors from the Fluent UI palette with a focus on:

### Brand Colors
- **Primary**: #0078d4 (Microsoft blue)
- **Secondary**: #2b579a (Deep blue)
- **Accent**: #5c2d91 (Purple)

### Neutral Colors
- **Dark**: #212529
- **Medium**: #495057
- **Light**: #f8f9fa
- **Border**: rgba(255, 255, 255, 0.1)

## Typography

All text in the UKG system uses the Segoe UI font family with the following sizes:

- **Tiny**: 10px
- **XSmall**: 12px
- **Small**: 13px
- **Medium**: 14px (default body text)
- **Large**: 16px
- **XLarge**: 18px
- **XXLarge**: 20px
- **XXXLarge**: 24px
- **XXXXLarge**: 28px

Font weights:
- **Regular**: 400
- **Semibold**: 600
- **Bold**: 700

## Spacing

The UKG system uses a consistent spacing system:

- **XXS**: 2px
- **XS**: 4px
- **S**: 8px
- **M**: 12px
- **L**: 16px
- **XL**: 20px
- **XXL**: 24px
- **XXXL**: 32px
- **XXXXL**: 40px
- **XXXXXL**: 48px
- **XXXXXXL**: 64px

## Component Guidelines

### Buttons

- Use primary buttons for main actions
- Use secondary/outline buttons for secondary actions
- Always include hover and focus states
- Use consistent padding and sizing

### Cards

- Use cards to group related content
- Maintain consistent padding within cards
- Use card headers for titles
- Consider using card footers for actions

### Navigation

- Use the Navbar component for main navigation
- Use the Sidebar component for contextual navigation
- Ensure active states are clearly visible
- Consider mobile navigation patterns

### Forms

- Group related form fields
- Provide clear labels and help text
- Show validation messages inline
- Use consistent input sizing

### Modals and Dialogs

- Use for focused user interactions
- Provide clear titles and actions
- Allow dismissal via close button, escape key, and backdrop click
- Ensure proper focus management

## Responsive Breakpoints

- **XS**: 0px (default)
- **SM**: 576px
- **MD**: 768px
- **LG**: 992px
- **XL**: 1200px
- **XXL**: 1400px

## Accessibility Guidelines

- Maintain WCAG 2.1 AA compliance
- Ensure proper color contrast (minimum 4.5:1 for text)
- Support keyboard navigation
- Include screen reader-friendly content
- Test with assistive technologies
