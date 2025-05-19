import React, { useState, useEffect } from 'react';
import {
  Box,
  Flex,
  VStack,
  HStack,
  Text,
  Heading,
  Button,
  IconButton,
  Select,
  Input,
  InputGroup,
  InputRightElement,
  Badge,
  Card,
  CardBody,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Divider,
  Switch,
  FormControl,
  FormLabel,
  Checkbox,
  useColorModeValue,
  useToast
} from '@chakra-ui/react';
import {
  FiRefreshCw,
  FiDownload,
  FiSearch,
  FiFilter,
  FiAlertCircle,
  FiInfo,
  FiCheckCircle,
  FiActivity,
  FiCpu,
  FiServer,
  FiLayers,
  FiCalendar,
  FiClock,
  FiTrash2,
  FiSettings,
  FiMoreVertical
} from 'react-icons/fi';

const LogsPage = () => {
  const toast = useToast();
  const [activeTab, setActiveTab] = useState('system');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterLevel, setFilterLevel] = useState('all');
  const [timeRange, setTimeRange] = useState('24h');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30);
  
  // Sample log data
  const [systemLogs, setSystemLogs] = useState([
    {
      id: 1,
      timestamp: '2025-05-19T21:15:23.855Z',
      level: 'info',
      source: 'UKG-System',
      message: 'UKG system initialization completed successfully',
      details: {
        version: '1.0.0',
        activeLayers: [1, 2, 3, 4, 5, 7],
        confidence: 0.97
      }
    },
    {
      id: 2,
      timestamp: '2025-05-19T21:15:27.233Z',
      level: 'info',
      source: 'UKG-MemoryManager',
      message: 'Structured memory initialized with 2048MB allocation',
      details: {
        memoryType: 'structured',
        allocation: '2048MB',
        status: 'active'
      }
    },
    {
      id: 3,
      timestamp: '2025-05-19T21:16:45.123Z',
      level: 'warning',
      source: 'UKG-Layer7',
      message: 'AGI System activating additional reasoning paths due to ambiguity',
      details: {
        confidence: 0.82,
        paths: 3,
        ambiguityScore: 0.32
      }
    },
    {
      id: 4,
      timestamp: '2025-05-19T21:17:12.567Z',
      level: 'error',
      source: 'UKG-Layer8',
      message: 'Quantum simulation failed due to resource constraints',
      details: {
        requestedQubits: 24,
        availableQubits: 16,
        errorCode: 'RESOURCE_LIMIT'
      }
    },
    {
      id: 5,
      timestamp: '2025-05-19T21:18:35.789Z',
      level: 'info',
      source: 'UKG-GatekeeperAgent',
      message: 'Access granted to Layer 7 for query processing',
      details: {
        query: 'Complex regulatory analysis for healthcare AI',
        confidenceThreshold: 0.85,
        accessGranted: true
      }
    },
    {
      id: 6,
      timestamp: '2025-05-19T21:20:42.123Z',
      level: 'debug',
      source: 'UKG-KnowledgeGraph',
      message: 'Node traversal completed with 42 nodes accessed',
      details: {
        startNode: 'PL25.3.2',
        endNode: 'PL40.7.9',
        traversalTime: '127ms',
        nodesAccessed: 42
      }
    },
    {
      id: 7,
      timestamp: '2025-05-19T21:23:15.456Z',
      level: 'info',
      source: 'UKG-QuadPersona',
      message: 'Quad Persona simulation completed with high confidence',
      details: {
        personas: ['Knowledge Expert', 'Sector Expert', 'Regulatory Expert', 'Compliance Expert'],
        confidence: 0.96,
        consensusReached: true
      }
    },
    {
      id: 8,
      timestamp: '2025-05-19T21:25:30.789Z',
      level: 'warning',
      source: 'UKG-Layer9',
      message: 'Recursive processing approaching depth limit',
      details: {
        currentDepth: 7,
        maxDepth: 10,
        processingTime: '3.2s'
      }
    },
    {
      id: 9,
      timestamp: '2025-05-19T21:29:23.855Z',
      level: 'info',
      source: 'UKG-Compliance',
      message: 'Compliance event check: Routine security check completed',
      details: {
        checkType: 'security',
        status: 'passed',
        findings: 0
      }
    },
    {
      id: 10,
      timestamp: '2025-05-19T21:34:23.857Z',
      level: 'info',
      source: 'UKG-Security',
      message: 'Security scan completed: 0 vulnerabilities, 1 warning',
      details: {
        vulnerabilities: 0,
        warnings: 1,
        scanDuration: '22s'
      }
    }
  ]);
  
  const [simulationLogs, setSimulationLogs] = useState([
    {
      id: 1,
      timestamp: '2025-05-19T21:15:30.123Z',
      level: 'info',
      source: 'SimulationEngine',
      message: 'Simulation initialized with parameters: confidence=0.9, maxLayers=7',
      details: {
        parameters: {
          confidence: 0.9,
          maxLayers: 7,
          refinementSteps: 12
        }
      }
    },
    {
      id: 2,
      timestamp: '2025-05-19T21:15:35.456Z',
      level: 'info',
      source: 'Layer1',
      message: 'Query received: "Analyze regulatory requirements for AI in healthcare"',
      details: {
        query: 'Analyze regulatory requirements for AI in healthcare',
        parsedIntent: 'REGULATORY_ANALYSIS',
        confidenceScore: 0.98
      }
    },
    {
      id: 3,
      timestamp: '2025-05-19T21:15:40.789Z',
      level: 'info',
      source: 'Layer2',
      message: 'Knowledge retrieval activated, accessing nodes PL20, PL40',
      details: {
        accessedNodes: ['PL20.3.1', 'PL20.5.2', 'PL40.2.1', 'PL40.3.7'],
        retrievalTime: '0.8s'
      }
    },
    {
      id: 4,
      timestamp: '2025-05-19T21:15:45.123Z',
      level: 'debug',
      source: 'QuadPersona',
      message: 'Activating Knowledge Expert persona for initial analysis',
      details: {
        activePersona: 'Knowledge Expert',
        attributes: {
          expertise: 'Healthcare Regulations',
          confidence: 0.92
        }
      }
    },
    {
      id: 5,
      timestamp: '2025-05-19T21:15:50.456Z',
      level: 'info',
      source: 'Layer3',
      message: 'Research agents deployed to gather FDA and HIPAA regulations',
      details: {
        agents: ['FDARegulationsAgent', 'HIPAAComplianceAgent'],
        status: 'active',
        priority: 'high'
      }
    },
    {
      id: 6,
      timestamp: '2025-05-19T21:16:00.789Z',
      level: 'info',
      source: 'Layer4',
      message: 'POV Engine activated to analyze multiple regulatory perspectives',
      details: {
        perspectives: ['Regulator', 'Healthcare Provider', 'AI Developer', 'Patient'],
        conflictDetection: true
      }
    },
    {
      id: 7,
      timestamp: '2025-05-19T21:16:20.123Z',
      level: 'warning',
      source: 'Layer5',
      message: 'Integration complexity high: multiple overlapping regulations detected',
      details: {
        complexityScore: 0.78,
        overlappingRegulations: ['FDA_SaMD', 'HIPAA_Privacy', 'GDPR_Article22'],
        resolution: 'applying conflict resolution rules'
      }
    },
    {
      id: 8,
      timestamp: '2025-05-19T21:16:40.456Z',
      level: 'info',
      source: 'Layer7',
      message: 'AGI system analyzing regulatory framework with multi-pass processing',
      details: {
        passes: 3,
        confidenceGain: '0.07',
        currentConfidence: 0.89
      }
    },
    {
      id: 9,
      timestamp: '2025-05-19T21:17:10.789Z',
      level: 'error',
      source: 'Layer8',
      message: 'Quantum simulation failed: unable to simulate full regulation space',
      details: {
        errorType: 'RESOURCE_LIMITATION',
        fallbackStrategy: 'using Layer 7 results',
        impact: 'reduced confidence in ambiguous areas'
      }
    },
    {
      id: 10,
      timestamp: '2025-05-19T21:17:30.123Z',
      level: 'info',
      source: 'RefinementEngine',
      message: 'Starting 12-step refinement process for regulatory analysis',
      details: {
        currentStep: 1,
        stepName: 'Initial Analysis',
        progress: '8%'
      }
    },
    {
      id: 11,
      timestamp: '2025-05-19T21:19:45.456Z',
      level: 'info',
      source: 'RefinementEngine',
      message: 'Refinement step 12 complete: Final Synthesis',
      details: {
        finalConfidence: 0.96,
        conflictsResolved: 3,
        outputReady: true
      }
    },
    {
      id: 12,
      timestamp: '2025-05-19T21:20:00.789Z',
      level: 'info',
      source: 'SimulationEngine',
      message: 'Simulation completed successfully',
      details: {
        duration: '4m 30s',
        confidenceScore: 0.96,
        layersUsed: [1, 2, 3, 4, 5, 7],
        memorySummary: {
          nodesAccessed: 127,
          edgesTraversed: 312,
          memoryCached: '156MB'
        }
      }
    }
  ]);
  
  const [userLogs, setUserLogs] = useState([
    {
      id: 1,
      timestamp: '2025-05-19T20:45:12.123Z',
      level: 'info',
      source: 'AuthSystem',
      message: 'User john.doe@example.com logged in successfully',
      details: {
        userId: 'user123',
        ipAddress: '192.168.1.105',
        authMethod: 'SSO'
      }
    },
    {
      id: 2,
      timestamp: '2025-05-19T20:46:30.456Z',
      level: 'info',
      source: 'ChatInterface',
      message: 'User started new conversation "Healthcare Regulatory Analysis"',
      details: {
        conversationId: 'conv789',
        sessionId: 'sess456',
        type: 'regulatory_analysis'
      }
    },
    {
      id: 3,
      timestamp: '2025-05-19T20:47:15.789Z',
      level: 'info',
      source: 'QueryProcessor',
      message: 'User submitted query "What are the key FDA regulations for AI-based medical diagnosis tools?"',
      details: {
        queryId: 'q12345',
        processingTime: '3.2s',
        simulated: true
      }
    },
    {
      id: 4,
      timestamp: '2025-05-19T20:55:42.123Z',
      level: 'warning',
      source: 'UserPreferences',
      message: 'User attempted to access Layer 8 features without proper permissions',
      details: {
        accessAttempt: 'Layer8_QuantumSimulation',
        requiredRole: 'advanced_user',
        userRole: 'standard_user'
      }
    },
    {
      id: 5,
      timestamp: '2025-05-19T21:05:23.456Z',
      level: 'info',
      source: 'MediaStudio',
      message: 'User generated image "Regulatory compliance framework visualization"',
      details: {
        mediaId: 'img456',
        mediaType: 'image',
        size: '1024x1024',
        stored: true
      }
    },
    {
      id: 6,
      timestamp: '2025-05-19T21:15:10.789Z',
      level: 'info',
      source: 'ProjectMode',
      message: 'User created new project "Healthcare AI Compliance Framework"',
      details: {
        projectId: 'proj123',
        template: 'regulatory_framework',
        objectives: 3
      }
    },
    {
      id: 7,
      timestamp: '2025-05-19T21:25:35.123Z',
      level: 'info',
      source: 'AuthSystem',
      message: 'User logged out',
      details: {
        sessionDuration: '40m 23s',
        reason: 'user_initiated'
      }
    }
  ]);
  
  // Filtered logs based on search and filter
  const getFilteredLogs = (logs) => {
    let filteredLogs = [...logs];
    
    // Apply level filter
    if (filterLevel !== 'all') {
      filteredLogs = filteredLogs.filter(log => log.level === filterLevel);
    }
    
    // Apply search filter
    if (searchQuery.trim() !== '') {
      const query = searchQuery.toLowerCase();
      filteredLogs = filteredLogs.filter(log => 
        log.message.toLowerCase().includes(query) ||
        log.source.toLowerCase().includes(query) ||
        JSON.stringify(log.details).toLowerCase().includes(query)
      );
    }
    
    // Apply time range filter
    const now = new Date();
    let timeFilterMs = 0;
    
    switch (timeRange) {
      case '1h':
        timeFilterMs = 60 * 60 * 1000; // 1 hour in milliseconds
        break;
      case '6h':
        timeFilterMs = 6 * 60 * 60 * 1000; // 6 hours in milliseconds
        break;
      case '24h':
        timeFilterMs = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
        break;
      case '7d':
        timeFilterMs = 7 * 24 * 60 * 60 * 1000; // 7 days in milliseconds
        break;
      default:
        timeFilterMs = 0; // All time
    }
    
    if (timeFilterMs > 0) {
      const cutoffTime = new Date(now.getTime() - timeFilterMs);
      filteredLogs = filteredLogs.filter(log => new Date(log.timestamp) > cutoffTime);
    }
    
    return filteredLogs;
  };
  
  // Format timestamp
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString([], {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };
  
  // Get badge color based on log level
  const getLevelBadgeColor = (level) => {
    switch (level) {
      case 'error': return 'red';
      case 'warning': return 'yellow';
      case 'info': return 'blue';
      case 'debug': return 'gray';
      case 'success': return 'green';
      default: return 'gray';
    }
  };
  
  // Get icon based on log level
  const getLevelIcon = (level) => {
    switch (level) {
      case 'error': return <FiAlertCircle />;
      case 'warning': return <FiInfo />;
      case 'info': return <FiInfo />;
      case 'debug': return <FiActivity />;
      case 'success': return <FiCheckCircle />;
      default: return <FiInfo />;
    }
  };
  
  // Download logs
  const downloadLogs = () => {
    let logsToDownload = [];
    
    switch (activeTab) {
      case 'system':
        logsToDownload = systemLogs;
        break;
      case 'simulation':
        logsToDownload = simulationLogs;
        break;
      case 'user':
        logsToDownload = userLogs;
        break;
      default:
        logsToDownload = systemLogs;
    }
    
    const jsonData = JSON.stringify(logsToDownload, null, 2);
    const blob = new Blob([jsonData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `ukg-${activeTab}-logs-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    
    toast({
      title: 'Logs Downloaded',
      description: `${activeTab} logs have been downloaded as JSON`,
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };
  
  // Clear logs
  const clearLogs = () => {
    toast({
      title: 'Logs Cleared',
      description: `${activeTab} logs have been cleared`,
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
    
    switch (activeTab) {
      case 'system':
        setSystemLogs([]);
        break;
      case 'simulation':
        setSimulationLogs([]);
        break;
      case 'user':
        setUserLogs([]);
        break;
      default:
        break;
    }
  };
  
  // Auto-refresh effect
  useEffect(() => {
    let intervalId = null;
    
    if (autoRefresh) {
      intervalId = setInterval(() => {
        // Simulate refreshing logs by adding a new log entry
        const newLog = {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          level: ['info', 'debug', 'warning', 'error'][Math.floor(Math.random() * 4)],
          source: 'UKG-AutoRefresh',
          message: `Auto-refreshed log entry at ${new Date().toLocaleTimeString()}`,
          details: {
            refreshInterval: `${refreshInterval}s`,
            autoGenerated: true
          }
        };
        
        switch (activeTab) {
          case 'system':
            setSystemLogs(prevLogs => [newLog, ...prevLogs]);
            break;
          case 'simulation':
            setSimulationLogs(prevLogs => [newLog, ...prevLogs]);
            break;
          case 'user':
            setUserLogs(prevLogs => [newLog, ...prevLogs]);
            break;
          default:
            break;
        }
      }, refreshInterval * 1000);
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [autoRefresh, refreshInterval, activeTab]);
  
  return (
    <Box h="100%">
      <Flex mb={6} justify="space-between" align="center">
        <Heading size="lg">System Logs</Heading>
        
        <HStack>
          <Menu>
            <MenuButton
              as={Button}
              rightIcon={<FiSettings />}
              variant="outline"
              size="sm"
            >
              Log Settings
            </MenuButton>
            <MenuList>
              <MenuItem onClick={() => setFilterLevel('all')}>Show All Levels</MenuItem>
              <MenuItem onClick={() => setFilterLevel('error')}>Show Errors Only</MenuItem>
              <MenuItem onClick={() => setFilterLevel('warning')}>Show Warnings & Errors</MenuItem>
              <Divider />
              <Box px={3} py={2}>
                <FormControl display="flex" alignItems="center">
                  <FormLabel htmlFor="auto-refresh" mb="0" fontSize="sm">
                    Auto-refresh
                  </FormLabel>
                  <Switch
                    id="auto-refresh"
                    isChecked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    colorScheme="brand"
                  />
                </FormControl>
              </Box>
              <Box px={3} py={2}>
                <FormControl>
                  <FormLabel fontSize="sm">Refresh Interval (seconds)</FormLabel>
                  <Select 
                    size="sm" 
                    value={refreshInterval}
                    onChange={(e) => setRefreshInterval(Number(e.target.value))}
                    isDisabled={!autoRefresh}
                  >
                    <option value={10}>10 seconds</option>
                    <option value={30}>30 seconds</option>
                    <option value={60}>1 minute</option>
                    <option value={300}>5 minutes</option>
                  </Select>
                </FormControl>
              </Box>
              <Divider />
              <MenuItem onClick={clearLogs} icon={<FiTrash2 />} color="red.500">
                Clear Logs
              </MenuItem>
            </MenuList>
          </Menu>
          
          <Button
            leftIcon={<FiDownload />}
            onClick={downloadLogs}
            size="sm"
          >
            Download Logs
          </Button>
          
          <IconButton
            aria-label="Refresh logs"
            icon={<FiRefreshCw />}
            onClick={() => {
              toast({
                title: 'Logs Refreshed',
                status: 'info',
                duration: 2000,
                isClosable: true,
              });
            }}
            size="sm"
          />
        </HStack>
      </Flex>
      
      <Card bg="dark.700" mb={6}>
        <CardBody>
          <HStack spacing={4} justify="space-between">
            <InputGroup maxW="400px">
              <Input
                placeholder="Search logs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                bg="dark.800"
              />
              <InputRightElement>
                <FiSearch />
              </InputRightElement>
            </InputGroup>
            
            <HStack spacing={4}>
              <Select
                value={filterLevel}
                onChange={(e) => setFilterLevel(e.target.value)}
                maxW="150px"
                bg="dark.800"
              >
                <option value="all">All Levels</option>
                <option value="error">Error</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
                <option value="debug">Debug</option>
              </Select>
              
              <Select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                maxW="150px"
                bg="dark.800"
              >
                <option value="1h">Last Hour</option>
                <option value="6h">Last 6 Hours</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="all">All Time</option>
              </Select>
              
              <IconButton
                aria-label="Advanced filters"
                icon={<FiFilter />}
                variant="outline"
                onClick={() => {
                  toast({
                    title: 'Advanced Filters',
                    description: 'Advanced filtering options would be available here',
                    status: 'info',
                    duration: 2000,
                    isClosable: true,
                  });
                }}
              />
            </HStack>
          </HStack>
        </CardBody>
      </Card>
      
      <Tabs
        variant="soft-rounded"
        colorScheme="brand"
        isFitted
        mb={4}
        index={activeTab === 'system' ? 0 : activeTab === 'simulation' ? 1 : 2}
        onChange={(index) => setActiveTab(index === 0 ? 'system' : index === 1 ? 'simulation' : 'user')}
      >
        <TabList>
          <Tab><HStack><FiServer /><Text>System Logs</Text></HStack></Tab>
          <Tab><HStack><FiCpu /><Text>Simulation Logs</Text></HStack></Tab>
          <Tab><HStack><FiLayers /><Text>User Activity</Text></HStack></Tab>
        </TabList>
        
        <TabPanels>
          {/* System Logs Tab */}
          <TabPanel p={0} mt={4}>
            <Card bg="dark.700" variant="outline" mb={3}>
              <CardBody p={0}>
                <Box overflowX="auto">
                  <Table variant="simple" size="sm">
                    <Thead>
                      <Tr>
                        <Th>Timestamp</Th>
                        <Th>Level</Th>
                        <Th>Source</Th>
                        <Th>Message</Th>
                        <Th>Actions</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {getFilteredLogs(systemLogs).map((log) => (
                        <Tr key={log.id} _hover={{ bg: 'dark.600' }}>
                          <Td whiteSpace="nowrap">
                            <HStack spacing={2}>
                              <FiClock size={14} />
                              <Text fontSize="xs">{formatTimestamp(log.timestamp)}</Text>
                            </HStack>
                          </Td>
                          <Td>
                            <Badge colorScheme={getLevelBadgeColor(log.level)}>
                              <HStack spacing={1}>
                                {getLevelIcon(log.level)}
                                <Text>{log.level}</Text>
                              </HStack>
                            </Badge>
                          </Td>
                          <Td>{log.source}</Td>
                          <Td>{log.message}</Td>
                          <Td>
                            <IconButton
                              aria-label="View log details"
                              icon={<FiInfo />}
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                toast({
                                  title: 'Log Details',
                                  description: 'Details would be displayed in a modal',
                                  status: 'info',
                                  duration: 2000,
                                  isClosable: true,
                                });
                              }}
                            />
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              </CardBody>
            </Card>
            
            <Text fontSize="sm" color="gray.500">
              Showing {getFilteredLogs(systemLogs).length} of {systemLogs.length} system logs
            </Text>
          </TabPanel>
          
          {/* Simulation Logs Tab */}
          <TabPanel p={0} mt={4}>
            <Card bg="dark.700" variant="outline" mb={3}>
              <CardBody p={0}>
                <Box overflowX="auto">
                  <Table variant="simple" size="sm">
                    <Thead>
                      <Tr>
                        <Th>Timestamp</Th>
                        <Th>Level</Th>
                        <Th>Source</Th>
                        <Th>Message</Th>
                        <Th>Actions</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {getFilteredLogs(simulationLogs).map((log) => (
                        <Tr key={log.id} _hover={{ bg: 'dark.600' }}>
                          <Td whiteSpace="nowrap">
                            <HStack spacing={2}>
                              <FiClock size={14} />
                              <Text fontSize="xs">{formatTimestamp(log.timestamp)}</Text>
                            </HStack>
                          </Td>
                          <Td>
                            <Badge colorScheme={getLevelBadgeColor(log.level)}>
                              <HStack spacing={1}>
                                {getLevelIcon(log.level)}
                                <Text>{log.level}</Text>
                              </HStack>
                            </Badge>
                          </Td>
                          <Td>{log.source}</Td>
                          <Td>{log.message}</Td>
                          <Td>
                            <IconButton
                              aria-label="View log details"
                              icon={<FiInfo />}
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                toast({
                                  title: 'Log Details',
                                  description: 'Details would be displayed in a modal',
                                  status: 'info',
                                  duration: 2000,
                                  isClosable: true,
                                });
                              }}
                            />
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              </CardBody>
            </Card>
            
            <Text fontSize="sm" color="gray.500">
              Showing {getFilteredLogs(simulationLogs).length} of {simulationLogs.length} simulation logs
            </Text>
          </TabPanel>
          
          {/* User Activity Tab */}
          <TabPanel p={0} mt={4}>
            <Card bg="dark.700" variant="outline" mb={3}>
              <CardBody p={0}>
                <Box overflowX="auto">
                  <Table variant="simple" size="sm">
                    <Thead>
                      <Tr>
                        <Th>Timestamp</Th>
                        <Th>Level</Th>
                        <Th>Source</Th>
                        <Th>Message</Th>
                        <Th>Actions</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {getFilteredLogs(userLogs).map((log) => (
                        <Tr key={log.id} _hover={{ bg: 'dark.600' }}>
                          <Td whiteSpace="nowrap">
                            <HStack spacing={2}>
                              <FiClock size={14} />
                              <Text fontSize="xs">{formatTimestamp(log.timestamp)}</Text>
                            </HStack>
                          </Td>
                          <Td>
                            <Badge colorScheme={getLevelBadgeColor(log.level)}>
                              <HStack spacing={1}>
                                {getLevelIcon(log.level)}
                                <Text>{log.level}</Text>
                              </HStack>
                            </Badge>
                          </Td>
                          <Td>{log.source}</Td>
                          <Td>{log.message}</Td>
                          <Td>
                            <IconButton
                              aria-label="View log details"
                              icon={<FiInfo />}
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                toast({
                                  title: 'Log Details',
                                  description: 'Details would be displayed in a modal',
                                  status: 'info',
                                  duration: 2000,
                                  isClosable: true,
                                });
                              }}
                            />
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              </CardBody>
            </Card>
            
            <Text fontSize="sm" color="gray.500">
              Showing {getFilteredLogs(userLogs).length} of {userLogs.length} user activity logs
            </Text>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};

export default LogsPage;