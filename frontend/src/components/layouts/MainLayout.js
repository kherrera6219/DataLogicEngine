import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box, Flex } from '@chakra-ui/react';
import Sidebar from '../navigation/Sidebar';
import Topbar from '../navigation/Topbar';

function MainLayout() {
  return (
    <Flex h="100vh" overflow="hidden">
      {/* Sidebar Navigation */}
      <Sidebar />
      
      {/* Main Content Area */}
      <Box flex="1" display="flex" flexDirection="column" overflow="hidden">
        {/* Top Navigation Bar */}
        <Topbar />
        
        {/* Main Content with Outlet for Routes */}
        <Box 
          flex="1" 
          p={4} 
          overflowY="auto"
          bg="dark.800"
          borderRadius="md"
          m={2}
        >
          <Outlet />
        </Box>
      </Box>
    </Flex>
  );
}

export default MainLayout;