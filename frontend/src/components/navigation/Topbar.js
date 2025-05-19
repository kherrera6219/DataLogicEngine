import React from 'react';
import {
  Box,
  Flex,
  Heading,
  IconButton,
  useColorModeValue,
  HStack,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Avatar,
  Text,
  Badge,
  Tooltip,
  Button
} from '@chakra-ui/react';
import { 
  FiMenu, 
  FiBell, 
  FiUser, 
  FiLogOut, 
  FiSettings,
  FiChevronDown,
  FiSearch
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

const Topbar = ({ isOpen, toggleSidebar, isMobileOpen, setIsMobileOpen }) => {
  const navigate = useNavigate();
  
  // Placeholder user data - would come from context in real app
  const user = {
    name: 'Admin User',
    email: 'admin@example.com',
    avatar: null, // Default avatar will be shown
    role: 'Administrator'
  };

  const handleLogout = () => {
    // Would use auth context to logout in real app
    navigate('/logout');
  };

  return (
    <Box
      as="header"
      bg="gray.800"
      px={4}
      height="64px"
      boxShadow="0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)"
      position="relative"
      zIndex="sticky"
    >
      <Flex h="full" alignItems="center" justifyContent="space-between">
        <Flex alignItems="center">
          <IconButton
            display={{ base: 'flex', md: 'flex' }}
            onClick={toggleSidebar}
            variant="ghost"
            aria-label="Toggle Sidebar"
            icon={<FiMenu />}
            size="lg"
            color="gray.400"
            _hover={{ color: 'white', bg: 'gray.700' }}
          />
          
          <Heading
            ml={2}
            fontSize="xl"
            fontWeight="bold"
            color="white"
            display={{ base: 'none', md: 'flex' }}
          >
            Universal Knowledge Graph
          </Heading>
          
          <Heading
            ml={2}
            fontSize="xl"
            fontWeight="bold"
            color="white"
            display={{ base: 'flex', md: 'none' }}
          >
            UKG
          </Heading>
        </Flex>

        {/* Search bar - desktop */}
        <Box display={{ base: 'none', md: 'block' }} flex="1" maxW="600px" mx={4}>
          <Flex 
            as="form" 
            bg="gray.700" 
            borderRadius="full" 
            px={4} 
            alignItems="center"
          >
            <IconButton
              variant="ghost"
              aria-label="Search"
              icon={<FiSearch />}
              color="gray.400"
              size="sm"
              _hover={{ color: 'white' }}
            />
            <Box 
              as="input" 
              bg="transparent" 
              border="none" 
              color="white" 
              placeholder="Search knowledge graph..." 
              w="full" 
              py={2} 
              px={2}
              _placeholder={{ color: 'gray.400' }}
              outline="none"
            />
          </Flex>
        </Box>
        
        <HStack spacing={3}>
          {/* Search button - mobile */}
          <IconButton
            display={{ base: 'flex', md: 'none' }}
            variant="ghost"
            aria-label="Search"
            icon={<FiSearch />}
            color="gray.400"
            _hover={{ color: 'white', bg: 'gray.700' }}
          />
          
          {/* Notifications */}
          <Tooltip label="Notifications" placement="bottom" hasArrow>
            <IconButton
              variant="ghost"
              aria-label="Notifications"
              icon={
                <>
                  <FiBell />
                  <Badge 
                    colorScheme="red" 
                    position="absolute" 
                    top="0" 
                    right="0" 
                    borderRadius="full" 
                    w="14px" 
                    h="14px"
                  >
                    3
                  </Badge>
                </>
              }
              color="gray.400"
              _hover={{ color: 'white', bg: 'gray.700' }}
            />
          </Tooltip>
          
          {/* User menu */}
          <Menu>
            <MenuButton
              as={Button}
              variant="ghost"
              rightIcon={<FiChevronDown />}
              _hover={{ bg: 'gray.700' }}
              _active={{ bg: 'gray.700' }}
            >
              <HStack spacing={2}>
                <Avatar 
                  size="sm" 
                  name={user.name} 
                  src={user.avatar}
                  bg="brand.500"
                />
                <Box display={{ base: 'none', md: 'block' }} textAlign="left">
                  <Text fontSize="sm" fontWeight="medium">{user.name}</Text>
                  <Text fontSize="xs" color="gray.400">{user.role}</Text>
                </Box>
              </HStack>
            </MenuButton>
            <MenuList bg="gray.800" borderColor="gray.700">
              <MenuItem 
                icon={<FiUser />} 
                onClick={() => navigate('/profile')}
                _hover={{ bg: 'gray.700' }}
              >
                Profile
              </MenuItem>
              <MenuItem 
                icon={<FiSettings />} 
                onClick={() => navigate('/settings')}
                _hover={{ bg: 'gray.700' }}
              >
                Settings
              </MenuItem>
              <MenuItem 
                icon={<FiLogOut />} 
                onClick={handleLogout}
                _hover={{ bg: 'gray.700' }}
              >
                Logout
              </MenuItem>
            </MenuList>
          </Menu>
        </HStack>
      </Flex>
    </Box>
  );
};

export default Topbar;