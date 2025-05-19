import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Flex,
  Text,
  Button,
  IconButton,
  Progress,
  Card,
  CardBody,
  Divider,
  Badge,
  Avatar,
  Switch,
  FormControl,
  FormLabel,
  Select,
  useToast,
  List,
  ListItem,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Tooltip
} from '@chakra-ui/react';
import {
  FiMic,
  FiMicOff,
  FiPause,
  FiPlay,
  FiSettings,
  FiVolume2,
  FiVolumeX,
  FiCpu,
  FiChevronDown,
  FiChevronUp,
  FiX,
  FiCheck,
  FiAlertCircle,
  FiInfo,
  FiRefreshCw,
  FiSave,
  FiUpload
} from 'react-icons/fi';

const VoicePage = () => {
  const toast = useToast();
  const [isListening, setIsListening] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [responses, setResponses] = useState([
    {
      id: 1,
      query: "What is the Universal Knowledge Graph?",
      response: "The Universal Knowledge Graph is a 13-axis simulation system that integrates knowledge across multiple domains, experts, and regulatory frameworks. It uses a layered architecture with simulated reasoning to provide comprehensive insights.",
      confidence: 0.96,
      activeLayers: [1, 2, 3, 4, 5],
      timestamp: new Date(Date.now() - 3600000).toISOString()
    }
  ]);
  const [activeResponse, setActiveResponse] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeakingResponse, setIsSpeakingResponse] = useState(false);
  
  // Voice settings
  const [voiceSettings, setVoiceSettings] = useState({
    voiceId: 'default',
    speed: 1.0,
    autoResponse: true,
    activationPhrase: 'UKG',
    confidenceThreshold: 0.8,
    maxResponseTime: 15
  });
  
  // Audio visualization
  const audioVisRef = useRef(null);
  const audioContext = useRef(null);
  const analyzer = useRef(null);
  const mockIntervalRef = useRef(null);
  
  // Voice recognition simulation
  useEffect(() => {
    if (isListening) {
      // Start the audio visualization
      mockIntervalRef.current = setInterval(() => {
        const newLevel = Math.random() * 100;
        setAudioLevel(newLevel);
      }, 100);
      
      // Simulate detecting phrases after a delay
      setTimeout(() => {
        if (isListening) {
          setTranscript("Tell me about regulatory compliance requirements in healthcare");
        }
      }, 4000);
    } else {
      // Stop the audio visualization
      if (mockIntervalRef.current) {
        clearInterval(mockIntervalRef.current);
        setAudioLevel(0);
      }
    }
    
    return () => {
      if (mockIntervalRef.current) {
        clearInterval(mockIntervalRef.current);
      }
    };
  }, [isListening]);
  
  // Process transcribed text
  const processTranscript = () => {
    if (!transcript.trim()) return;
    
    setIsProcessing(true);
    
    // Simulate UKG processing
    setTimeout(() => {
      const newResponse = {
        id: responses.length + 1,
        query: transcript,
        response: getSimulatedResponse(transcript),
        confidence: 0.88 + Math.random() * 0.1,
        activeLayers: [1, 2, 3, 4, 7],
        timestamp: new Date().toISOString()
      };
      
      setResponses([...responses, newResponse]);
      setActiveResponse(newResponse);
      setIsProcessing(false);
      setTranscript('');
      
      // Auto speak response if enabled
      if (voiceSettings.autoResponse) {
        speakResponse(newResponse.response);
      }
      
      toast({
        title: "Response Generated",
        description: "The UKG system has processed your voice query",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    }, 3000);
  };
  
  // Simple response simulation
  const getSimulatedResponse = (query) => {
    if (query.toLowerCase().includes('regulatory') || query.toLowerCase().includes('compliance')) {
      return "Healthcare regulatory compliance incorporates several frameworks including HIPAA for patient data privacy, FDA regulations for medical devices and software, and Medicare/Medicaid requirements. Organizations need comprehensive policies, regular staff training, documentation, and ongoing monitoring to ensure compliance. AI systems in healthcare must meet additional requirements around bias, transparency, and clinical validation.";
    } else if (query.toLowerCase().includes('universal') || query.toLowerCase().includes('knowledge graph')) {
      return "The Universal Knowledge Graph is a 13-axis simulation system that integrates knowledge across multiple domains using a layered architecture. It incorporates quad persona simulation with expert roles in Knowledge, Sector, Regulatory, and Compliance domains. The system uses recursive planning and quantum-like processing to resolve ambiguities.";
    } else {
      return "Based on your query, the Universal Knowledge Graph has analyzed relevant information across multiple domains. The system activated Layers 1 through 5 to process your request, with the Knowledge and Regulatory expert personas providing the highest confidence contributions. Would you like me to explore any specific aspect in more detail?";
    }
  };
  
  // Toggle listening state
  const toggleListening = () => {
    setIsListening(!isListening);
    
    if (!isListening) {
      toast({
        title: "Voice Recognition Active",
        description: "Listening for your query...",
        status: "info",
        duration: 2000,
        isClosable: true,
      });
    } else {
      if (transcript.trim()) {
        processTranscript();
      }
    }
  };
  
  // Speak response using text-to-speech
  const speakResponse = (text) => {
    setIsSpeakingResponse(true);
    
    // Simulate speaking with a timeout
    const wordCount = text.split(' ').length;
    const speakingTime = (wordCount / 3) * 1000; // Rough estimate: 3 words per second
    
    toast({
      title: "Speaking Response",
      description: "UKG is vocally responding to your query",
      status: "info",
      duration: 2000,
      isClosable: true,
    });
    
    // End speaking after the calculated time
    setTimeout(() => {
      setIsSpeakingResponse(false);
    }, speakingTime);
  };
  
  // Format timestamp
  const formatTime = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return 'Invalid time';
    }
  };
  
  return (
    <Box h="100%" display="flex" flexDirection="column">
      <Flex mb={6} justify="space-between" align="center">
        <Text fontSize="2xl" fontWeight="bold">Voice Interaction Mode</Text>
        
        <HStack>
          <Button
            leftIcon={isSpeakingResponse ? <FiVolumeX /> : <FiVolume2 />}
            size="sm"
            colorScheme={isSpeakingResponse ? "orange" : "gray"}
            variant="outline"
            onClick={() => {
              if (isSpeakingResponse) {
                setIsSpeakingResponse(false);
                toast({
                  title: "Voice Output Stopped",
                  status: "info",
                  duration: 2000,
                  isClosable: true,
                });
              } else if (activeResponse) {
                speakResponse(activeResponse.response);
              }
            }}
          >
            {isSpeakingResponse ? "Stop Speaking" : "Speak Response"}
          </Button>
          
          <Select 
            size="sm"
            width="180px"
            value={voiceSettings.voiceId}
            onChange={(e) => setVoiceSettings({...voiceSettings, voiceId: e.target.value})}
          >
            <option value="default">Default Voice</option>
            <option value="conversational">Conversational</option>
            <option value="professional">Professional</option>
            <option value="neural">Neural TTS</option>
          </Select>
        </HStack>
      </Flex>
      
      <Flex flex="1" gap={4}>
        {/* Left Panel - Voice Input */}
        <Card flex="3" bg="dark.700" variant="outline">
          <CardBody p={4} display="flex" flexDirection="column">
            {/* Audio Visualizer */}
            <Box 
              h="140px" 
              mb={4} 
              bg="dark.800"
              borderRadius="md"
              overflow="hidden"
              position="relative"
              ref={audioVisRef}
            >
              {/* Audio Wave Visualization */}
              <Flex
                h="100%"
                align="center"
                justify="center"
                p={4}
              >
                {Array.from({ length: 30 }).map((_, i) => (
                  <Box
                    key={i}
                    w="6px"
                    h={`${isListening ? (20 + Math.random() * audioLevel) : 5}%`}
                    mx="2px"
                    bg={isListening ? "brand.500" : "gray.600"}
                    transition="height 0.1s ease-in-out"
                  />
                ))}
              </Flex>
              
              {/* Status Overlay */}
              {!isListening && !isProcessing && (
                <Flex
                  position="absolute"
                  top="0"
                  left="0"
                  w="100%"
                  h="100%"
                  align="center"
                  justify="center"
                  bg="rgba(0, 0, 0, 0.5)"
                  color="white"
                  flexDirection="column"
                >
                  <Text>Click the microphone to start speaking</Text>
                </Flex>
              )}
              
              {isProcessing && (
                <Flex
                  position="absolute"
                  top="0"
                  left="0"
                  w="100%"
                  h="100%"
                  align="center"
                  justify="center"
                  bg="rgba(0, 0, 0, 0.7)"
                  color="white"
                  flexDirection="column"
                >
                  <Text mb={2}>Processing your query...</Text>
                  <Progress 
                    size="sm" 
                    w="70%" 
                    isIndeterminate 
                    colorScheme="brand" 
                    borderRadius="md" 
                  />
                </Flex>
              )}
            </Box>
            
            {/* Recognized Speech */}
            <Box mb={6}>
              <Text mb={2} fontWeight="semibold">Recognized Speech</Text>
              <Box
                p={3}
                minH="60px"
                bg="dark.800"
                borderRadius="md"
                border="1px solid"
                borderColor={isListening ? "brand.500" : "gray.700"}
              >
                {transcript ? (
                  <Text>{transcript}</Text>
                ) : (
                  <Text color="gray.500">Your speech will appear here...</Text>
                )}
              </Box>
            </Box>
            
            {/* Control Buttons */}
            <Flex justify="center" gap={3} mt="auto">
              <Tooltip label={isListening ? "Stop listening" : "Start listening"}>
                <IconButton
                  icon={isListening ? <FiMicOff /> : <FiMic />}
                  aria-label={isListening ? "Stop listening" : "Start listening"}
                  onClick={toggleListening}
                  colorScheme={isListening ? "red" : "brand"}
                  size="lg"
                  height="64px"
                  width="64px"
                  isRound
                  boxShadow="lg"
                />
              </Tooltip>
              
              <Tooltip label="Process transcript">
                <IconButton
                  icon={<FiCpu />}
                  aria-label="Process transcript"
                  onClick={processTranscript}
                  colorScheme="green"
                  size="lg"
                  isDisabled={!transcript.trim() || isProcessing || isListening}
                />
              </Tooltip>
              
              <Tooltip label="Clear transcript">
                <IconButton
                  icon={<FiX />}
                  aria-label="Clear transcript"
                  onClick={() => setTranscript('')}
                  size="lg"
                  isDisabled={!transcript.trim() || isProcessing || isListening}
                />
              </Tooltip>
              
              <Tooltip label="Voice settings">
                <IconButton
                  icon={<FiSettings />}
                  aria-label="Voice settings"
                  size="lg"
                  variant="outline"
                />
              </Tooltip>
            </Flex>
          </CardBody>
        </Card>
        
        {/* Right Panel - Responses & Settings */}
        <Flex flex="2" direction="column" gap={4}>
          {/* Active Response */}
          {activeResponse && (
            <Card bg="dark.700" variant="outline">
              <CardBody>
                <VStack align="stretch" spacing={4}>
                  <HStack justify="space-between">
                    <Text fontWeight="bold">UKG Response</Text>
                    <Badge colorScheme={activeResponse.confidence > 0.9 ? "green" : "yellow"}>
                      {Math.round(activeResponse.confidence * 100)}% Confidence
                    </Badge>
                  </HStack>
                  
                  <Box p={3} bg="dark.800" borderRadius="md">
                    <Text>{activeResponse.response}</Text>
                  </Box>
                  
                  <HStack wrap="wrap" spacing={2}>
                    <Text fontSize="sm" color="gray.400">Active Layers:</Text>
                    {activeResponse.activeLayers.map(layer => (
                      <Badge key={layer} colorScheme="brand">L{layer}</Badge>
                    ))}
                  </HStack>
                  
                  <Tooltip label={isSpeakingResponse ? "Stop speaking" : "Speak this response"}>
                    <Button
                      leftIcon={isSpeakingResponse ? <FiVolumeX /> : <FiVolume2 />}
                      size="sm"
                      onClick={() => {
                        if (isSpeakingResponse) {
                          setIsSpeakingResponse(false);
                        } else {
                          speakResponse(activeResponse.response);
                        }
                      }}
                      isLoading={isSpeakingResponse}
                      loadingText="Speaking..."
                    >
                      {isSpeakingResponse ? "Stop" : "Speak"}
                    </Button>
                  </Tooltip>
                </VStack>
              </CardBody>
            </Card>
          )}
          
          {/* Conversation History & Settings */}
          <Card flex="1" bg="dark.700" variant="outline">
            <Tabs variant="soft-rounded" colorScheme="brand" size="sm">
              <TabList px={4} pt={4}>
                <Tab>Conversation</Tab>
                <Tab>Voice Settings</Tab>
              </TabList>
              
              <TabPanels>
                <TabPanel p={4}>
                  <VStack align="stretch" spacing={4} maxH="400px" overflowY="auto">
                    {responses.length > 0 ? (
                      responses.map((response) => (
                        <Card 
                          key={response.id} 
                          size="sm" 
                          bg="dark.800"
                          variant="outline"
                          borderColor={activeResponse?.id === response.id ? "brand.500" : "transparent"}
                          onClick={() => setActiveResponse(response)}
                          cursor="pointer"
                          _hover={{ bg: "dark.900" }}
                        >
                          <CardBody py={2}>
                            <VStack align="stretch" spacing={1}>
                              <HStack justify="space-between">
                                <Text fontWeight="semibold" fontSize="sm">
                                  {response.query.length > 50 
                                    ? response.query.substring(0, 50) + '...'
                                    : response.query
                                  }
                                </Text>
                                <Text fontSize="xs" color="gray.500">
                                  {formatTime(response.timestamp)}
                                </Text>
                              </HStack>
                              
                              <Text fontSize="xs" noOfLines={2} color="gray.400">
                                {response.response.substring(0, 100)}...
                              </Text>
                              
                              <HStack>
                                <Badge size="sm" colorScheme={response.confidence > 0.9 ? "green" : "yellow"}>
                                  {Math.round(response.confidence * 100)}%
                                </Badge>
                                
                                <Text fontSize="xs" color="gray.500">
                                  Layers: {response.activeLayers.join(', ')}
                                </Text>
                              </HStack>
                            </VStack>
                          </CardBody>
                        </Card>
                      ))
                    ) : (
                      <Text color="gray.500" textAlign="center">
                        No conversation history yet
                      </Text>
                    )}
                  </VStack>
                </TabPanel>
                
                <TabPanel p={4}>
                  <VStack align="stretch" spacing={4}>
                    <FormControl display="flex" alignItems="center" justifyContent="space-between">
                      <FormLabel htmlFor="auto-response" mb="0" fontSize="sm">
                        Auto-Speak Response
                      </FormLabel>
                      <Switch 
                        id="auto-response"
                        isChecked={voiceSettings.autoResponse}
                        onChange={(e) => setVoiceSettings({
                          ...voiceSettings,
                          autoResponse: e.target.checked
                        })}
                        colorScheme="brand"
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Voice</FormLabel>
                      <Select 
                        value={voiceSettings.voiceId}
                        onChange={(e) => setVoiceSettings({
                          ...voiceSettings,
                          voiceId: e.target.value
                        })}
                        bg="dark.800"
                      >
                        <option value="default">Default Voice</option>
                        <option value="conversational">Conversational</option>
                        <option value="professional">Professional</option>
                        <option value="neural">Neural TTS</option>
                      </Select>
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Speech Speed</FormLabel>
                      <HStack>
                        <IconButton
                          icon={<FiChevronDown />}
                          size="sm"
                          onClick={() => setVoiceSettings({
                            ...voiceSettings,
                            speed: Math.max(0.5, voiceSettings.speed - 0.1)
                          })}
                          isDisabled={voiceSettings.speed <= 0.5}
                        />
                        
                        <Box flex="1" textAlign="center">
                          <Text>{voiceSettings.speed.toFixed(1)}x</Text>
                        </Box>
                        
                        <IconButton
                          icon={<FiChevronUp />}
                          size="sm"
                          onClick={() => setVoiceSettings({
                            ...voiceSettings,
                            speed: Math.min(2.0, voiceSettings.speed + 0.1)
                          })}
                          isDisabled={voiceSettings.speed >= 2.0}
                        />
                      </HStack>
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Activation Phrase</FormLabel>
                      <Select 
                        value={voiceSettings.activationPhrase}
                        onChange={(e) => setVoiceSettings({
                          ...voiceSettings,
                          activationPhrase: e.target.value
                        })}
                        bg="dark.800"
                      >
                        <option value="UKG">UKG</option>
                        <option value="Universal Knowledge Graph">Universal Knowledge Graph</option>
                        <option value="Assistant">Assistant</option>
                        <option value="Computer">Computer</option>
                      </Select>
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Confidence Threshold</FormLabel>
                      <HStack>
                        <Text fontSize="sm" minW="40px">
                          {Math.round(voiceSettings.confidenceThreshold * 100)}%
                        </Text>
                        <Box flex="1">
                          <Progress 
                            value={voiceSettings.confidenceThreshold * 100} 
                            min={50}
                            max={100}
                            size="sm"
                            colorScheme="brand"
                            borderRadius="md"
                          />
                        </Box>
                      </HStack>
                    </FormControl>
                    
                    <Button
                      leftIcon={<FiSave />}
                      colorScheme="brand"
                      size="sm"
                      onClick={() => {
                        toast({
                          title: "Settings Saved",
                          description: "Voice interaction settings have been updated",
                          status: "success",
                          duration: 2000,
                          isClosable: true,
                        });
                      }}
                    >
                      Save Settings
                    </Button>
                  </VStack>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </Card>
        </Flex>
      </Flex>
    </Box>
  );
};

export default VoicePage;