import React from 'react';
import { 
  Box, 
  Flex, 
  VStack, 
  Icon, 
  Text, 
  Divider,
  useColorModeValue,
  Drawer,
  DrawerOverlay,
  DrawerContent,
  DrawerBody,
  DrawerCloseButton
} from '@chakra-ui/react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  FiHome, 
  FiMessageSquare, 
  FiBriefcase, 
  FiCpu, 
  FiEdit3, 
  FiMic, 
  FiFilm,
  FiMap,
  FiList,
  FiSettings
} from 'react-icons/fi';

// Navigation items configuration
const navItems = [
  { name: 'Home', icon: FiHome, path: '/' },
  { name: 'Chatbot', icon: FiMessageSquare, path: '/chat' },
  { name: 'Project', icon: FiBriefcase, path: '/project' },
  { name: 'AutoGPT', icon: FiCpu, path: '/autogpt' },
  { name: 'Canvas', icon: FiEdit3, path: '/canvas' },
  { name: 'Voice', icon: FiMic, path: '/voice' },
  { name: 'Media Studio', icon: FiFilm, path: '/media-studio' },
  { name: 'Simulation Map', icon: FiMap, path: '/simulation-map' },
  { name: 'Logs', icon: FiList, path: '/logs' },
  { name: 'Settings', icon: FiSettings, path: '/settings' },
];

// NavItem component
const NavItem = ({ icon, children, path, isActive, isOpen }) => {
  return (
    <Box
      as={NavLink}
      to={path}
      display="flex"
      alignItems="center"
      py={3}
      px={4}
      mx={2}
      borderRadius="md"
      role="group"
      cursor="pointer"
      _hover={{
        bg: 'gray.700',
        color: 'white',
      }}
      bg={isActive ? 'gray.700' : 'transparent'}
      color={isActive ? 'white' : 'gray.400'}
      fontWeight={isActive ? 'bold' : 'normal'}
      transition="all 0.3s"
    >
      <Icon
        as={icon}
        fontSize="xl"
        color={isActive ? 'brand.400' : 'gray.400'}
        _groupHover={{
          color: 'brand.400',
        }}
      />
      {isOpen && (
        <Text ml={4} display={{ base: 'block', md: 'block' }}>
          {children}
        </Text>
      )}
    </Box>
  );
};

// Main Sidebar component
const Sidebar = ({ isOpen, isMobileOpen, onClose }) => {
  const location = useLocation();
  
  // Sidebar content
  const SidebarContent = () => (
    <Box
      bg="gray.800"
      color="white"
      height="full"
      w={isOpen ? '250px' : '80px'}
      transition="width 0.3s ease"
      overflowY="auto"
      boxShadow="0 4px 12px 0 rgba(0, 0, 0, 0.5)"
    >
      {/* Logo */}
      <Flex
        h="20"
        alignItems="center"
        justifyContent={isOpen ? "flex-start" : "center"}
        px={6}
      >
        <Text 
          fontSize="xl" 
          fontWeight="bold" 
          color="brand.400"
          ml={isOpen ? 2 : 0}
        >
          {isOpen ? "UKG System" : "UKG"}
        </Text>
      </Flex>
      
      <Divider borderColor="gray.600" />
      
      {/* Navigation Links */}
      <VStack align="stretch" spacing={1} mt={4}>
        {navItems.map((item) => (
          <NavItem 
            key={item.name} 
            icon={item.icon} 
            path={item.path} 
            isActive={location.pathname === item.path}
            isOpen={isOpen}
          >
            {item.name}
          </NavItem>
        ))}
      </VStack>
      
      <Divider my={6} borderColor="gray.600" />
      
      {/* System Info */}
      {isOpen && (
        <Box px={4} fontSize="xs" color="gray.500" mb={4}>
          <Text>Universal Knowledge Graph</Text>
          <Text>Version 1.0.0</Text>
        </Box>
      )}
    </Box>
  );

  // For mobile view: use a drawer
  if (isMobileOpen) {
    return (
      <Drawer
        isOpen={isMobileOpen}
        placement="left"
        onClose={onClose}
        returnFocusOnClose={false}
        size="xs"
      >
        <DrawerOverlay />
        <DrawerContent bg="gray.800">
          <DrawerCloseButton color="white" />
          <DrawerBody p={0}>
            <SidebarContent />
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    );
  }

  // For desktop view: use fixed sidebar
  return (
    <Box
      position="fixed"
      left={0}
      height="full"
      top="64px"
      display={{ base: 'none', md: 'block' }}
      zIndex="sticky"
    >
      <SidebarContent />
    </Box>
  );
};

export default Sidebar;