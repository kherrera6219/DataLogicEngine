import React from 'react';
import { Box, Flex, Image, Text, useColorModeValue } from '@chakra-ui/react';
import { Outlet } from 'react-router-dom';

const AuthLayout = () => {
  return (
    <Flex minH="100vh" direction={{ base: 'column', md: 'row' }}>
      {/* Left side branding/hero section */}
      <Box
        flex={{ base: '0', md: '1' }}
        bg="gray.800"
        color="white"
        py={{ base: 8, md: 0 }}
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        position="relative"
        bgGradient="linear(to-b, gray.800, gray.900)"
      >
        <Box maxW="440px" px={8} py={12} textAlign="center">
          <Text
            fontSize="4xl"
            fontWeight="bold"
            mb={6}
            bgGradient="linear(to-r, brand.400, brand.600)"
            bgClip="text"
          >
            Universal Knowledge Graph
          </Text>
          
          <Text fontSize="lg" mb={8} color="gray.300">
            Advanced multi-perspective knowledge synthesis and expert simulation
            across multiple cognitive layers.
          </Text>
          
          <Box 
            borderRadius="lg" 
            overflow="hidden" 
            boxShadow="xl"
            mb={6}
            maxW="360px"
            mx="auto"
          >
            {/* Placeholder for a hero image or animation */}
            <Box 
              h="240px" 
              bg="gray.700" 
              display="flex" 
              alignItems="center" 
              justifyContent="center"
            >
              <Text color="gray.500" fontWeight="bold">Knowledge Graph Visualization</Text>
            </Box>
          </Box>
          
          <Text fontSize="sm" color="gray.500">
            © {new Date().getFullYear()} Universal Knowledge Graph System
            <br />
            Enterprise Edition v1.0.0
          </Text>
        </Box>
      </Box>
      
      {/* Right side content area */}
      <Box
        flex={{ base: '1', md: '1' }}
        bg="gray.900"
        display="flex"
        alignItems="center"
        justifyContent="center"
        p={{ base: 4, md: 8 }}
        minH={{ base: 'auto', md: '100vh' }}
      >
        <Box 
          w="full" 
          maxW="440px" 
          mx="auto"
        >
          <Outlet />
        </Box>
      </Box>
    </Flex>
  );
};

export default AuthLayout;