import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Input,
  IconButton,
  Flex,
  Avatar,
  Textarea,
  Button,
  useColorModeValue,
  Divider,
  Badge,
  Tooltip,
  Card,
  CardBody,
  CardHeader,
  Heading,
  Select,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  SliderMark,
  Collapse
} from '@chakra-ui/react';
import { FiSend, FiSettings, FiChevronDown, FiChevronUp } from 'react-icons/fi';
import { useUKG } from '../contexts/UKGContext';
import { useNotification } from '../contexts/NotificationContext';
import { marked } from 'marked';

const ChatbotPage = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef(null);
  
  // UKG Context
  const { 
    runQuery, 
    activeLayer,
    setActiveLayer,
    confidenceThreshold,
    setConfidenceThreshold,
    refinementSteps,
    setRefinementSteps,
    lastQuery,
    lastResponse
  } = useUKG();
  
  // Notification Context
  const { success, error: showError } = useNotification();
  
  // Scroll to the bottom of the chat on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // When context updates from external actions
  useEffect(() => {
    if (lastQuery && lastResponse && lastQuery !== messages[messages.length - 2]?.content) {
      setMessages(prev => [
        ...prev,
        { role: 'user', content: lastQuery },
        { role: 'assistant', content: lastResponse }
      ]);
    }
  }, [lastQuery, lastResponse, messages]);
  
  // Handle sending a message
  const handleSendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = {
      role: 'user',
      content: input
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsProcessing(true);
    
    try {
      const result = await runQuery(userMessage.content, {
        confidenceThreshold,
        refinementSteps,
        maxLayer: activeLayer
      });
      
      if (result.success) {
        const assistantMessage = {
          role: 'assistant',
          content: result.data.response,
          metadata: {
            confidenceScore: result.data.confidenceScore,
            activeLayer: result.data.activeLayer,
            elapsedTime: result.data.elapsedTime
          }
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        
        if (result.data.activeLayer > 3) {
          success(`Query required Layer ${result.data.activeLayer} processing for optimal confidence.`);
        }
      } else {
        const errorMessage = {
          role: 'assistant',
          content: `I'm sorry, I encountered a problem while processing your request: ${result.error}`,
          error: true
        };
        
        setMessages(prev => [...prev, errorMessage]);
        showError(result.error);
      }
    } catch (err) {
      console.error('Error in query processing:', err);
      
      const errorMessage = {
        role: 'assistant',
        content: 'I apologize, but I experienced an unexpected error while processing your request. Please try again.',
        error: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
      showError('Unexpected error in query processing');
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Handle input change
  const handleInputChange = (e) => {
    setInput(e.target.value);
  };
  
  // Handle key press (Enter to send)
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Toggle settings panel
  const toggleSettings = () => {
    setShowSettings(!showSettings);
  };
  
  // Render message with markdown support
  const renderMessage = (content) => {
    return (
      <Box 
        dangerouslySetInnerHTML={{ 
          __html: marked.parse(content) 
        }} 
        sx={{
          'p': { my: 2 },
          'pre': { bg: 'gray.700', p: 2, borderRadius: 'md', overflowX: 'auto' },
          'code': { fontFamily: 'monospace', fontSize: 'sm' },
          'blockquote': { borderLeftWidth: '2px', borderLeftColor: 'gray.600', pl: 2, ml: 0 },
          'ul, ol': { pl: 4 },
          'a': { color: 'brand.400', textDecoration: 'underline' },
          'table': { borderCollapse: 'collapse', width: 'full', my: 2 },
          'th, td': { borderWidth: '1px', borderColor: 'gray.600', p: 2 }
        }}
      />
    );
  };
  
  return (
    <Box h="full" display="flex" flexDirection="column">
      <Card variant="outline" bg="gray.800" mb={4}>
        <CardHeader pb={2}>
          <Flex justify="space-between" align="center">
            <Heading size="md">Universal Knowledge Graph - Interactive Mode</Heading>
            <Tooltip label={showSettings ? "Hide Settings" : "Show Settings"}>
              <IconButton
                icon={showSettings ? <FiChevronUp /> : <FiChevronDown />}
                variant="ghost"
                onClick={toggleSettings}
                aria-label="Toggle Settings"
              />
            </Tooltip>
          </Flex>
        </CardHeader>
        
        <Collapse in={showSettings} animateOpacity>
          <CardBody pt={0}>
            <Divider mb={4} />
            <Flex direction={{ base: 'column', md: 'row' }} gap={4}>
              <Box flex="1">
                <Text mb={2} fontWeight="medium">Active Layer</Text>
                <Select 
                  value={activeLayer} 
                  onChange={(e) => setActiveLayer(Number(e.target.value))}
                  bg="gray.700"
                >
                  <option value={0}>Layer 0 - Basic Knowledge</option>
                  <option value={1}>Layer 1 - Entity Recognition</option>
                  <option value={2}>Layer 2 - Quad Persona Integration</option>
                  <option value={3}>Layer 3 - Research Simulation</option>
                  <option value={4}>Layer 4 - POV Processing</option>
                  <option value={5}>Layer 5 - Enhanced Capabilities</option>
                  <option value={7}>Layer 7 - Simulated AGI</option>
                  <option value={8}>Layer 8 - Quantum Simulation</option>
                  <option value={9}>Layer 9 - Recursive Processing</option>
                  <option value={10}>Layer 10 - Self-Monitoring</option>
                </Select>
              </Box>
              
              <Box flex="1">
                <Text mb={2} fontWeight="medium">Confidence Threshold: {confidenceThreshold}</Text>
                <Slider 
                  min={0.5} 
                  max={0.99} 
                  step={0.01} 
                  value={confidenceThreshold}
                  onChange={(val) => setConfidenceThreshold(val)}
                >
                  <SliderTrack bg="gray.700">
                    <SliderFilledTrack bg="brand.500" />
                  </SliderTrack>
                  <SliderThumb />
                  <SliderMark value={0.5} mt={2} ml={-2} fontSize="xs">0.5</SliderMark>
                  <SliderMark value={0.75} mt={2} ml={-2} fontSize="xs">0.75</SliderMark>
                  <SliderMark value={0.99} mt={2} ml={-2} fontSize="xs">0.99</SliderMark>
                </Slider>
              </Box>
              
              <Box flex="1">
                <Text mb={2} fontWeight="medium">Refinement Steps: {refinementSteps}</Text>
                <Slider 
                  min={1} 
                  max={24} 
                  step={1} 
                  value={refinementSteps}
                  onChange={(val) => setRefinementSteps(val)}
                >
                  <SliderTrack bg="gray.700">
                    <SliderFilledTrack bg="brand.500" />
                  </SliderTrack>
                  <SliderThumb />
                  <SliderMark value={1} mt={2} ml={-1} fontSize="xs">1</SliderMark>
                  <SliderMark value={12} mt={2} ml={-2} fontSize="xs">12</SliderMark>
                  <SliderMark value={24} mt={2} ml={-2} fontSize="xs">24</SliderMark>
                </Slider>
              </Box>
            </Flex>
          </CardBody>
        </Collapse>
      </Card>
      
      {/* Messages container */}
      <Box
        flex="1"
        overflowY="auto"
        bg="gray.900"
        borderRadius="md"
        p={4}
        mb={4}
      >
        {messages.length === 0 ? (
          <Flex
            direction="column"
            alignItems="center"
            justifyContent="center"
            h="full"
            textAlign="center"
            color="gray.500"
            p={8}
          >
            <Heading size="md" mb={4}>Welcome to the Universal Knowledge Graph</Heading>
            <Text mb={4}>
              Interact with the 13-axis knowledge system to access multi-perspective insights 
              across various domains and knowledge levels.
            </Text>
            <Text fontStyle="italic">
              Try asking questions like: "Explain the relationship between quantum computing and machine learning" 
              or "Analyze cybersecurity regulations across financial and healthcare sectors."
            </Text>
          </Flex>
        ) : (
          <VStack spacing={4} align="stretch">
            {messages.map((message, index) => (
              <Box
                key={index}
                bg={message.role === 'user' ? 'gray.800' : message.error ? 'red.900' : 'gray.700'}
                p={4}
                borderRadius="md"
                maxW="100%"
                alignSelf={message.role === 'user' ? 'flex-end' : 'flex-start'}
                boxShadow="sm"
              >
                <HStack spacing={3} align="flex-start" mb={2}>
                  <Avatar
                    size="sm"
                    name={message.role === 'user' ? 'User' : 'UKG'}
                    bg={message.role === 'user' ? 'purple.500' : 'brand.500'}
                  />
                  <Box>
                    <Text fontWeight="bold">
                      {message.role === 'user' ? 'You' : 'Universal Knowledge Graph'}
                    </Text>
                    {message.metadata && (
                      <HStack spacing={2} mt={1}>
                        <Badge colorScheme="blue">
                          Layer {message.metadata.activeLayer}
                        </Badge>
                        <Badge 
                          colorScheme={
                            message.metadata.confidenceScore > 0.9 ? 'green' : 
                            message.metadata.confidenceScore > 0.75 ? 'yellow' : 'red'
                          }
                        >
                          Confidence: {Math.round(message.metadata.confidenceScore * 100)}%
                        </Badge>
                        <Badge colorScheme="gray">
                          {message.metadata.elapsedTime}ms
                        </Badge>
                      </HStack>
                    )}
                  </Box>
                </HStack>
                
                <Box ml={10}>
                  {renderMessage(message.content)}
                </Box>
              </Box>
            ))}
            <div ref={messagesEndRef} />
          </VStack>
        )}
      </Box>
      
      {/* Input box */}
      <Box>
        <Flex>
          <Textarea
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder="Ask a question or enter a prompt..."
            resize="none"
            bg="gray.800"
            borderRadius="md"
            border="none"
            _focus={{ border: 'none', boxShadow: '0 0 0 1px #3182ce' }}
            mr={2}
            rows={2}
          />
          <IconButton
            colorScheme="brand"
            aria-label="Send message"
            icon={<FiSend />}
            onClick={handleSendMessage}
            alignSelf="flex-end"
            isLoading={isProcessing}
            isDisabled={!input.trim() || isProcessing}
          />
        </Flex>
        <Text fontSize="xs" color="gray.500" mt={1} textAlign="right">
          Press Enter to send, Shift+Enter for new line
        </Text>
      </Box>
    </Box>
  );
};

export default ChatbotPage;