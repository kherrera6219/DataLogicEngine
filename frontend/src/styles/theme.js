import { extendTheme } from '@chakra-ui/react';

const theme = extendTheme({
  colors: {
    brand: {
      50: '#e1f5fe',
      100: '#b3e5fc',
      200: '#81d4fa',
      300: '#4fc3f7',
      400: '#29b6f6',
      500: '#03a9f4',
      600: '#039be5',
      700: '#0288d1',
      800: '#0277bd',
      900: '#01579b',
    },
    gray: {
      50: '#f9f9fb',
      100: '#eef1f6',
      200: '#e3e8f0',
      300: '#cfd9e7',
      400: '#bfc7d9',
      500: '#97a3b9',
      600: '#707a94',
      700: '#58606e',
      800: '#373b43',
      900: '#111418',
    },
    success: {
      500: '#38b2ac',
    },
    warning: {
      500: '#d69e2e',
    },
    error: {
      500: '#e53e3e',
    },
    info: {
      500: '#3182ce',
    },
  },
  fonts: {
    heading: '"Inter", sans-serif',
    body: '"Inter", sans-serif',
  },
  config: {
    initialColorMode: 'dark',
    useSystemColorMode: false,
  },
  styles: {
    global: (props) => ({
      body: {
        bg: 'gray.900',
        color: 'white',
      },
    }),
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: 'medium',
        borderRadius: 'md',
      },
      variants: {
        solid: {
          bg: 'brand.500',
          color: 'white',
          _hover: {
            bg: 'brand.600',
          },
        },
        outline: {
          borderColor: 'brand.500',
          color: 'brand.500',
        },
        ghost: {
          color: 'brand.500',
        },
      },
    },
    Card: {
      baseStyle: {
        container: {
          bg: 'gray.800',
          borderRadius: 'lg',
          overflow: 'hidden',
          boxShadow: 'md',
        },
      },
    },
    Link: {
      baseStyle: {
        color: 'brand.500',
        _hover: {
          textDecoration: 'none',
          color: 'brand.400',
        },
      },
    },
  },
});

export default theme;