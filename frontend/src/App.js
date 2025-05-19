import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@chakra-ui/react';

// Layouts
import MainLayout from './components/layouts/MainLayout';

// Pages
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

function App() {
  return (
    <Box minH="100vh" bg="dark.800" color="white">
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<HomePage />} />
          <Route path="chat" element={<ChatbotPage />} />
          <Route path="project" element={<ProjectPage />} />
          <Route path="auto-gpt" element={<AutoGPTPage />} />
          <Route path="canvas" element={<CanvasPage />} />
          <Route path="voice" element={<VoicePage />} />
          <Route path="media-studio" element={<MediaStudioPage />} />
          <Route path="simulation-map" element={<SimulationMapPage />} />
          <Route path="logs" element={<LogsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </Box>
  );
}

export default App;