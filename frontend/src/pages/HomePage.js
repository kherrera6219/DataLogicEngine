import React from 'react';
import {
  Box,
  Flex,
  VStack,
  HStack,
  Text,
  Heading,
  Button,
  Grid,
  GridItem,
  Card,
  CardBody,
  Image,
  Badge,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Icon,
  Divider,
  useColorModeValue
} from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import {
  FiMessageSquare,
  FiFolder,
  FiCpu,
  FiEdit3,
  FiMic,
  FiImage,
  FiMap,
  FiPieChart,
  FiActivity,
  FiLayers,
  FiInfo,
  FiArrowRight
} from 'react-icons/fi';

const HomePage = () => {
  return (
    <Box>
      {/* Hero Section */}
      <Flex
        direction={{ base: 'column', lg: 'row' }}
        align="center"
        justify="space-between"
        mb={10}
        bg="dark.800"
        p={8}
        borderRadius="xl"
        boxShadow="xl"
      >
        <VStack align="start" spacing={4} maxW={{ base: '100%', lg: '60%' }}>
          <Heading size="2xl" lineHeight="shorter">
            Universal Knowledge Graph
          </Heading>
          <Text fontSize="xl" color="gray.300">
            An advanced 13-axis simulation system for dynamic knowledge synthesis across multiple cognitive layers
          </Text>
          <HStack spacing={4} mt={2}>
            <Button
              as={RouterLink}
              to="/chat"
              colorScheme="brand"
              size="lg"
              rightIcon={<FiArrowRight />}
            >
              Start Conversation
            </Button>
            <Button
              as={RouterLink}
              to="/project"
              variant="outline"
              size="lg"
            >
              Explore Project Mode
            </Button>
          </HStack>
        </VStack>
        
        <Box
          maxW={{ base: "100%", lg: "40%" }}
          mt={{ base: 8, lg: 0 }}
          display={{ base: 'none', md: 'block' }}
        >
          {/* Knowledge graph visualization placeholder */}
          <Box
            w="400px"
            h="300px"
            bg="dark.700"
            borderRadius="md"
            p={4}
            display="flex"
            flexDirection="column"
            justifyContent="center"
            alignItems="center"
            border="1px dashed"
            borderColor="gray.600"
          >
            <Icon as={FiLayers} boxSize={12} color="brand.500" mb={4} />
            <Text>Universal Knowledge Graph Visualization</Text>
            <Text fontSize="sm" color="gray.500" mt={2}>
              13-Axis Dynamic System
            </Text>
          </Box>
        </Box>
      </Flex>
      
      {/* System Status */}
      <Card bg="dark.800" mb={10}>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <HStack justify="space-between">
              <Heading size="md">System Status</Heading>
              <Badge colorScheme="green">All Systems Operational</Badge>
            </HStack>
            
            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={5}>
              <Stat>
                <StatLabel>Active Layers</StatLabel>
                <StatNumber>10</StatNumber>
                <StatHelpText>
                  <HStack spacing={1}>
                    <Badge colorScheme="green">L1-L5</Badge>
                    <Badge colorScheme="green">L7-L10</Badge>
                  </HStack>
                </StatHelpText>
              </Stat>
              
              <Stat>
                <StatLabel>Confidence Score</StatLabel>
                <StatNumber>96.5%</StatNumber>
                <StatHelpText>
                  <Badge colorScheme="green">High Confidence</Badge>
                </StatHelpText>
              </Stat>
              
              <Stat>
                <StatLabel>Memory Usage</StatLabel>
                <StatNumber>4.2 GB</StatNumber>
                <StatHelpText>
                  <Badge colorScheme="green">Optimal</Badge>
                </StatHelpText>
              </Stat>
              
              <Stat>
                <StatLabel>Quad Persona</StatLabel>
                <StatNumber>Active</StatNumber>
                <StatHelpText>
                  <Badge colorScheme="green">All Experts Online</Badge>
                </StatHelpText>
              </Stat>
            </SimpleGrid>
            
            <HStack>
              <Text color="gray.500" fontSize="sm">
                Last system check: 3 minutes ago
              </Text>
            </HStack>
          </VStack>
        </CardBody>
      </Card>
      
      {/* Interaction Modes */}
      <Heading size="lg" mb={4}>Interaction Modes</Heading>
      <SimpleGrid columns={{ base: 1, sm: 2, md: 3 }} spacing={6} mb={10}>
        <Card bg="dark.800" _hover={{ borderColor: 'brand.500', cursor: 'pointer' }} as={RouterLink} to="/chat">
          <CardBody>
            <VStack spacing={4} align="center">
              <Icon as={FiMessageSquare} boxSize={10} color="brand.500" />
              <Text fontWeight="bold" fontSize="xl">Chatbot</Text>
              <Text color="gray.400" textAlign="center">
                Conversational interface to interact with the Universal Knowledge Graph
              </Text>
            </VStack>
          </CardBody>
        </Card>
        
        <Card bg="dark.800" _hover={{ borderColor: 'brand.500', cursor: 'pointer' }} as={RouterLink} to="/project">
          <CardBody>
            <VStack spacing={4} align="center">
              <Icon as={FiFolder} boxSize={10} color="green.500" />
              <Text fontWeight="bold" fontSize="xl">Project Mode</Text>
              <Text color="gray.400" textAlign="center">
                Objective-based autonomous agent workflow for complex tasks
              </Text>
            </VStack>
          </CardBody>
        </Card>
        
        <Card bg="dark.800" _hover={{ borderColor: 'brand.500', cursor: 'pointer' }} as={RouterLink} to="/auto-gpt">
          <CardBody>
            <VStack spacing={4} align="center">
              <Icon as={FiCpu} boxSize={10} color="purple.500" />
              <Text fontWeight="bold" fontSize="xl">AutoGPT Mode</Text>
              <Text color="gray.400" textAlign="center">
                Advanced autonomous agent for sophisticated reasoning and task execution
              </Text>
            </VStack>
          </CardBody>
        </Card>
        
        <Card bg="dark.800" _hover={{ borderColor: 'brand.500', cursor: 'pointer' }} as={RouterLink} to="/canvas">
          <CardBody>
            <VStack spacing={4} align="center">
              <Icon as={FiEdit3} boxSize={10} color="blue.500" />
              <Text fontWeight="bold" fontSize="xl">Canvas Mode</Text>
              <Text color="gray.400" textAlign="center">
                Visual knowledge mapping and graph exploration interface
              </Text>
            </VStack>
          </CardBody>
        </Card>
        
        <Card bg="dark.800" _hover={{ borderColor: 'brand.500', cursor: 'pointer' }} as={RouterLink} to="/voice">
          <CardBody>
            <VStack spacing={4} align="center">
              <Icon as={FiMic} boxSize={10} color="red.500" />
              <Text fontWeight="bold" fontSize="xl">Voice Mode</Text>
              <Text color="gray.400" textAlign="center">
                Voice-controlled interface for hands-free UKG interaction
              </Text>
            </VStack>
          </CardBody>
        </Card>
        
        <Card bg="dark.800" _hover={{ borderColor: 'brand.500', cursor: 'pointer' }} as={RouterLink} to="/media-studio">
          <CardBody>
            <VStack spacing={4} align="center">
              <Icon as={FiImage} boxSize={10} color="yellow.500" />
              <Text fontWeight="bold" fontSize="xl">Media Studio</Text>
              <Text color="gray.400" textAlign="center">
                Create images and videos using UKG-enhanced generation
              </Text>
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>
      
      {/* Key System Features */}
      <Heading size="lg" mb={4}>Key UKG System Features</Heading>
      <Grid
        templateColumns={{ base: 'repeat(1, 1fr)', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }}
        gap={6}
        mb={10}
      >
        <Card bg="dark.800">
          <CardBody>
            <HStack align="start" spacing={4}>
              <Icon as={FiLayers} boxSize={6} color="brand.500" mt={1} />
              <VStack align="start" spacing={2}>
                <Text fontWeight="bold">10-Layer AGI Architecture</Text>
                <Text color="gray.400" fontSize="sm">
                  Sophisticated cognitive processing layers from basic request handling to recursive AGI core and self-awareness engine
                </Text>
              </VStack>
            </HStack>
          </CardBody>
        </Card>
        
        <Card bg="dark.800">
          <CardBody>
            <HStack align="start" spacing={4}>
              <Icon as={FiPieChart} boxSize={6} color="green.500" mt={1} />
              <VStack align="start" spacing={2}>
                <Text fontWeight="bold">Quad Persona Engine</Text>
                <Text color="gray.400" fontSize="sm">
                  Integrated expert simulation across Knowledge, Sector, Regulatory, and Compliance domains
                </Text>
              </VStack>
            </HStack>
          </CardBody>
        </Card>
        
        <Card bg="dark.800">
          <CardBody>
            <HStack align="start" spacing={4}>
              <Icon as={FiActivity} boxSize={6} color="purple.500" mt={1} />
              <VStack align="start" spacing={2}>
                <Text fontWeight="bold">Quantum-Enhanced Reasoning</Text>
                <Text color="gray.400" fontSize="sm">
                  Layer 8 quantum simulation improves confidence scores by up to 19% through superposition logic
                </Text>
              </VStack>
            </HStack>
          </CardBody>
        </Card>
        
        <Card bg="dark.800">
          <CardBody>
            <HStack align="start" spacing={4}>
              <Icon as={FiMap} boxSize={6} color="blue.500" mt={1} />
              <VStack align="start" spacing={2}>
                <Text fontWeight="bold">13-Axis Knowledge Structure</Text>
                <Text color="gray.400" fontSize="sm">
                  Comprehensive knowledge organization across 13 dimensions including Pillar Levels, Sectors, and Domains
                </Text>
              </VStack>
            </HStack>
          </CardBody>
        </Card>
        
        <Card bg="dark.800">
          <CardBody>
            <HStack align="start" spacing={4}>
              <Icon as={FiInfo} boxSize={6} color="red.500" mt={1} />
              <VStack align="start" spacing={2}>
                <Text fontWeight="bold">Self-Awareness Engine</Text>
                <Text color="gray.400" fontSize="sm">
                  Layer 10 monitors system integrity through identity tracking and belief decay monitoring
                </Text>
              </VStack>
            </HStack>
          </CardBody>
        </Card>
        
        <Card bg="dark.800">
          <CardBody>
            <HStack align="start" spacing={4}>
              <Icon as={FiMessageSquare} boxSize={6} color="orange.500" mt={1} />
              <VStack align="start" spacing={2}>
                <Text fontWeight="bold">Multi-Pass Refinement</Text>
                <Text color="gray.400" fontSize="sm">
                  12-step refinement workflow with confidence assessment and recursive analysis produces 97% accuracy
                </Text>
              </VStack>
            </HStack>
          </CardBody>
        </Card>
      </Grid>
      
      {/* Getting Started */}
      <Card bg="dark.800" mb={10}>
        <CardBody>
          <VStack spacing={6} align="start">
            <Heading size="md">Getting Started</Heading>
            <Text>
              The Universal Knowledge Graph (UKG) system combines advanced simulation layers with a sophisticated 13-axis knowledge structure. Navigate using the sidebar to explore different interaction modes.
            </Text>
            
            <HStack spacing={4}>
              <Button as={RouterLink} to="/chat" colorScheme="brand">
                Start with Chatbot
              </Button>
              <Button as={RouterLink} to="/simulation-map" variant="outline">
                Explore UKG Structure
              </Button>
            </HStack>
          </VStack>
        </CardBody>
      </Card>
    </Box>
  );
};

export default HomePage;