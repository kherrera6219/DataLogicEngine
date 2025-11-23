import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  Button,
  VStack,
  HStack,
  Grid,
  GridItem,
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatGroup,
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
  IconButton,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Select,
  Code,
  Divider,
  Spinner,
  useDisclosure,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react';
import {
  FiServer,
  FiPlus,
  FiTrash2,
  FiRefreshCw,
  FiPlay,
  FiDatabase,
  FiTool,
  FiFileText,
  FiActivity,
  FiSettings,
  FiCpu,
} from 'react-icons/fi';
import axios from 'axios';

const MCPConsolePage = () => {
  const [servers, setServers] = useState([]);
  const [selectedServer, setSelectedServer] = useState(null);
  const [resources, setResources] = useState([]);
  const [tools, setTools] = useState([]);
  const [prompts, setPrompts] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [clients, setClients] = useState([]);

  const toast = useToast();
  const {
    isOpen: isCreateServerOpen,
    onOpen: onCreateServerOpen,
    onClose: onCreateServerClose,
  } = useDisclosure();
  const {
    isOpen: isToolCallOpen,
    onOpen: onToolCallOpen,
    onClose: onToolCallClose,
  } = useDisclosure();
  const {
    isOpen: isPromptGetOpen,
    onOpen: onPromptGetOpen,
    onClose: onPromptGetClose,
  } = useDisclosure();

  const [newServer, setNewServer] = useState({
    name: '',
    version: '1.0.0',
    description: '',
  });
  const [selectedTool, setSelectedTool] = useState(null);
  const [toolArguments, setToolArguments] = useState('{}');
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [promptArguments, setPromptArguments] = useState('{}');
  const [toolResult, setToolResult] = useState(null);
  const [promptResult, setPromptResult] = useState(null);

  // Fetch data on component mount
  useEffect(() => {
    fetchServers();
    fetchStats();
    fetchClients();
  }, []);

  // Fetch server details when selected
  useEffect(() => {
    if (selectedServer) {
      fetchServerDetails(selectedServer.server_id);
    }
  }, [selectedServer]);

  const fetchServers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/mcp/servers');
      setServers(response.data.servers || []);
    } catch (error) {
      toast({
        title: 'Error fetching servers',
        description: error.response?.data?.error || error.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchServerDetails = async (serverId) => {
    try {
      // Fetch resources
      const resourcesRes = await axios.get(`/api/mcp/servers/${serverId}/resources`);
      setResources(resourcesRes.data.resources || []);

      // Fetch tools
      const toolsRes = await axios.get(`/api/mcp/servers/${serverId}/tools`);
      setTools(toolsRes.data.tools || []);

      // Fetch prompts
      const promptsRes = await axios.get(`/api/mcp/servers/${serverId}/prompts`);
      setPrompts(promptsRes.data.prompts || []);
    } catch (error) {
      toast({
        title: 'Error fetching server details',
        description: error.response?.data?.error || error.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/mcp/stats');
      setStats(response.data.stats || {});
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await axios.get('/api/mcp/clients');
      setClients(response.data.clients || []);
    } catch (error) {
      console.error('Error fetching clients:', error);
    }
  };

  const handleCreateServer = async () => {
    try {
      const response = await axios.post('/api/mcp/servers', newServer);
      toast({
        title: 'Server created',
        description: `MCP server "${newServer.name}" created successfully`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      setNewServer({ name: '', version: '1.0.0', description: '' });
      onCreateServerClose();
      fetchServers();
    } catch (error) {
      toast({
        title: 'Error creating server',
        description: error.response?.data?.error || error.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleDeleteServer = async (serverId) => {
    if (!window.confirm('Are you sure you want to delete this server?')) return;

    try {
      await axios.delete(`/api/mcp/servers/${serverId}`);
      toast({
        title: 'Server deleted',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      if (selectedServer?.server_id === serverId) {
        setSelectedServer(null);
      }
      fetchServers();
    } catch (error) {
      toast({
        title: 'Error deleting server',
        description: error.response?.data?.error || error.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleSetupDefault = async () => {
    try {
      const response = await axios.post('/api/mcp/setup-default');
      toast({
        title: 'Default servers setup',
        description: 'Default MCP servers have been created successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      fetchServers();
    } catch (error) {
      toast({
        title: 'Error setting up defaults',
        description: error.response?.data?.error || error.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleCallTool = async () => {
    try {
      const args = JSON.parse(toolArguments);
      const response = await axios.post(
        `/api/mcp/servers/${selectedServer.server_id}/tools/${selectedTool.id}/call`,
        { arguments: args }
      );
      setToolResult(response.data.result);
      toast({
        title: 'Tool executed',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Error executing tool',
        description: error.response?.data?.error || error.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleGetPrompt = async () => {
    try {
      const args = JSON.parse(promptArguments);
      const response = await axios.post(
        `/api/mcp/servers/${selectedServer.server_id}/prompts/${selectedPrompt.id}/get`,
        { arguments: args }
      );
      setPromptResult(response.data.prompt);
      toast({
        title: 'Prompt generated',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Error getting prompt',
        description: error.response?.data?.error || error.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'green';
      case 'inactive':
        return 'gray';
      case 'error':
        return 'red';
      default:
        return 'gray';
    }
  };

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            <HStack>
              <FiServer />
              <Text>MCP Console</Text>
            </HStack>
          </Heading>
          <Text color="gray.600">
            Model Context Protocol - Server & Client Management
          </Text>
        </Box>

        {/* Stats */}
        <StatGroup>
          <Stat>
            <StatLabel>Active Servers</StatLabel>
            <StatNumber>{stats.active_servers || 0}</StatNumber>
            <StatHelpText>MCP Servers Running</StatHelpText>
          </Stat>
          <Stat>
            <StatLabel>Resources</StatLabel>
            <StatNumber>{stats.total_resources || 0}</StatNumber>
            <StatHelpText>Available Resources</StatHelpText>
          </Stat>
          <Stat>
            <StatLabel>Tools</StatLabel>
            <StatNumber>{stats.total_tools || 0}</StatNumber>
            <StatHelpText>Registered Tools</StatHelpText>
          </Stat>
          <Stat>
            <StatLabel>Prompts</StatLabel>
            <StatNumber>{stats.total_prompts || 0}</StatNumber>
            <StatHelpText>Prompt Templates</StatHelpText>
          </Stat>
        </StatGroup>

        {/* Action Buttons */}
        <HStack spacing={4}>
          <Button
            leftIcon={<FiPlus />}
            colorScheme="blue"
            onClick={onCreateServerOpen}
          >
            Create Server
          </Button>
          <Button
            leftIcon={<FiSettings />}
            colorScheme="purple"
            onClick={handleSetupDefault}
          >
            Setup Default Servers
          </Button>
          <Button
            leftIcon={<FiRefreshCw />}
            onClick={() => {
              fetchServers();
              fetchStats();
            }}
          >
            Refresh
          </Button>
        </HStack>

        {/* Main Content */}
        <Grid templateColumns="repeat(12, 1fr)" gap={6}>
          {/* Server List */}
          <GridItem colSpan={{ base: 12, md: 4 }}>
            <Card>
              <CardHeader>
                <Heading size="md">MCP Servers</Heading>
              </CardHeader>
              <CardBody>
                {loading ? (
                  <Spinner />
                ) : servers.length === 0 ? (
                  <Alert status="info">
                    <AlertIcon />
                    <AlertDescription>
                      No servers found. Create one to get started.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <VStack align="stretch" spacing={2}>
                    {servers.map((server) => (
                      <Card
                        key={server.server_id}
                        variant={
                          selectedServer?.server_id === server.server_id
                            ? 'filled'
                            : 'outline'
                        }
                        cursor="pointer"
                        onClick={() => setSelectedServer(server)}
                        _hover={{ borderColor: 'blue.500' }}
                      >
                        <CardBody>
                          <VStack align="stretch" spacing={2}>
                            <HStack justify="space-between">
                              <Text fontWeight="bold">{server.name}</Text>
                              <Badge colorScheme={getStatusColor(server.status)}>
                                {server.status}
                              </Badge>
                            </HStack>
                            <Text fontSize="sm" color="gray.600">
                              v{server.version}
                            </Text>
                            <HStack spacing={2}>
                              <IconButton
                                size="sm"
                                icon={<FiTrash2 />}
                                colorScheme="red"
                                variant="ghost"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteServer(server.server_id);
                                }}
                              />
                            </HStack>
                          </VStack>
                        </CardBody>
                      </Card>
                    ))}
                  </VStack>
                )}
              </CardBody>
            </Card>
          </GridItem>

          {/* Server Details */}
          <GridItem colSpan={{ base: 12, md: 8 }}>
            {selectedServer ? (
              <Card>
                <CardHeader>
                  <Heading size="md">{selectedServer.name}</Heading>
                  <Text color="gray.600">{selectedServer.description}</Text>
                </CardHeader>
                <CardBody>
                  <Tabs>
                    <TabList>
                      <Tab>
                        <HStack>
                          <FiDatabase />
                          <Text>Resources</Text>
                        </HStack>
                      </Tab>
                      <Tab>
                        <HStack>
                          <FiTool />
                          <Text>Tools</Text>
                        </HStack>
                      </Tab>
                      <Tab>
                        <HStack>
                          <FiFileText />
                          <Text>Prompts</Text>
                        </HStack>
                      </Tab>
                      <Tab>
                        <HStack>
                          <FiActivity />
                          <Text>Stats</Text>
                        </HStack>
                      </Tab>
                    </TabList>

                    <TabPanels>
                      {/* Resources Tab */}
                      <TabPanel>
                        {resources.length === 0 ? (
                          <Text color="gray.500">No resources available</Text>
                        ) : (
                          <Table variant="simple">
                            <Thead>
                              <Tr>
                                <Th>Name</Th>
                                <Th>URI</Th>
                                <Th>Type</Th>
                                <Th>Access Count</Th>
                              </Tr>
                            </Thead>
                            <Tbody>
                              {resources.map((resource) => (
                                <Tr key={resource.id}>
                                  <Td>{resource.name}</Td>
                                  <Td>
                                    <Code>{resource.uri}</Code>
                                  </Td>
                                  <Td>{resource.mime_type || 'N/A'}</Td>
                                  <Td>{resource.access_count}</Td>
                                </Tr>
                              ))}
                            </Tbody>
                          </Table>
                        )}
                      </TabPanel>

                      {/* Tools Tab */}
                      <TabPanel>
                        {tools.length === 0 ? (
                          <Text color="gray.500">No tools available</Text>
                        ) : (
                          <VStack align="stretch" spacing={4}>
                            {tools.map((tool) => (
                              <Card key={tool.id} variant="outline">
                                <CardBody>
                                  <VStack align="stretch" spacing={2}>
                                    <HStack justify="space-between">
                                      <Heading size="sm">{tool.name}</Heading>
                                      <Button
                                        size="sm"
                                        leftIcon={<FiPlay />}
                                        colorScheme="blue"
                                        onClick={() => {
                                          setSelectedTool(tool);
                                          setToolArguments('{}');
                                          setToolResult(null);
                                          onToolCallOpen();
                                        }}
                                      >
                                        Execute
                                      </Button>
                                    </HStack>
                                    <Text fontSize="sm" color="gray.600">
                                      {tool.description}
                                    </Text>
                                    <Text fontSize="xs" color="gray.500">
                                      Executions: {tool.stats?.execution_count || 0} |
                                      Success: {tool.stats?.success_count || 0} |
                                      Failed: {tool.stats?.failure_count || 0}
                                    </Text>
                                  </VStack>
                                </CardBody>
                              </Card>
                            ))}
                          </VStack>
                        )}
                      </TabPanel>

                      {/* Prompts Tab */}
                      <TabPanel>
                        {prompts.length === 0 ? (
                          <Text color="gray.500">No prompts available</Text>
                        ) : (
                          <VStack align="stretch" spacing={4}>
                            {prompts.map((prompt) => (
                              <Card key={prompt.id} variant="outline">
                                <CardBody>
                                  <VStack align="stretch" spacing={2}>
                                    <HStack justify="space-between">
                                      <Heading size="sm">{prompt.name}</Heading>
                                      <Button
                                        size="sm"
                                        leftIcon={<FiFileText />}
                                        colorScheme="purple"
                                        onClick={() => {
                                          setSelectedPrompt(prompt);
                                          setPromptArguments('{}');
                                          setPromptResult(null);
                                          onPromptGetOpen();
                                        }}
                                      >
                                        Get Prompt
                                      </Button>
                                    </HStack>
                                    <Text fontSize="sm" color="gray.600">
                                      {prompt.description}
                                    </Text>
                                    <Text fontSize="xs" color="gray.500">
                                      Usage: {prompt.usage_count || 0}
                                    </Text>
                                  </VStack>
                                </CardBody>
                              </Card>
                            ))}
                          </VStack>
                        )}
                      </TabPanel>

                      {/* Stats Tab */}
                      <TabPanel>
                        <VStack align="stretch" spacing={4}>
                          <StatGroup>
                            <Stat>
                              <StatLabel>Total Requests</StatLabel>
                              <StatNumber>
                                {selectedServer.stats?.total_requests || 0}
                              </StatNumber>
                            </Stat>
                            <Stat>
                              <StatLabel>Successful</StatLabel>
                              <StatNumber>
                                {selectedServer.stats?.successful_requests || 0}
                              </StatNumber>
                            </Stat>
                            <Stat>
                              <StatLabel>Failed</StatLabel>
                              <StatNumber>
                                {selectedServer.stats?.failed_requests || 0}
                              </StatNumber>
                            </Stat>
                          </StatGroup>
                          <Divider />
                          <Box>
                            <Heading size="sm" mb={2}>
                              Server Info
                            </Heading>
                            <Code display="block" p={4} borderRadius="md" whiteSpace="pre">
                              {JSON.stringify(selectedServer, null, 2)}
                            </Code>
                          </Box>
                        </VStack>
                      </TabPanel>
                    </TabPanels>
                  </Tabs>
                </CardBody>
              </Card>
            ) : (
              <Card>
                <CardBody>
                  <Text color="gray.500" textAlign="center">
                    Select a server to view details
                  </Text>
                </CardBody>
              </Card>
            )}
          </GridItem>
        </Grid>
      </VStack>

      {/* Create Server Modal */}
      <Modal isOpen={isCreateServerOpen} onClose={onCreateServerClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Create MCP Server</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Server Name</FormLabel>
                <Input
                  placeholder="My MCP Server"
                  value={newServer.name}
                  onChange={(e) =>
                    setNewServer({ ...newServer, name: e.target.value })
                  }
                />
              </FormControl>
              <FormControl>
                <FormLabel>Version</FormLabel>
                <Input
                  placeholder="1.0.0"
                  value={newServer.version}
                  onChange={(e) =>
                    setNewServer({ ...newServer, version: e.target.value })
                  }
                />
              </FormControl>
              <FormControl>
                <FormLabel>Description</FormLabel>
                <Textarea
                  placeholder="Server description"
                  value={newServer.description}
                  onChange={(e) =>
                    setNewServer({ ...newServer, description: e.target.value })
                  }
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onCreateServerClose}>
              Cancel
            </Button>
            <Button colorScheme="blue" onClick={handleCreateServer}>
              Create
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Tool Call Modal */}
      <Modal isOpen={isToolCallOpen} onClose={onToolCallClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Execute Tool: {selectedTool?.name}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Box>
                <Text fontWeight="bold" mb={2}>
                  Tool Description
                </Text>
                <Text fontSize="sm" color="gray.600">
                  {selectedTool?.description}
                </Text>
              </Box>
              <FormControl>
                <FormLabel>Arguments (JSON)</FormLabel>
                <Textarea
                  value={toolArguments}
                  onChange={(e) => setToolArguments(e.target.value)}
                  fontFamily="mono"
                  rows={6}
                />
              </FormControl>
              {toolResult && (
                <Box>
                  <Text fontWeight="bold" mb={2}>
                    Result
                  </Text>
                  <Code display="block" p={4} borderRadius="md" whiteSpace="pre">
                    {JSON.stringify(toolResult, null, 2)}
                  </Code>
                </Box>
              )}
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onToolCallClose}>
              Close
            </Button>
            <Button colorScheme="blue" leftIcon={<FiPlay />} onClick={handleCallTool}>
              Execute
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Prompt Get Modal */}
      <Modal isOpen={isPromptGetOpen} onClose={onPromptGetClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Get Prompt: {selectedPrompt?.name}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <Box>
                <Text fontWeight="bold" mb={2}>
                  Description
                </Text>
                <Text fontSize="sm" color="gray.600">
                  {selectedPrompt?.description}
                </Text>
              </Box>
              <FormControl>
                <FormLabel>Arguments (JSON)</FormLabel>
                <Textarea
                  value={promptArguments}
                  onChange={(e) => setPromptArguments(e.target.value)}
                  fontFamily="mono"
                  rows={6}
                />
              </FormControl>
              {promptResult && (
                <Box>
                  <Text fontWeight="bold" mb={2}>
                    Generated Prompt
                  </Text>
                  <Code display="block" p={4} borderRadius="md" whiteSpace="pre">
                    {JSON.stringify(promptResult, null, 2)}
                  </Code>
                </Box>
              )}
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onPromptGetClose}>
              Close
            </Button>
            <Button
              colorScheme="purple"
              leftIcon={<FiFileText />}
              onClick={handleGetPrompt}
            >
              Generate
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Container>
  );
};

export default MCPConsolePage;
