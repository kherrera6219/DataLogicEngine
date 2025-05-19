import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ChakraProvider, extendTheme } from '@chakra-ui/react';

// Import layout components
import MainLayout from './components/layouts/MainLayout';

// Import pages
import HomePage from './pages/HomePage';
import ChatbotPage from './pages/ChatbotPage';
import ProjectPage from './pages/ProjectPage';
import AutoGPTPage from './pages/AutoGPTPage';
import CanvasPage from './pages/CanvasPage';
import VoicePage from './pages/VoicePage';
import MediaStudioPage from './pages/MediaStudioPage';
import SimulationMapPage from './pages/SimulationMapPage';
import LogsPage from './pages/LogsPage';
import SettingsPage from './pages/SettingsPage';

// Extend the Chakra UI theme for custom styles
const theme = extendTheme({
  initialColorMode: 'dark',
  useSystemColorMode: false,
  colors: {
    dark: {
      900: '#111418',
      800: '#1A1D23',
      700: '#22262F',
      600: '#2D3748',
    },
    brand: {
      900: '#1a365d',
      800: '#153e75',
      700: '#2a69ac',
      600: '#3182ce',
      500: '#4299e1',
      400: '#63b3ed',
    },
    accent: {
      500: '#ED8936',
      600: '#DD6B20',
    }
  },
  fonts: {
    heading: '"Inter", sans-serif',
    body: '"Inter", sans-serif',
  },
  styles: {
    global: {
      body: {
        bg: 'dark.900',
        color: 'white',
      },
    },
  },
  components: {
    Button: {
      baseStyle: {
        borderRadius: 'md',
      },
    },
    Card: {
      baseStyle: {
        container: {
          borderRadius: 'md',
        },
      },
    },
  },
});

function App() {
  return (
    <ChakraProvider theme={theme}>
      <Router>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<HomePage />} />
            <Route path="/chat" element={<ChatbotPage />} />
            <Route path="/project" element={<ProjectPage />} />
            <Route path="/auto-gpt" element={<AutoGPTPage />} />
            <Route path="/canvas" element={<CanvasPage />} />
            <Route path="/voice" element={<VoicePage />} />
            <Route path="/media-studio" element={<MediaStudioPage />} />
            <Route path="/simulation-map" element={<SimulationMapPage />} />
            <Route path="/logs" element={<LogsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </Router>
    </ChakraProvider>
  );
}

export default App;