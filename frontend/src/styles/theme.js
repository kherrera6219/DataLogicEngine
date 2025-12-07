import { extendTheme } from '@chakra-ui/react';

const theme = extendTheme({
  colors: {
    brand: {
      50: '#eff6fc',
      100: '#dceefb',
      200: '#c0e0f5',
      300: '#93c5ed',
      400: '#62a8e5',
      500: '#0f6cbd', // Microsoft blue (Fluent 2)
      600: '#0d5ba5',
      700: '#0b4a8c',
      800: '#093b75',
      900: '#072e5d',
    },
    neutral: {
      50: '#f8f9fa',
      100: '#f3f2f1',
      200: '#e6e6e6',
      300: '#d2d0ce',
      400: '#b3b0ad',
      500: '#979593',
      600: '#7a7574',
      700: '#605e5c',
      800: '#484644',
      900: '#323130',
    },
    success: {
      500: '#107c10',
    },
    warning: {
      500: '#f7630c',
    },
    error: {
      500: '#d13438',
    },
    info: {
      500: '#106ebe',
    },
    focus: '#0f6cbd',
  },
  fonts: {
    heading: '"Segoe UI Variable Display", "Segoe UI", system-ui, -apple-system, sans-serif',
    body: '"Segoe UI Variable Text", "Segoe UI", system-ui, -apple-system, sans-serif',
  },
  config: {
    initialColorMode: 'light',
    useSystemColorMode: true,
  },
  styles: {
    global: {
      body: {
        bg: 'neutral.100',
        color: 'neutral.900',
        lineHeight: '1.5',
      },
    },
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: 'semibold',
        borderRadius: 'md',
        _focusVisible: {
          boxShadow: '0 0 0 3px rgba(15, 108, 189, 0.35)',
        },
      },
      variants: {
        solid: {
          bg: 'brand.500',
          color: 'white',
          _hover: { bg: 'brand.600' },
          _active: { bg: 'brand.700' },
        },
        outline: {
          borderColor: 'brand.500',
          color: 'brand.600',
          _hover: { bg: 'brand.50' },
        },
        ghost: {
          color: 'brand.600',
          _hover: { bg: 'brand.50' },
        },
        subtle: {
          bg: 'neutral.50',
          color: 'neutral.900',
          _hover: { bg: 'neutral.100' },
        },
      },
    },
    Card: {
      baseStyle: {
        container: {
          bg: 'white',
          borderRadius: 'lg',
          borderWidth: '1px',
          borderColor: 'neutral.200',
          boxShadow: 'md',
        },
      },
    },
    Link: {
      baseStyle: {
        color: 'brand.600',
        fontWeight: 'semibold',
        _hover: {
          textDecoration: 'none',
          color: 'brand.500',
        },
        _focusVisible: {
          outline: '2px solid',
          outlineColor: 'focus',
          outlineOffset: '2px',
        },
      },
    },
  },
});

export default theme;