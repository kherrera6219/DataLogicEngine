import React, { useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Input,
  Button,
  Flex,
  Card,
  CardBody,
  CardHeader,
  Divider,
  List,
  ListItem,
  ListIcon,
  OrderedList,
  Badge,
  IconButton,
  Textarea,
  useToast,
  Progress,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Tag,
  Select
} from '@chakra-ui/react';
import {
  FiCheckCircle,
  FiAlertCircle,
  FiPlus,
  FiTrash2,
  FiEdit,
  FiRefreshCw,
  FiMoreVertical,
  FiPlay,
  FiPause,
  FiCheck,
  FiX,
  FiInfo,
  FiFolder,
  FiTag,
  FiCpu
} from 'react-icons/fi';

const ProjectPage = () => {
  const toast = useToast();
  const [objective, setObjective] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [projectProgress, setProjectProgress] = useState(0);
  const [agentName, setAgentName] = useState('GatekeeperAI');
  
  // Task management state
  const [tasks, setTasks] = useState([
    {
      id: 1,
      description: 'Define project scope',
      status: 'completed',
      result: 'Project scope defined as creating a comprehensive analysis of regulatory requirements for AI systems in healthcare.',
      confidence: 0.96,
      timestamp: '2025-05-19T14:23:45Z'
    },
    {
      id: 2,
      description: 'Identify key stakeholders',
      status: 'completed',
      result: 'Key stakeholders identified: FDA, healthcare providers, AI developers, patients, and compliance officers.',
      confidence: 0.92,
      timestamp: '2025-05-19T14:25:12Z'
    },
    {
      id: 3,
      description: 'Research FDA regulations related to AI in healthcare',
      status: 'in-progress',
      subTasks: [
        { id: 31, description: 'Review FDA guidance on Software as Medical Device (SaMD)', status: 'completed' },
        { id: 32, description: 'Analyze premarket notification requirements', status: 'in-progress' },
        { id: 33, description: 'Investigate clinical validation requirements', status: 'pending' }
      ],
      confidence: 0.87,
      timestamp: '2025-05-19T14:28:33Z'
    },
    {
      id: 4, 
      description: 'Map regulatory requirements to software development lifecycle',
      status: 'pending',
      confidence: null,
      timestamp: '2025-05-19T14:30:45Z'
    }
  ]);
  
  // Simulation state
  const [simulationLogs, setSimulationLogs] = useState([
    { timestamp: '2025-05-19T14:22:30Z', level: 'info', message: 'Project simulation initialized' },
    { timestamp: '2025-05-19T14:22:35Z', level: 'info', message: 'GatekeeperAI assigned as primary agent' },
    { timestamp: '2025-05-19T14:23:40Z', level: 'info', message: 'Layer 3 activated for research capabilities' },
    { timestamp: '2025-05-19T14:23:45Z', level: 'success', message: 'Task 1 completed with 96% confidence' },
    { timestamp: '2025-05-19T14:25:12Z', level: 'success', message: 'Task 2 completed with 92% confidence' },
    { timestamp: '2025-05-19T14:26:03Z', level: 'info', message: 'Layer 7 activated for complex reasoning' },
    { timestamp: '2025-05-19T14:27:15Z', level: 'info', message: 'Accessing regulatory knowledge from Universal Knowledge Graph' },
    { timestamp: '2025-05-19T14:28:33Z', level: 'info', message: 'Task 3 started - Research initiated' },
    { timestamp: '2025-05-19T14:30:10Z', level: 'warning', message: 'Confidence below threshold (0.87), initiating Layer 8 quantum simulation' }
  ]);
  
  // Start project simulation
  const handleStartProject = () => {
    if (!objective.trim()) {
      toast({
        title: "Objective Required",
        description: "Please enter a project objective to start simulation.",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    setIsRunning(true);
    setProjectProgress(10);
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      setProjectProgress(prev => {
        const newProgress = prev + Math.random() * 5;
        if (newProgress >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return newProgress;
      });
    }, 3000);
    
    // Generate new task every 5 seconds
    const taskInterval = setInterval(() => {
      if (projectProgress < 90) {
        addNewSimulatedTask();
      } else {
        clearInterval(taskInterval);
      }
    }, 5000);
    
    toast({
      title: "Project Started",
      description: `Starting project with objective: ${objective}`,
      status: "success",
      duration: 3000,
      isClosable: true,
    });
  };
  
  // Stop project simulation
  const handleStopProject = () => {
    setIsRunning(false);
    
    toast({
      title: "Project Paused",
      description: "You can resume the project at any time.",
      status: "info",
      duration: 3000,
      isClosable: true,
    });
  };
  
  // Add a new simulated task
  const addNewSimulatedTask = () => {
    const taskTemplates = [
      "Analyze compliance requirements for data privacy",
      "Prepare documentation templates for regulatory submission",
      "Create traceability matrix for requirements",
      "Define verification and validation protocols",
      "Map technical specifications to regulatory standards",
      "Develop risk management framework",
      "Create standard operating procedures for compliance monitoring"
    ];
    
    const randomTask = taskTemplates[Math.floor(Math.random() * taskTemplates.length)];
    const newTask = {
      id: tasks.length + 1,
      description: randomTask,
      status: 'in-progress',
      confidence: Math.random() * 0.15 + 0.8, // Random confidence between 0.8 and 0.95
      timestamp: new Date().toISOString()
    };
    
    setTasks(prevTasks => [...prevTasks, newTask]);
    
    // Add log entry
    const newLog = {
      timestamp: new Date().toISOString(),
      level: 'info',
      message: `New task created: ${randomTask}`
    };
    
    setSimulationLogs(prevLogs => [...prevLogs, newLog]);
    
    // Simulate task completion in 10 seconds
    setTimeout(() => {
      setTasks(prevTasks => 
        prevTasks.map(task => 
          task.id === newTask.id 
            ? {
                ...task, 
                status: 'completed',
                result: `Completed analysis of ${randomTask.toLowerCase()} with comprehensive documentation.`
              } 
            : task
        )
      );
      
      // Add completion log
      const completionLog = {
        timestamp: new Date().toISOString(),
        level: 'success',
        message: `Task "${randomTask}" completed with ${(newTask.confidence * 100).toFixed(1)}% confidence`
      };
      
      setSimulationLogs(prevLogs => [...prevLogs, completionLog]);
    }, 10000);
  };
  
  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };
  
  return (
    <Box h="100%" display="flex" flexDirection="column">
      <HStack mb={6} justify="space-between">
        <Text fontSize="2xl" fontWeight="bold">Project Mode (AgentGPT)</Text>
        
        <HStack>
          <Select 
            value={agentName} 
            onChange={(e) => setAgentName(e.target.value)}
            size="sm" 
            width="200px"
            bg="dark.900"
          >
            <option value="GatekeeperAI">GatekeeperAI</option>
            <option value="AlexMorgan">AlexMorgan</option>
            <option value="RegulatorAI">RegulatorAI</option>
            <option value="ComplianceExpert">ComplianceExpert</option>
          </Select>
          
          {isRunning ? (
            <Button
              leftIcon={<FiPause />}
              colorScheme="orange"
              size="sm"
              onClick={handleStopProject}
            >
              Pause Project
            </Button>
          ) : (
            <Button
              leftIcon={<FiPlay />}
              colorScheme="green"
              size="sm"
              onClick={handleStartProject}
              isDisabled={!objective.trim()}
            >
              Start Project
            </Button>
          )}
        </HStack>
      </HStack>
      
      {/* Project Configuration & Display */}
      <Flex flex="1" gap={4}>
        {/* Left Panel - Project Definition & Status */}
        <Card flex="3" bg="dark.700" variant="outline">
          <CardHeader pb={2}>
            <Text fontWeight="bold" fontSize="lg">Project Definition</Text>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              {/* Objective Setting */}
              <Box>
                <Text mb={2} fontWeight="semibold">Objective</Text>
                <Textarea
                  placeholder="Enter a project objective for the UKG System to work on..."
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  isDisabled={isRunning}
                  bg="dark.800"
                  mb={3}
                  resize="none"
                  rows={3}
                />
                
                {/* Only shown when not running */}
                {!isRunning && (
                  <Text fontSize="sm" color="gray.400">
                    The Universal Knowledge Graph system will break down this objective into actionable tasks and work through them autonomously.
                  </Text>
                )}
              </Box>
              
              {/* If running - show progress */}
              {isRunning && (
                <Box>
                  <HStack mb={1} justify="space-between">
                    <Text fontWeight="semibold">Project Progress</Text>
                    <Text>{projectProgress.toFixed(0)}%</Text>
                  </HStack>
                  <Progress 
                    value={projectProgress} 
                    size="sm" 
                    colorScheme="brand" 
                    borderRadius="md" 
                    hasStripe
                    isAnimated
                  />
                  
                  <HStack mt={3} spacing={4}>
                    <Box>
                      <Text fontSize="sm" color="gray.400">Agent</Text>
                      <Text fontWeight="semibold">{agentName}</Text>
                    </Box>
                    <Box>
                      <Text fontSize="sm" color="gray.400">Active Layers</Text>
                      <HStack mt={1} spacing={1}>
                        {[1, 2, 3, 7].map(layer => (
                          <Badge key={layer} colorScheme="green" size="sm">L{layer}</Badge>
                        ))}
                      </HStack>
                    </Box>
                    <Box>
                      <Text fontSize="sm" color="gray.400">Tasks</Text>
                      <Text fontWeight="semibold">
                        {tasks.filter(t => t.status === 'completed').length} / {tasks.length}
                      </Text>
                    </Box>
                  </HStack>
                </Box>
              )}
            </VStack>
          </CardBody>
        </Card>
        
        {/* Right Panel - Tasks List */}
        <Card flex="4" bg="dark.700" variant="outline">
          <CardHeader pb={0}>
            <Tabs variant="soft-rounded" colorScheme="brand" size="sm">
              <TabList>
                <Tab>Tasks</Tab>
                <Tab>Simulation Logs</Tab>
                <Tab>Results</Tab>
              </TabList>
              
              <TabPanels>
                <TabPanel p={4}>
                  {/* Tasks List */}
                  <List spacing={3}>
                    {tasks.map((task) => (
                      <Card 
                        key={task.id} 
                        variant="outline" 
                        bg={task.status === 'completed' ? 'green.900' : 
                           task.status === 'in-progress' ? 'blue.900' : 'gray.700'}
                        opacity={task.status === 'pending' ? 0.7 : 1}
                        borderWidth="1px"
                        borderColor={task.status === 'completed' ? 'green.500' : 
                                   task.status === 'in-progress' ? 'blue.500' : 'gray.600'}
                      >
                        <CardBody py={3}>
                          <HStack justify="space-between" mb={task.result ? 2 : 0}>
                            <HStack>
                              <Box mr={2}>
                                {task.status === 'completed' && <FiCheckCircle color="green" />}
                                {task.status === 'in-progress' && <FiCpu color="blue" />}
                                {task.status === 'pending' && <FiInfo color="gray" />}
                              </Box>
                              <Text fontWeight="semibold">{task.description}</Text>
                            </HStack>
                            
                            {task.confidence && (
                              <Badge colorScheme={task.confidence > 0.9 ? "green" : "yellow"}>
                                {(task.confidence * 100).toFixed(0)}%
                              </Badge>
                            )}
                          </HStack>
                          
                          {task.result && (
                            <Box ml={8} fontSize="sm" color="gray.300">
                              {task.result}
                            </Box>
                          )}
                          
                          {task.subTasks && (
                            <Box ml={8} mt={2}>
                              <Text fontSize="sm" color="gray.400" mb={1}>Subtasks:</Text>
                              <List spacing={1}>
                                {task.subTasks.map(subTask => (
                                  <ListItem key={subTask.id} fontSize="sm">
                                    <HStack>
                                      <Box>
                                        {subTask.status === 'completed' && <FiCheck size={12} color="green" />}
                                        {subTask.status === 'in-progress' && <FiCpu size={12} color="blue" />}
                                        {subTask.status === 'pending' && <FiInfo size={12} color="gray" />}
                                      </Box>
                                      <Text>{subTask.description}</Text>
                                    </HStack>
                                  </ListItem>
                                ))}
                              </List>
                            </Box>
                          )}
                          
                          {task.timestamp && (
                            <Text fontSize="xs" color="gray.500" mt={1} textAlign="right">
                              {formatTime(task.timestamp)}
                            </Text>
                          )}
                        </CardBody>
                      </Card>
                    ))}
                  </List>
                </TabPanel>
                
                <TabPanel p={4}>
                  {/* Simulation Logs */}
                  <List spacing={1}>
                    {simulationLogs.map((log, idx) => (
                      <ListItem key={idx}>
                        <HStack fontSize="sm" spacing={2}>
                          <Text color="gray.500" fontFamily="monospace">
                            {formatTime(log.timestamp)}
                          </Text>
                          <Badge 
                            colorScheme={
                              log.level === 'info' ? 'blue' : 
                              log.level === 'success' ? 'green' : 
                              log.level === 'warning' ? 'yellow' : 
                              log.level === 'error' ? 'red' : 'gray'
                            }
                          >
                            {log.level}
                          </Badge>
                          <Text flex="1">{log.message}</Text>
                        </HStack>
                      </ListItem>
                    ))}
                  </List>
                </TabPanel>
                
                <TabPanel p={4}>
                  {/* Results Panel - shows summary of project */}
                  <VStack align="stretch" spacing={4}>
                    <Text>Project results will appear here when the autonomous agents complete their tasks.</Text>
                    
                    {projectProgress >= 50 && (
                      <Card variant="outline" bg="dark.800">
                        <CardBody>
                          <Text fontWeight="semibold" mb={2}>Interim Project Report</Text>
                          <Text fontSize="sm" mb={3}>
                            The UKG system has identified key regulatory requirements for AI in healthcare. The project has analyzed FDA guidelines, identified stakeholder needs, and begun mapping compliance frameworks.
                          </Text>
                          
                          <Text fontWeight="semibold" fontSize="sm" mb={1}>Key Findings:</Text>
                          <UnorderedList fontSize="sm" spacing={1} pl={4}>
                            <ListItem>FDA categorizes AI healthcare solutions under Software as Medical Device (SaMD) framework</ListItem>
                            <ListItem>Premarket notification pathways depend on risk classification</ListItem>
                            <ListItem>Continuous learning systems require specialized validation approaches</ListItem>
                            <ListItem>Data privacy requirements span multiple regulatory domains (HIPAA, GDPR for EU markets)</ListItem>
                          </UnorderedList>
                        </CardBody>
                      </Card>
                    )}
                  </VStack>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </CardHeader>
        </Card>
      </Flex>
    </Box>
  );
};

// Helper component for list rendering
const UnorderedList = ({ children, ...props }) => (
  <List spacing={2} {...props}>
    {React.Children.map(children, (child) => (
      <ListItem display="flex">
        <ListIcon as={FiCheckCircle} color="green.500" mt="5px" />
        <Box>{child}</Box>
      </ListItem>
    ))}
  </List>
);

export default ProjectPage;