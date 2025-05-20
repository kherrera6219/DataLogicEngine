import React, { useState, useEffect } from 'react';
import { ChakraProvider, Box } from '@chakra-ui/react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Theme
import theme from './styles/theme';

// Layout Components
import MainLayout from './components/layouts/MainLayout';
import AuthLayout from './components/layouts/AuthLayout';

// Authentication Components
import LoginPage from './pages/LoginPage';
import LogoutPage from './pages/LogoutPage';

// Main Application Pages
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
import NotificationsPage from './pages/NotificationsPage';
import CompareSimulationsPage from './pages/CompareSimulationsPage';
import CoverageMapPage from './pages/CoverageMapPage';
import AGIDashboardPage from './pages/AGIDashboardPage';
import AgentBuilderPage from './pages/AgentBuilderPage';
import AuthoringAndEvaluationPage from './pages/AuthoringAndEvaluationPage';
import SimulationDashboardPage from './pages/SimulationDashboardPage';
import AdminIntegrationsPage from './pages/AdminIntegrationsPage';
import MCPConsolePage from './pages/MCPConsolePage';
import ProfilePage from './pages/ProfilePage';

// Contexts
import { AuthProvider } from './contexts/AuthContext';
import { UKGProvider } from './contexts/UKGContext';
import { NotificationProvider } from './contexts/NotificationContext';

// Utils
import { getToken, isValidToken } from './utils/auth';

const App = () => {
  const [initialized, setInitialized] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check if user is authenticated on initial load
    const token = getToken();
    const tokenIsValid = isValidToken(token);
    setIsAuthenticated(tokenIsValid);
    setInitialized(true);
  }, []);

  // Protected route wrapper component
  const ProtectedRoute = ({ children }) => {
    if (!initialized) {
      // Show loading state while checking authentication
      return <Box p={8}>Loading...</Box>;
    }

    if (!isAuthenticated) {
      // Redirect to login if not authenticated
      return <Navigate to="/login" replace />;
    }

    return children;
  };

  return (
    <ChakraProvider theme={theme}>
      <AuthProvider setIsAuthenticated={setIsAuthenticated}>
        <UKGProvider>
          <NotificationProvider>
            <Router>
              <Routes>
                {/* Authentication Routes */}
                <Route element={<AuthLayout />}>
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/logout" element={<LogoutPage />} />
                </Route>

                {/* Main Application Routes */}
                <Route
                  element={
                    <ProtectedRoute>
                      <MainLayout />
                    </ProtectedRoute>
                  }
                >
                  <Route path="/" element={<HomePage />} />
                  <Route path="/chat" element={<ChatbotPage />} />
                  <Route path="/project" element={<ProjectPage />} />
                  <Route path="/autogpt" element={<AutoGPTPage />} />
                  <Route path="/canvas" element={<CanvasPage />} />
                  <Route path="/voice" element={<VoicePage />} />
                  <Route path="/media-studio" element={<MediaStudioPage />} />
                  <Route path="/simulation-map" element={<SimulationMapPage />} />
                  <Route path="/logs" element={<LogsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="/notifications" element={<NotificationsPage />} />
                  <Route path="/compare" element={<CompareSimulationsPage />} />
                  <Route path="/coverage-map" element={<CoverageMapPage />} />
                  <Route path="/agi-dashboard" element={<AGIDashboardPage />} />
                  <Route path="/agents/builder" element={<AgentBuilderPage />} />
                  <Route path="/authoring-and-evaluation" element={<AuthoringAndEvaluationPage />} />
                  <Route path="/simulation-dashboard" element={<SimulationDashboardPage />} />
                  <Route path="/admin/integrations" element={<AdminIntegrationsPage />} />
                  <Route path="/mcp-console" element={<MCPConsolePage />} />
                  <Route path="/profile" element={<ProfilePage />} />
                </Route>

                {/* Fallback Route */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Router>
          </NotificationProvider>
        </UKGProvider>
      </AuthProvider>
    </ChakraProvider>
  );
};

export default App;