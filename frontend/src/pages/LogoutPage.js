import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Spinner, Text, VStack } from '@chakra-ui/react';

export default function LogoutPage() {
  const navigate = useNavigate();

  useEffect(() => {
    // Perform logout
    localStorage.removeItem('authToken');
    sessionStorage.clear();

    // Redirect to home after 1 second
    setTimeout(() => {
      navigate('/');
    }, 1000);
  }, [navigate]);

  return (
    <Box
      height="100vh"
      display="flex"
      alignItems="center"
      justifyContent="center"
    >
      <VStack spacing={4}>
        <Spinner size="xl" color="blue.500" />
        <Text fontSize="xl">Logging out...</Text>
      </VStack>
    </Box>
  );
}
