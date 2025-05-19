import React from 'react';
import { 
  Flex, 
  Box, 
  Text, 
  IconButton, 
  Badge, 
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Divider,
  useColorMode,
  HStack,
  Button,
  Icon,
  Tooltip
} from '@chakra-ui/react';
import { 
  FiBell, 
  FiSettings, 
  FiMoon, 
  FiSun,
  FiInfo,
  FiCpu
} from 'react-icons/fi';

function Topbar() {
  const { colorMode, toggleColorMode } = useColorMode();
  
  // Simulation Status indicator
  const simulationStatus = "active"; // Could be active, idle, error
  const confidenceScore = 0.96; // Example confidence score
  
  // Get appropriate colors for confidence score
  const getConfidenceColor = (score) => {
    if (score >= 0.9) return "green.500";
    if (score >= 0.75) return "yellow.500";
    return "red.500";
  };
  
  return (
    <Flex 
      h="60px" 
      px={4} 
      align="center" 
      justify="space-between"
      borderBottom="1px solid"
      borderColor="gray.700"
      bg="dark.900"
    >
      {/* Left Side - Page Title (dynamically set based on current route) */}
      <Text fontWeight="bold" fontSize="lg">Universal Knowledge Graph System</Text>
      
      {/* Right Side - Controls */}
      <HStack spacing={4}>
        {/* Simulation Status */}
        <Flex align="center">
          <Tooltip label="Simulation Engine Status">
            <HStack>
              <Box 
                w={3} 
                h={3} 
                borderRadius="full" 
                bg={simulationStatus === 'active' ? 'green.500' : 
                   simulationStatus === 'idle' ? 'yellow.500' : 'red.500'} 
              />
              <Text fontSize="sm" color="gray.400">Simulation</Text>
            </HStack>
          </Tooltip>
        </Flex>
        
        {/* Confidence Score */}
        <Tooltip label="Current Confidence Score">
          <Button 
            size="sm" 
            variant="ghost" 
            leftIcon={<Icon as={FiCpu} />}
            borderRadius="full"
          >
            <Text fontSize="sm">Confidence:</Text>
            <Badge ml={1} colorScheme={confidenceScore >= 0.9 ? "green" : confidenceScore >= 0.75 ? "yellow" : "red"}>
              {(confidenceScore * 100).toFixed(1)}%
            </Badge>
          </Button>
        </Tooltip>
        
        {/* Notifications */}
        <Menu>
          <Tooltip label="Notifications">
            <MenuButton
              as={IconButton}
              aria-label="Notifications"
              icon={<FiBell />}
              variant="ghost"
              size="md"
              position="relative"
            >
              <Box
                position="absolute"
                top="0"
                right="0"
                px={1}
                py={0.5}
                fontSize="xs"
                fontWeight="bold"
                lineHeight="none"
                color="white"
                transform="translate(25%, -25%)"
                bg="accent.500"
                rounded="full"
              >
                3
              </Box>
            </MenuButton>
          </Tooltip>
          <MenuList bg="dark.800" borderColor="gray.700">
            <MenuItem _hover={{ bg: 'dark.700' }}>New simulation completed</MenuItem>
            <MenuItem _hover={{ bg: 'dark.700' }}>System update available</MenuItem>
            <Divider />
            <MenuItem _hover={{ bg: 'dark.700' }}>View all notifications</MenuItem>
          </MenuList>
        </Menu>
        
        {/* Theme Toggle */}
        <Tooltip label={colorMode === 'dark' ? 'Light Mode' : 'Dark Mode'}>
          <IconButton
            aria-label="Toggle color mode"
            icon={colorMode === 'dark' ? <FiSun /> : <FiMoon />}
            onClick={toggleColorMode}
            variant="ghost"
            size="md"
          />
        </Tooltip>
        
        {/* Help */}
        <Tooltip label="Help & Documentation">
          <IconButton
            aria-label="Help"
            icon={<FiInfo />}
            variant="ghost"
            size="md"
          />
        </Tooltip>
      </HStack>
    </Flex>
  );
}

export default Topbar;