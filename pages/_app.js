
import 'bootstrap-icons/font/bootstrap-icons.css';
import '../styles/globals.css';
import '../styles/chat.css';
import { useEffect, useState } from 'react';
import { 
  FluentProvider, 
  teamsLightTheme, 
  teamsDarkTheme,
  createDarkTheme
} from '@fluentui/react-components';
import { darkTheme } from '../styles/theme';

function MyApp({ Component, pageProps }) {
  const [isDarkMode, setIsDarkMode] = useState(true);
  
  // Load Bootstrap JS on client side only
  useEffect(() => {
    import('bootstrap/dist/js/bootstrap.bundle.min.js');
  }, []);

  // Detect user's preferred color scheme
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setIsDarkMode(prefersDark);
      
      // Listen for changes in color scheme preference
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = (e) => setIsDarkMode(e.matches);
      mediaQuery.addEventListener('change', handleChange);
      
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, []);
  
  // Toggle dark mode
  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  return (
    <FluentProvider theme={isDarkMode ? darkTheme : teamsLightTheme}>
      <Component {...pageProps} isDarkMode={isDarkMode} toggleDarkMode={toggleDarkMode} />
    </FluentProvider>
  );
}

export default MyApp;
