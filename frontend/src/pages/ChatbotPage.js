import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  VStack, 
  HStack, 
  Input, 
  Button, 
  IconButton, 
  Text, 
  Avatar, 
  Flex,
  Divider,
  useColorModeValue,
  Textarea,
  Select,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Badge,
  Card,
  CardBody
} from '@chakra-ui/react';
import { FiSend, FiMic, FiUpload, FiMaximize, FiInfo } from 'react-icons/fi';

const ChatbotPage = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'system',
      content: 'Welcome to the Universal Knowledge Graph System. How can I assist you today?',
      timestamp: new Date().toISOString(),
      confidence: 0.97,
      perspectives: [
        { role: 'Knowledge', agreement: 'high' },
        { role: 'Sector', agreement: 'high' },
        { role: 'Regulatory', agreement: 'medium' },
        { role: 'Compliance', agreement: 'high' }
      ]
    }
  ]);
  
  const [input, setInput] = useState('');
  const [selectedPersona, setSelectedPersona] = useState('auto');
  const [isProcessing, setIsProcessing] = useState(false);
  
  const endOfMessagesRef = useRef(null);
  
  // Scroll to bottom whenever messages change
  useEffect(() => {
    if (endOfMessagesRef.current) {
      endOfMessagesRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  const handleSendMessage = () => {
    if (input.trim() === '') return;
    
    // Add user message
    const userMessage = {
      id: messages.length + 1,
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };
    
    setMessages([...messages, userMessage]);
    setInput('');
    setIsProcessing(true);
    
    // Simulate response from UKG system (replace with actual API call)
    setTimeout(() => {
      const systemResponse = {
        id: messages.length + 2,
        role: 'system',
        content: getSimulatedResponse(input, selectedPersona),
        timestamp: new Date().toISOString(),
        confidence: Math.random() * 0.1 + 0.89, // Random confidence between 0.89 and 0.99
        perspectives: [
          { role: 'Knowledge', agreement: getRandomAgreement() },
          { role: 'Sector', agreement: getRandomAgreement() },
          { role: 'Regulatory', agreement: getRandomAgreement() },
          { role: 'Compliance', agreement: getRandomAgreement() }
        ],
        refinementPasses: Math.floor(Math.random() * 3) + 1,
        layersActivated: getRandomLayers()
      };
      
      setMessages(prevMessages => [...prevMessages, systemResponse]);
      setIsProcessing(false);
    }, 2000);
  };
  
  // Helper function to get random agreement level
  const getRandomAgreement = () => {
    const levels = ['high', 'medium', 'low'];
    return levels[Math.floor(Math.random() * levels.length)];
  };
  
  // Helper function to get random activated layers
  const getRandomLayers = () => {
    const allLayers = [1, 2, 3, 4, 5, 6, 7];
    const layerCount = Math.floor(Math.random() * 4) + 3; // Between 3-7 layers
    const layers = [];
    
    while (layers.length < layerCount) {
      const layer = allLayers[Math.floor(Math.random() * allLayers.length)];
      if (!layers.includes(layer)) {
        layers.push(layer);
      }
    }
    
    return layers.sort((a, b) => a - b);
  };
  
  // Simple response generation for demo purposes
  const getSimulatedResponse = (query, persona) => {
    if (query.toLowerCase().includes('compliance') || query.toLowerCase().includes('regulatory')) {
      return 'Based on the Universal Knowledge Graph analysis, compliance requirements include documentation of algorithms, regular testing procedures, kill switches for emergency situations, and comprehensive audit trails. Organizations must demonstrate that their systems cannot manipulate markets and adhere to SEC Rule 15c3-5 and MiFID II regulations.';
    } else if (query.toLowerCase().includes('data') || query.toLowerCase().includes('privacy')) {
      return 'The UKG simulation indicates that data privacy regulations like GDPR, CCPA, and emerging global standards require data minimization, explicit consent mechanisms, and data portability. There are inherent tensions between extensive AI data collection needs and privacy compliance that organizations must navigate through privacy-by-design principles.';
    } else {
      return 'According to the Universal Knowledge Graph analysis across all 13 axes, this query involves multiple domains and regulatory frameworks. The simulated experts recommend considering both technical implementation challenges and compliance requirements. Further details can be provided by activating specific expert personas or requesting a deeper simulation pass.';
    }
  };
  
  // Format the timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // Get agreement color
  const getAgreementColor = (agreement) => {
    switch (agreement) {
      case 'high': return 'green.500';
      case 'medium': return 'yellow.500';
      case 'low': return 'red.500';
      default: return 'gray.500';
    }
  };
  
  // Get confidence color
  const getConfidenceColor = (score) => {
    if (score >= 0.95) return 'green.500';
    if (score >= 0.85) return 'yellow.500';
    return 'red.500';
  };
  
  return (
    <Box h="100%" display="flex" flexDirection="column">
      <Flex mb={4}>
        <Text fontSize="2xl" fontWeight="bold">UKG Chat Interface</Text>
      </Flex>
      
      <Flex flex="1" overflow="hidden">
        {/* Left Panel - Chat Window */}
        <Box 
          flex="1" 
          borderRadius="md" 
          bg="dark.700" 
          p={4}
          display="flex"
          flexDirection="column"
          mr={4}
          overflow="hidden"
        >
          {/* Messages Area */}
          <Box flex="1" overflowY="auto" mb={4} px={2}>
            <VStack spacing={4} align="stretch">
              {messages.map((msg) => (
                <Box key={msg.id}>
                  <HStack spacing={3} alignItems="flex-start">
                    <Avatar 
                      bg={msg.role === 'system' ? 'brand.500' : 'gray.500'} 
                      icon={<Text fontSize="sm">{msg.role === 'system' ? 'UKG' : 'You'}</Text>}
                      size="sm"
                    />
                    <Box flex="1">
                      <HStack mb={1}>
                        <Text fontWeight="bold">
                          {msg.role === 'system' ? 'Universal Knowledge Graph' : 'You'}
                        </Text>
                        <Text fontSize="xs" color="gray.500">
                          {formatTime(msg.timestamp)}
                        </Text>
                        {msg.confidence && (
                          <Badge colorScheme={msg.confidence >= 0.95 ? "green" : "yellow"}>
                            {(msg.confidence * 100).toFixed(1)}%
                          </Badge>
                        )}
                      </HStack>
                      <Text>{msg.content}</Text>
                      
                      {/* Perspective Agreement (for system messages) */}
                      {msg.role === 'system' && msg.perspectives && (
                        <HStack mt={2} spacing={2}>
                          {msg.perspectives.map((perspective, idx) => (
                            <Badge 
                              key={idx} 
                              variant="outline" 
                              colorScheme={perspective.agreement === 'high' ? 'green' : 
                                          perspective.agreement === 'medium' ? 'yellow' : 'red'}
                              size="sm"
                            >
                              {perspective.role}
                            </Badge>
                          ))}
                        </HStack>
                      )}
                      
                      {/* Simulation Details */}
                      {msg.role === 'system' && msg.layersActivated && (
                        <HStack mt={1} fontSize="xs" color="gray.500">
                          <Text>Passes: {msg.refinementPasses}</Text>
                          <Text>•</Text>
                          <Text>Layers: {msg.layersActivated.join(', ')}</Text>
                        </HStack>
                      )}
                    </Box>
                  </HStack>
                  <Divider mt={4} mb={2} opacity={0.2} />
                </Box>
              ))}
              <div ref={endOfMessagesRef} />
            </VStack>
            
            {isProcessing && (
              <Flex align="center" mt={4}>
                <Text fontSize="sm" color="gray.500">UKG System thinking...</Text>
                <Box
                  as="span"
                  display="inline-block"
                  ml={2}
                  h="6px"
                  w="6px"
                  borderRadius="full"
                  bg="brand.500"
                  animation="pulse 1.5s infinite"
                />
              </Flex>
            )}
          </Box>
          
          {/* Input Area */}
          <HStack spacing={2} mt={2}>
            <Select 
              size="md" 
              w="180px" 
              value={selectedPersona} 
              onChange={(e) => setSelectedPersona(e.target.value)}
              bg="dark.800"
              borderColor="gray.600"
            >
              <option value="auto">Auto-Detect Personas</option>
              <option value="knowledge">Knowledge Expert</option>
              <option value="sector">Sector Expert</option>
              <option value="regulatory">Regulatory Expert</option>
              <option value="compliance">Compliance Expert</option>
              <option value="quad">Quad Persona Mode</option>
            </Select>
            
            <Box flex="1" position="relative">
              <Textarea
                placeholder="Ask the Universal Knowledge Graph..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                size="md"
                resize="none"
                rows={1}
                bg="dark.800"
                borderColor="gray.600"
              />
            </Box>

            <IconButton
              aria-label="Send message"
              icon={<FiSend />}
              onClick={handleSendMessage}
              colorScheme="brand"
              size="md"
            />
            
            <IconButton
              aria-label="Voice input"
              icon={<FiMic />}
              variant="outline"
              size="md"
            />
            
            <IconButton
              aria-label="Upload file"
              icon={<FiUpload />}
              variant="outline"
              size="md"
            />
          </HStack>
        </Box>
        
        {/* Right Panel - Context & Simulation Details */}
        <Box 
          w="300px" 
          borderRadius="md" 
          bg="dark.700" 
          p={4}
          overflowY="auto"
        >
          <Tabs size="sm" variant="enclosed" colorScheme="brand">
            <TabList>
              <Tab>Simulation</Tab>
              <Tab>Context</Tab>
              <Tab>Agents</Tab>
            </TabList>
            
            <TabPanels>
              {/* Simulation Panel */}
              <TabPanel>
                <VStack spacing={4} align="stretch">
                  <Card variant="outline" size="sm" bg="dark.800">
                    <CardBody>
                      <Text fontWeight="semibold" mb={2}>Active Simulation Layers</Text>
                      <Box>
                        {[1, 2, 3, 4, 5, 6, 7].map((layer) => (
                          <Badge 
                            key={layer}
                            m={1}
                            colorScheme={layer <= 5 ? 'green' : layer <= 7 ? 'blue' : 'purple'}
                          >
                            Layer {layer}
                          </Badge>
                        ))}
                      </Box>
                    </CardBody>
                  </Card>
                  
                  <Card variant="outline" size="sm" bg="dark.800">
                    <CardBody>
                      <Text fontWeight="semibold" mb={2}>Confidence Score</Text>
                      <Flex align="center" justify="space-between">
                        <Text fontSize="2xl" fontWeight="bold" color="green.500">96.5%</Text>
                        <Badge colorScheme="green">High</Badge>
                      </Flex>
                      <Text fontSize="xs" color="gray.500" mt={1}>
                        Based on 3 refinement passes
                      </Text>
                    </CardBody>
                  </Card>
                  
                  <Card variant="outline" size="sm" bg="dark.800">
                    <CardBody>
                      <Text fontWeight="semibold" mb={2}>Simulation Stats</Text>
                      <VStack align="stretch" spacing={1} fontSize="sm">
                        <Flex justify="space-between">
                          <Text>Entropy Score:</Text>
                          <Text>0.243</Text>
                        </Flex>
                        <Flex justify="space-between">
                          <Text>Emergence:</Text>
                          <Text>0.112</Text>
                        </Flex>
                        <Flex justify="space-between">
                          <Text>Memory Anchors:</Text>
                          <Text>27</Text>
                        </Flex>
                        <Flex justify="space-between">
                          <Text>Identity Consistency:</Text>
                          <Text>0.925</Text>
                        </Flex>
                      </VStack>
                    </CardBody>
                  </Card>
                </VStack>
              </TabPanel>
              
              {/* Context Panel */}
              <TabPanel>
                <VStack spacing={4} align="stretch">
                  <Card variant="outline" size="sm" bg="dark.800">
                    <CardBody>
                      <Text fontWeight="semibold" mb={2}>Active UKG Axes</Text>
                      <Box>
                        {[2, 3, 8, 9, 10, 11, 13].map((axis) => (
                          <Badge 
                            key={axis}
                            m={1}
                          >
                            Axis {axis}
                          </Badge>
                        ))}
                      </Box>
                    </CardBody>
                  </Card>
                  
                  <Card variant="outline" size="sm" bg="dark.800">
                    <CardBody>
                      <Text fontWeight="semibold" mb={2}>Domain Context</Text>
                      <VStack align="stretch" spacing={1} fontSize="sm">
                        <Flex justify="space-between">
                          <Text>Pillar Level:</Text>
                          <Text>PL32</Text>
                        </Flex>
                        <Flex justify="space-between">
                          <Text>Sector Code:</Text>
                          <Text>NAICS 5182</Text>
                        </Flex>
                        <Flex justify="space-between">
                          <Text>Branch:</Text>
                          <Text>Technology</Text>
                        </Flex>
                      </VStack>
                    </CardBody>
                  </Card>
                </VStack>
              </TabPanel>
              
              {/* Agents Panel */}
              <TabPanel>
                <VStack spacing={4} align="stretch">
                  <Card variant="outline" size="sm" bg="dark.800">
                    <CardBody>
                      <Text fontWeight="semibold" mb={2}>Active Agents</Text>
                      <VStack align="stretch" spacing={1} fontSize="sm">
                        <Flex justify="space-between" align="center">
                          <Text>Gatekeeper</Text>
                          <Badge colorScheme="green">Active</Badge>
                        </Flex>
                        <Flex justify="space-between" align="center">
                          <Text>Knowledge Expert</Text>
                          <Badge colorScheme="green">Active</Badge>
                        </Flex>
                        <Flex justify="space-between" align="center">
                          <Text>Sector Expert</Text>
                          <Badge colorScheme="green">Active</Badge>
                        </Flex>
                        <Flex justify="space-between" align="center">
                          <Text>Regulatory Expert</Text>
                          <Badge colorScheme="green">Active</Badge>
                        </Flex>
                        <Flex justify="space-between" align="center">
                          <Text>Compliance Expert</Text>
                          <Badge colorScheme="green">Active</Badge>
                        </Flex>
                      </VStack>
                    </CardBody>
                  </Card>
                </VStack>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Box>
      </Flex>
    </Box>
  );
};

export default ChatbotPage;