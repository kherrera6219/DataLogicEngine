import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  VStack, 
  Box, 
  Text, 
  Flex, 
  Divider, 
  Icon,
  Tooltip
} from '@chakra-ui/react';
import { 
  FiHome, 
  FiMessageSquare, 
  FiFolder, 
  FiCpu, 
  FiEdit3, 
  FiMic, 
  FiImage, 
  FiMap, 
  FiFileText, 
  FiSettings 
} from 'react-icons/fi';

// Navigation items mapping
const navItems = [
  { path: '/', label: 'Home', icon: FiHome },
  { path: '/chat', label: 'Chatbot', icon: FiMessageSquare },
  { path: '/project', label: 'Project Mode', icon: FiFolder },
  { path: '/auto-gpt', label: 'AutoGPT Mode', icon: FiCpu },
  { path: '/canvas', label: 'Canvas Mode', icon: FiEdit3 },
  { path: '/voice', label: 'Voice Mode', icon: FiMic },
  { path: '/media-studio', label: 'Media Studio', icon: FiImage },
  { path: '/simulation-map', label: 'Simulation Map', icon: FiMap },
  { path: '/logs', label: 'Logs', icon: FiFileText },
  { path: '/settings', label: 'Settings', icon: FiSettings }
];

function Sidebar() {
  const location = useLocation();
  
  return (
    <Box 
      w="240px" 
      h="100vh"
      bg="dark.900"
      color="white"
      py={4}
      display="flex"
      flexDirection="column"
      borderRight="1px solid"
      borderColor="gray.700"
      flexShrink={0}
    >
      {/* Logo & Title */}
      <Flex px={4} mb={6} alignItems="center">
        <Box 
          w={10} 
          h={10} 
          borderRadius="md" 
          bg="brand.500" 
          display="flex" 
          alignItems="center" 
          justifyContent="center" 
          fontWeight="bold"
          fontSize="lg"
        >
          UKG
        </Box>
        <Text ml={3} fontWeight="bold" fontSize="lg">
          Universal KG
        </Text>
      </Flex>
      
      <Divider mb={4} opacity={0.2} />
      
      {/* Navigation Links */}
      <VStack spacing={1} align="stretch" flex="1">
        {navItems.map((item) => (
          <Tooltip key={item.path} label={item.label} placement="right" hasArrow>
            <Box>
              <NavLink 
                to={item.path} 
                style={{ textDecoration: 'none' }}
              >
                {({ isActive }) => (
                  <Flex
                    align="center"
                    py={2}
                    px={4}
                    borderRadius="md"
                    bg={isActive || location.pathname === item.path ? 'brand.700' : 'transparent'}
                    color={isActive || location.pathname === item.path ? 'white' : 'gray.400'}
                    _hover={{ bg: 'brand.800', color: 'white' }}
                    transition="all 0.2s"
                  >
                    <Icon as={item.icon} boxSize={5} mr={3} />
                    <Text fontSize="sm">{item.label}</Text>
                  </Flex>
                )}
              </NavLink>
            </Box>
          </Tooltip>
        ))}
      </VStack>
      
      <Divider mt={4} opacity={0.2} />
      
      {/* Version Info */}
      <Box px={4} pt={4} fontSize="xs" color="gray.500">
        <Text>UKG System v1.0.0</Text>
        <Text>Powered by 13-Axis Simulation</Text>
      </Box>
    </Box>
  );
}

export default Sidebar;