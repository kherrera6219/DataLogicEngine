import React, { useState } from 'react';
import { Box, Flex, useDisclosure } from '@chakra-ui/react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../navigation/Sidebar';
import Topbar from '../navigation/Topbar';

const MainLayout = () => {
  const { isOpen, onOpen, onClose } = useDisclosure({ defaultIsOpen: true });
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const toggleSidebar = () => {
    if (window.innerWidth < 768) {
      setIsMobileOpen(!isMobileOpen);
    } else {
      if (isOpen) {
        onClose();
      } else {
        onOpen();
      }
    }
  };

  return (
    <Flex h="100vh" flexDirection="column">
      <Topbar 
        isOpen={isOpen} 
        toggleSidebar={toggleSidebar} 
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />
      
      <Flex flex="1" overflow="hidden">
        <Sidebar 
          isOpen={isOpen} 
          isMobileOpen={isMobileOpen} 
          onClose={() => setIsMobileOpen(false)}
        />
        
        <Box
          flex="1"
          p={4}
          ml={{ base: 0, md: isOpen ? '250px' : '80px' }}
          transition="margin-left 0.3s"
          bg="gray.900"
          overflowY="auto"
          position="relative"
        >
          <Outlet />
        </Box>
      </Flex>
    </Flex>
  );
};

export default MainLayout;