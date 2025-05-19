import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router } from 'react-router-dom';
import { ChakraProvider, extendTheme } from '@chakra-ui/react';
import App from './App';
import './styles/main.css';

// Custom theme with UKG colors and styling
const theme = extendTheme({
  colors: {
    brand: {
      900: '#1a365d', // deep navy
      800: '#2a4365',
      700: '#2c5282',
      600: '#2b6cb0',
      500: '#3182ce', // primary blue
      400: '#4299e1', 
      300: '#63b3ed',
      200: '#90cdf4',
      100: '#bee3f8',
      50: '#ebf8ff',
    },
    accent: {
      500: '#805AD5', // purple
      400: '#00B5D8', // cyan
      300: '#DD6B20', // orange
      200: '#38A169', // green
    },
    dark: {
      900: '#171923',
      800: '#1A202C',
      700: '#2D3748',
      600: '#4A5568',
    },
  },
  fonts: {
    body: 'Inter, system-ui, sans-serif',
    heading: 'Inter, system-ui, sans-serif',
  },
  config: {
    initialColorMode: 'dark',
    useSystemColorMode: true,
  },
});

const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <ChakraProvider theme={theme}>
      <Router>
        <App />
      </Router>
    </ChakraProvider>
  </React.StrictMode>
);