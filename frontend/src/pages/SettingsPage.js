import React, { useState } from 'react';
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
  FormControl,
  FormLabel,
  FormHelperText,
  Input,
  Textarea,
  Switch,
  Card,
  CardBody,
  CardHeader,
  Divider,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Badge,
  Grid,
  GridItem,
  InputGroup,
  InputRightElement,
  RadioGroup,
  Radio,
  Stack,
  Code,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  CloseButton,
  useToast,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton
} from '@chakra-ui/react';
import {
  FiSave,
  FiShield,
  FiActivity,
  FiUser,
  FiServer,
  FiLock,
  FiSettings,
  FiDatabase,
  FiSliders,
  FiGlobe,
  FiInfo,
  FiEye,
  FiEyeOff,
  FiAlertCircle,
  FiCheck,
  FiPlus,
  FiTrash2,
  FiRefreshCw,
  FiUpload,
  FiDownload,
  FiCpu,
  FiCloud
} from 'react-icons/fi';

const SettingsPage = () => {
  const toast = useToast();
  const apiKeyModal = useDisclosure();
  
  // Settings state
  const [generalSettings, setGeneralSettings] = useState({
    systemName: 'Universal Knowledge Graph System',
    environment: 'production',
    defaultLanguage: 'en-US',
    logRetention: '30',
    autoSave: true,
    telemetryEnabled: true,
    debugMode: false
  });
  
  const [securitySettings, setSecuritySettings] = useState({
    authProvider: 'azure_ad',
    ssoEnabled: true,
    mfaRequired: true,
    sessionTimeout: '60',
    passwordPolicy: 'enterprise',
    minimumPasswordLength: '14',
    apiTokenExpiry: '30'
  });
  
  const [ukgSimulationSettings, setUkgSimulationSettings] = useState({
    defaultConfidenceThreshold: '0.85',
    maxSimulationLayers: '7',
    refinementStepsEnabled: true,
    defaultRefinementSteps: '12',
    entropySamplingEnabled: true,
    memoryCacheSize: '4096',
    quantumSimulationEnabled: false,
    recursiveProcessingEnabled: true,
    maxRecursionDepth: '8'
  });
  
  const [layoutSettings, setLayoutSettings] = useState({
    theme: 'dark',
    sidebarCollapsed: false,
    cardDensity: 'comfortable',
    animationsEnabled: true,
    visualizationQuality: 'high'
  });
  
  const [integrationSettings, setIntegrationSettings] = useState({
    msGraphEnabled: true,
    azureOpenAIEnabled: true,
    azureOpenAIEndpoint: 'https://ukg-openai.openai.azure.com/',
    azureOpenAIDeployment: 'gpt-4o',
    azureMLEnabled: false,
    cosmosDBEnabled: true,
    azureKeyVaultEnabled: true,
    msTeamsEnabled: true,
    sharePointEnabled: false,
    azureDevOpsEnabled: false
  });
  
  // API Keys (sensitive information)
  const [apiKeys, setApiKeys] = useState([
    {
      id: 1,
      name: 'Azure OpenAI API Key',
      service: 'azure_openai',
      environment: 'production',
      lastRotated: '2025-04-15',
      isActive: true
    },
    {
      id: 2,
      name: 'Azure Cognitive Services Key',
      service: 'azure_cognitive',
      environment: 'production',
      lastRotated: '2025-04-02',
      isActive: true
    },
    {
      id: 3,
      name: 'Graph API Client Secret',
      service: 'ms_graph',
      environment: 'production',
      lastRotated: '2025-05-01',
      isActive: true
    }
  ]);
  
  const [currentApiKey, setCurrentApiKey] = useState(null);
  const [showApiKeyValue, setShowApiKeyValue] = useState(false);
  
  // Update handlers
  const handleGeneralSettingsChange = (e) => {
    const { name, value, type, checked } = e.target;
    setGeneralSettings({
      ...generalSettings,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  const handleSecuritySettingsChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSecuritySettings({
      ...securitySettings,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  const handleUkgSimulationSettingsChange = (e) => {
    const { name, value, type, checked } = e.target;
    setUkgSimulationSettings({
      ...ukgSimulationSettings,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  const handleLayoutSettingsChange = (e) => {
    const { name, value, type, checked } = e.target;
    setLayoutSettings({
      ...layoutSettings,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  const handleIntegrationSettingsChange = (e) => {
    const { name, value, type, checked } = e.target;
    setIntegrationSettings({
      ...integrationSettings,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  // Save settings
  const saveSettings = () => {
    toast({
      title: 'Settings Saved',
      description: 'Your settings have been updated successfully.',
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };
  
  // API Key management
  const openApiKeyModal = (apiKey = null) => {
    setCurrentApiKey(apiKey || {
      id: null,
      name: '',
      service: '',
      environment: 'production',
      lastRotated: new Date().toISOString().split('T')[0],
      isActive: true
    });
    apiKeyModal.onOpen();
  };
  
  const saveApiKey = () => {
    if (currentApiKey.id) {
      // Update existing key
      setApiKeys(apiKeys.map(key => key.id === currentApiKey.id ? currentApiKey : key));
    } else {
      // Add new key
      setApiKeys([...apiKeys, { ...currentApiKey, id: Date.now() }]);
    }
    
    apiKeyModal.onClose();
    
    toast({
      title: currentApiKey.id ? 'API Key Updated' : 'API Key Added',
      description: `The API key for ${currentApiKey.name} has been ${currentApiKey.id ? 'updated' : 'added'}.`,
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };
  
  const deleteApiKey = (id) => {
    setApiKeys(apiKeys.filter(key => key.id !== id));
    
    toast({
      title: 'API Key Removed',
      description: 'The API key has been removed.',
      status: 'info',
      duration: 3000,
      isClosable: true,
    });
  };
  
  // Export settings
  const exportSettings = () => {
    const settings = {
      general: generalSettings,
      security: securitySettings,
      ukgSimulation: ukgSimulationSettings,
      layout: layoutSettings,
      integration: integrationSettings
    };
    
    const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'ukg-settings.json';
    link.click();
    
    toast({
      title: 'Settings Exported',
      description: 'Your settings have been exported as JSON.',
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };
  
  return (
    <Box h="100%">
      <Flex mb={6} justify="space-between" align="center">
        <Heading size="lg">System Settings</Heading>
        
        <HStack spacing={3}>
          <Button
            leftIcon={<FiUpload />}
            variant="outline"
            onClick={() => {
              toast({
                title: 'Import Settings',
                description: 'This would allow importing settings from a JSON file.',
                status: 'info',
                duration: 3000,
                isClosable: true,
              });
            }}
          >
            Import
          </Button>
          
          <Button
            leftIcon={<FiDownload />}
            variant="outline"
            onClick={exportSettings}
          >
            Export
          </Button>
          
          <Button
            leftIcon={<FiSave />}
            colorScheme="brand"
            onClick={saveSettings}
          >
            Save All Changes
          </Button>
        </HStack>
      </Flex>
      
      <Tabs variant="soft-rounded" colorScheme="brand">
        <TabList mb={4}>
          <Tab><HStack><FiSettings /><Text>General</Text></HStack></Tab>
          <Tab><HStack><FiShield /><Text>Security</Text></HStack></Tab>
          <Tab><HStack><FiCpu /><Text>UKG Simulation</Text></HStack></Tab>
          <Tab><HStack><FiSliders /><Text>Layout</Text></HStack></Tab>
          <Tab><HStack><FiCloud /><Text>Integrations</Text></HStack></Tab>
          <Tab><HStack><FiLock /><Text>API Keys</Text></HStack></Tab>
        </TabList>
        
        <TabPanels>
          {/* General Settings */}
          <TabPanel>
            <Card bg="dark.700" variant="outline">
              <CardHeader>
                <Heading size="md">General Settings</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={6} align="stretch">
                  <FormControl>
                    <FormLabel>System Name</FormLabel>
                    <Input
                      name="systemName"
                      value={generalSettings.systemName}
                      onChange={handleGeneralSettingsChange}
                      bg="dark.800"
                    />
                    <FormHelperText>The name of your UKG system instance</FormHelperText>
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Environment</FormLabel>
                    <Select
                      name="environment"
                      value={generalSettings.environment}
                      onChange={handleGeneralSettingsChange}
                      bg="dark.800"
                    >
                      <option value="development">Development</option>
                      <option value="staging">Staging</option>
                      <option value="production">Production</option>
                    </Select>
                    <FormHelperText>Current environment for this UKG instance</FormHelperText>
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Default Language</FormLabel>
                    <Select
                      name="defaultLanguage"
                      value={generalSettings.defaultLanguage}
                      onChange={handleGeneralSettingsChange}
                      bg="dark.800"
                    >
                      <option value="en-US">English (US)</option>
                      <option value="en-UK">English (UK)</option>
                      <option value="es-ES">Spanish (Spain)</option>
                      <option value="fr-FR">French</option>
                      <option value="de-DE">German</option>
                      <option value="ja-JP">Japanese</option>
                      <option value="zh-CN">Chinese (Simplified)</option>
                    </Select>
                    <FormHelperText>Default language for the interface and simulations</FormHelperText>
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Log Retention (days)</FormLabel>
                    <Input
                      name="logRetention"
                      value={generalSettings.logRetention}
                      onChange={handleGeneralSettingsChange}
                      type="number"
                      bg="dark.800"
                    />
                    <FormHelperText>Number of days to retain system logs</FormHelperText>
                  </FormControl>
                  
                  <Divider />
                  
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="autoSave" mb="0">
                      Auto-Save Settings
                    </FormLabel>
                    <Switch
                      id="autoSave"
                      name="autoSave"
                      isChecked={generalSettings.autoSave}
                      onChange={handleGeneralSettingsChange}
                      colorScheme="brand"
                    />
                  </FormControl>
                  
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="telemetryEnabled" mb="0">
                      Enable Telemetry
                    </FormLabel>
                    <Switch
                      id="telemetryEnabled"
                      name="telemetryEnabled"
                      isChecked={generalSettings.telemetryEnabled}
                      onChange={handleGeneralSettingsChange}
                      colorScheme="brand"
                    />
                  </FormControl>
                  
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="debugMode" mb="0">
                      Debug Mode
                    </FormLabel>
                    <Switch
                      id="debugMode"
                      name="debugMode"
                      isChecked={generalSettings.debugMode}
                      onChange={handleGeneralSettingsChange}
                      colorScheme="brand"
                    />
                  </FormControl>
                  
                  <HStack justify="flex-end">
                    <Button
                      leftIcon={<FiRefreshCw />}
                      variant="outline"
                      onClick={() => {
                        setGeneralSettings({
                          systemName: 'Universal Knowledge Graph System',
                          environment: 'production',
                          defaultLanguage: 'en-US',
                          logRetention: '30',
                          autoSave: true,
                          telemetryEnabled: true,
                          debugMode: false
                        });
                      }}
                    >
                      Reset to Defaults
                    </Button>
                    <Button
                      leftIcon={<FiSave />}
                      colorScheme="brand"
                      onClick={() => {
                        toast({
                          title: 'General Settings Saved',
                          status: 'success',
                          duration: 2000,
                          isClosable: true,
                        });
                      }}
                    >
                      Save Changes
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
          
          {/* Security Settings */}
          <TabPanel>
            <Card bg="dark.700" variant="outline">
              <CardHeader>
                <Heading size="md">Security Settings</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={6} align="stretch">
                  <Alert status="info" variant="subtle" borderRadius="md">
                    <AlertIcon />
                    <Box>
                      <AlertTitle>Microsoft Enterprise Security Standards</AlertTitle>
                      <AlertDescription>
                        These settings follow Microsoft's security best practices and comply with enterprise standards.
                      </AlertDescription>
                    </Box>
                  </Alert>
                  
                  <FormControl>
                    <FormLabel>Authentication Provider</FormLabel>
                    <Select
                      name="authProvider"
                      value={securitySettings.authProvider}
                      onChange={handleSecuritySettingsChange}
                      bg="dark.800"
                    >
                      <option value="azure_ad">Azure Active Directory</option>
                      <option value="entra_id">Microsoft Entra ID</option>
                      <option value="okta">Okta</option>
                      <option value="auth0">Auth0</option>
                      <option value="local">Local Authentication</option>
                    </Select>
                    <FormHelperText>Identity provider for user authentication</FormHelperText>
                  </FormControl>
                  
                  <Grid templateColumns="repeat(2, 1fr)" gap={6}>
                    <GridItem>
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="ssoEnabled" mb="0">
                          Enable Single Sign-On (SSO)
                        </FormLabel>
                        <Switch
                          id="ssoEnabled"
                          name="ssoEnabled"
                          isChecked={securitySettings.ssoEnabled}
                          onChange={handleSecuritySettingsChange}
                          colorScheme="brand"
                        />
                      </FormControl>
                    </GridItem>
                    
                    <GridItem>
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="mfaRequired" mb="0">
                          Require Multi-Factor Authentication
                        </FormLabel>
                        <Switch
                          id="mfaRequired"
                          name="mfaRequired"
                          isChecked={securitySettings.mfaRequired}
                          onChange={handleSecuritySettingsChange}
                          colorScheme="brand"
                        />
                      </FormControl>
                    </GridItem>
                  </Grid>
                  
                  <FormControl>
                    <FormLabel>Session Timeout (minutes)</FormLabel>
                    <Input
                      name="sessionTimeout"
                      value={securitySettings.sessionTimeout}
                      onChange={handleSecuritySettingsChange}
                      type="number"
                      bg="dark.800"
                    />
                    <FormHelperText>Automatically log out inactive users after this period</FormHelperText>
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Password Policy</FormLabel>
                    <Select
                      name="passwordPolicy"
                      value={securitySettings.passwordPolicy}
                      onChange={handleSecuritySettingsChange}
                      bg="dark.800"
                    >
                      <option value="standard">Standard (8+ chars, mixed case, numbers)</option>
                      <option value="enterprise">Enterprise (12+ chars, mixed case, numbers, symbols)</option>
                      <option value="nist">NIST 800-63B (Passphrase based)</option>
                      <option value="custom">Custom Policy</option>
                    </Select>
                    <FormHelperText>Password complexity requirements</FormHelperText>
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Minimum Password Length</FormLabel>
                    <Input
                      name="minimumPasswordLength"
                      value={securitySettings.minimumPasswordLength}
                      onChange={handleSecuritySettingsChange}
                      type="number"
                      bg="dark.800"
                    />
                    <FormHelperText>Minimum required password length</FormHelperText>
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>API Token Expiry (days)</FormLabel>
                    <Input
                      name="apiTokenExpiry"
                      value={securitySettings.apiTokenExpiry}
                      onChange={handleSecuritySettingsChange}
                      type="number"
                      bg="dark.800"
                    />
                    <FormHelperText>Number of days before API tokens expire</FormHelperText>
                  </FormControl>
                  
                  <Divider />
                  
                  <HStack justify="flex-end">
                    <Button
                      leftIcon={<FiRefreshCw />}
                      variant="outline"
                      onClick={() => {
                        setSecuritySettings({
                          authProvider: 'azure_ad',
                          ssoEnabled: true,
                          mfaRequired: true,
                          sessionTimeout: '60',
                          passwordPolicy: 'enterprise',
                          minimumPasswordLength: '14',
                          apiTokenExpiry: '30'
                        });
                      }}
                    >
                      Reset to Microsoft Defaults
                    </Button>
                    <Button
                      leftIcon={<FiSave />}
                      colorScheme="brand"
                      onClick={() => {
                        toast({
                          title: 'Security Settings Saved',
                          status: 'success',
                          duration: 2000,
                          isClosable: true,
                        });
                      }}
                    >
                      Save Changes
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
          
          {/* UKG Simulation Settings */}
          <TabPanel>
            <Card bg="dark.700" variant="outline">
              <CardHeader>
                <Heading size="md">UKG Simulation Settings</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={6} align="stretch">
                  <FormControl>
                    <FormLabel>Default Confidence Threshold</FormLabel>
                    <HStack>
                      <Input
                        name="defaultConfidenceThreshold"
                        value={ukgSimulationSettings.defaultConfidenceThreshold}
                        onChange={handleUkgSimulationSettingsChange}
                        type="number"
                        step="0.01"
                        min="0"
                        max="1"
                        bg="dark.800"
                      />
                      <Badge colorScheme="green">{(parseFloat(ukgSimulationSettings.defaultConfidenceThreshold) * 100).toFixed(0)}%</Badge>
                    </HStack>
                    <FormHelperText>Minimum confidence score required for simulation results (0.0 - 1.0)</FormHelperText>
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Maximum Simulation Layers</FormLabel>
                    <Select
                      name="maxSimulationLayers"
                      value={ukgSimulationSettings.maxSimulationLayers}
                      onChange={handleUkgSimulationSettingsChange}
                      bg="dark.800"
                    >
                      <option value="5">5 Layers (L1-L5)</option>
                      <option value="7">7 Layers (L1-L7)</option>
                      <option value="10">10 Layers (L1-L10)</option>
                    </Select>
                    <FormHelperText>Maximum number of simulation layers to activate by default</FormHelperText>
                  </FormControl>
                  
                  <Grid templateColumns="repeat(2, 1fr)" gap={6}>
                    <GridItem>
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="refinementStepsEnabled" mb="0">
                          Enable Refinement Steps
                        </FormLabel>
                        <Switch
                          id="refinementStepsEnabled"
                          name="refinementStepsEnabled"
                          isChecked={ukgSimulationSettings.refinementStepsEnabled}
                          onChange={handleUkgSimulationSettingsChange}
                          colorScheme="brand"
                        />
                      </FormControl>
                    </GridItem>
                    
                    <GridItem>
                      <FormControl>
                        <FormLabel>Default Refinement Steps</FormLabel>
                        <Input
                          name="defaultRefinementSteps"
                          value={ukgSimulationSettings.defaultRefinementSteps}
                          onChange={handleUkgSimulationSettingsChange}
                          isDisabled={!ukgSimulationSettings.refinementStepsEnabled}
                          type="number"
                          bg="dark.800"
                        />
                      </FormControl>
                    </GridItem>
                  </Grid>
                  
                  <FormControl>
                    <FormLabel>Memory Cache Size (MB)</FormLabel>
                    <Input
                      name="memoryCacheSize"
                      value={ukgSimulationSettings.memoryCacheSize}
                      onChange={handleUkgSimulationSettingsChange}
                      type="number"
                      bg="dark.800"
                    />
                    <FormHelperText>Maximum memory allocation for simulation cache</FormHelperText>
                  </FormControl>
                  
                  <Divider />
                  
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="entropySamplingEnabled" mb="0">
                      Enable Entropy Sampling
                    </FormLabel>
                    <Switch
                      id="entropySamplingEnabled"
                      name="entropySamplingEnabled"
                      isChecked={ukgSimulationSettings.entropySamplingEnabled}
                      onChange={handleUkgSimulationSettingsChange}
                      colorScheme="brand"
                    />
                  </FormControl>
                  
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="quantumSimulationEnabled" mb="0">
                      Enable Quantum Simulation (Layer 8)
                    </FormLabel>
                    <Switch
                      id="quantumSimulationEnabled"
                      name="quantumSimulationEnabled"
                      isChecked={ukgSimulationSettings.quantumSimulationEnabled}
                      onChange={handleUkgSimulationSettingsChange}
                      colorScheme="brand"
                    />
                  </FormControl>
                  
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="recursiveProcessingEnabled" mb="0">
                      Enable Recursive Processing (Layer 9)
                    </FormLabel>
                    <Switch
                      id="recursiveProcessingEnabled"
                      name="recursiveProcessingEnabled"
                      isChecked={ukgSimulationSettings.recursiveProcessingEnabled}
                      onChange={handleUkgSimulationSettingsChange}
                      colorScheme="brand"
                    />
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Maximum Recursion Depth</FormLabel>
                    <Input
                      name="maxRecursionDepth"
                      value={ukgSimulationSettings.maxRecursionDepth}
                      onChange={handleUkgSimulationSettingsChange}
                      isDisabled={!ukgSimulationSettings.recursiveProcessingEnabled}
                      type="number"
                      bg="dark.800"
                    />
                    <FormHelperText>Maximum depth for recursive processing in Layer 9</FormHelperText>
                  </FormControl>
                  
                  <HStack justify="flex-end">
                    <Button
                      leftIcon={<FiRefreshCw />}
                      variant="outline"
                      onClick={() => {
                        setUkgSimulationSettings({
                          defaultConfidenceThreshold: '0.85',
                          maxSimulationLayers: '7',
                          refinementStepsEnabled: true,
                          defaultRefinementSteps: '12',
                          entropySamplingEnabled: true,
                          memoryCacheSize: '4096',
                          quantumSimulationEnabled: false,
                          recursiveProcessingEnabled: true,
                          maxRecursionDepth: '8'
                        });
                      }}
                    >
                      Reset to Defaults
                    </Button>
                    <Button
                      leftIcon={<FiSave />}
                      colorScheme="brand"
                      onClick={() => {
                        toast({
                          title: 'Simulation Settings Saved',
                          status: 'success',
                          duration: 2000,
                          isClosable: true,
                        });
                      }}
                    >
                      Save Changes
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
          
          {/* Layout Settings */}
          <TabPanel>
            <Card bg="dark.700" variant="outline">
              <CardHeader>
                <Heading size="md">Layout & Appearance Settings</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={6} align="stretch">
                  <FormControl>
                    <FormLabel>Theme</FormLabel>
                    <RadioGroup
                      name="theme"
                      value={layoutSettings.theme}
                      onChange={(value) => setLayoutSettings({...layoutSettings, theme: value})}
                    >
                      <Stack direction="row" spacing={5}>
                        <Radio value="light">Light Mode</Radio>
                        <Radio value="dark">Dark Mode</Radio>
                        <Radio value="system">Use System Preference</Radio>
                      </Stack>
                    </RadioGroup>
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Card Density</FormLabel>
                    <Select
                      name="cardDensity"
                      value={layoutSettings.cardDensity}
                      onChange={handleLayoutSettingsChange}
                      bg="dark.800"
                    >
                      <option value="comfortable">Comfortable</option>
                      <option value="compact">Compact</option>
                      <option value="spacious">Spacious</option>
                    </Select>
                    <FormHelperText>Controls spacing in cards and UI elements</FormHelperText>
                  </FormControl>
                  
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="sidebarCollapsed" mb="0">
                      Collapsed Sidebar by Default
                    </FormLabel>
                    <Switch
                      id="sidebarCollapsed"
                      name="sidebarCollapsed"
                      isChecked={layoutSettings.sidebarCollapsed}
                      onChange={handleLayoutSettingsChange}
                      colorScheme="brand"
                    />
                  </FormControl>
                  
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="animationsEnabled" mb="0">
                      Enable Animations
                    </FormLabel>
                    <Switch
                      id="animationsEnabled"
                      name="animationsEnabled"
                      isChecked={layoutSettings.animationsEnabled}
                      onChange={handleLayoutSettingsChange}
                      colorScheme="brand"
                    />
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Visualization Quality</FormLabel>
                    <Select
                      name="visualizationQuality"
                      value={layoutSettings.visualizationQuality}
                      onChange={handleLayoutSettingsChange}
                      bg="dark.800"
                    >
                      <option value="low">Low (Better Performance)</option>
                      <option value="medium">Medium</option>
                      <option value="high">High (Better Visuals)</option>
                    </Select>
                    <FormHelperText>Controls the quality of graphs and visualizations</FormHelperText>
                  </FormControl>
                  
                  <HStack justify="flex-end">
                    <Button
                      leftIcon={<FiRefreshCw />}
                      variant="outline"
                      onClick={() => {
                        setLayoutSettings({
                          theme: 'dark',
                          sidebarCollapsed: false,
                          cardDensity: 'comfortable',
                          animationsEnabled: true,
                          visualizationQuality: 'high'
                        });
                      }}
                    >
                      Reset to Defaults
                    </Button>
                    <Button
                      leftIcon={<FiSave />}
                      colorScheme="brand"
                      onClick={() => {
                        toast({
                          title: 'Layout Settings Saved',
                          status: 'success',
                          duration: 2000,
                          isClosable: true,
                        });
                      }}
                    >
                      Save Changes
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
          
          {/* Integration Settings */}
          <TabPanel>
            <Card bg="dark.700" variant="outline">
              <CardHeader>
                <HStack justify="space-between">
                  <Heading size="md">Microsoft Enterprise Integrations</Heading>
                  <Badge colorScheme="blue">Microsoft Enterprise Standards Compliant</Badge>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack spacing={6} align="stretch">
                  <Alert status="info" variant="subtle" borderRadius="md">
                    <AlertIcon />
                    <Box>
                      <AlertTitle>Azure Active Directory Connected</AlertTitle>
                      <AlertDescription>
                        Integration with Azure AD is active and properly configured. Users can log in with their Microsoft credentials.
                      </AlertDescription>
                    </Box>
                  </Alert>
                  
                  <Divider />
                  
                  <FormControl>
                    <FormLabel fontWeight="bold">Microsoft Azure AI Services</FormLabel>
                    <VStack align="stretch" spacing={4} mt={2}>
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="azureOpenAIEnabled" mb="0">
                          Azure OpenAI Service
                        </FormLabel>
                        <Switch
                          id="azureOpenAIEnabled"
                          name="azureOpenAIEnabled"
                          isChecked={integrationSettings.azureOpenAIEnabled}
                          onChange={handleIntegrationSettingsChange}
                          colorScheme="brand"
                        />
                      </FormControl>
                      
                      {integrationSettings.azureOpenAIEnabled && (
                        <Box pl={5}>
                          <FormControl mb={3}>
                            <FormLabel fontSize="sm">Azure OpenAI Endpoint</FormLabel>
                            <Input
                              name="azureOpenAIEndpoint"
                              value={integrationSettings.azureOpenAIEndpoint}
                              onChange={handleIntegrationSettingsChange}
                              bg="dark.800"
                              size="sm"
                            />
                          </FormControl>
                          
                          <FormControl>
                            <FormLabel fontSize="sm">Azure OpenAI Deployment</FormLabel>
                            <Select
                              name="azureOpenAIDeployment"
                              value={integrationSettings.azureOpenAIDeployment}
                              onChange={handleIntegrationSettingsChange}
                              bg="dark.800"
                              size="sm"
                            >
                              <option value="gpt-4o">GPT-4o</option>
                              <option value="gpt-35-turbo">GPT-3.5 Turbo</option>
                              <option value="text-embedding-ada-002">Text Embedding Ada</option>
                            </Select>
                          </FormControl>
                        </Box>
                      )}
                      
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="azureMLEnabled" mb="0">
                          Azure Machine Learning
                        </FormLabel>
                        <Switch
                          id="azureMLEnabled"
                          name="azureMLEnabled"
                          isChecked={integrationSettings.azureMLEnabled}
                          onChange={handleIntegrationSettingsChange}
                          colorScheme="brand"
                        />
                      </FormControl>
                    </VStack>
                  </FormControl>
                  
                  <Divider />
                  
                  <FormControl>
                    <FormLabel fontWeight="bold">Microsoft Data & Storage</FormLabel>
                    <VStack align="stretch" spacing={4} mt={2}>
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="cosmosDBEnabled" mb="0">
                          Azure Cosmos DB
                        </FormLabel>
                        <Switch
                          id="cosmosDBEnabled"
                          name="cosmosDBEnabled"
                          isChecked={integrationSettings.cosmosDBEnabled}
                          onChange={handleIntegrationSettingsChange}
                          colorScheme="brand"
                        />
                      </FormControl>
                      
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="azureKeyVaultEnabled" mb="0">
                          Azure Key Vault
                        </FormLabel>
                        <Switch
                          id="azureKeyVaultEnabled"
                          name="azureKeyVaultEnabled"
                          isChecked={integrationSettings.azureKeyVaultEnabled}
                          onChange={handleIntegrationSettingsChange}
                          colorScheme="brand"
                        />
                      </FormControl>
                    </VStack>
                  </FormControl>
                  
                  <Divider />
                  
                  <FormControl>
                    <FormLabel fontWeight="bold">Microsoft 365 & Productivity</FormLabel>
                    <VStack align="stretch" spacing={4} mt={2}>
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="msGraphEnabled" mb="0">
                          Microsoft Graph API
                        </FormLabel>
                        <Switch
                          id="msGraphEnabled"
                          name="msGraphEnabled"
                          isChecked={integrationSettings.msGraphEnabled}
                          onChange={handleIntegrationSettingsChange}
                          colorScheme="brand"
                        />
                      </FormControl>
                      
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="msTeamsEnabled" mb="0">
                          Microsoft Teams
                        </FormLabel>
                        <Switch
                          id="msTeamsEnabled"
                          name="msTeamsEnabled"
                          isChecked={integrationSettings.msTeamsEnabled}
                          onChange={handleIntegrationSettingsChange}
                          colorScheme="brand"
                        />
                      </FormControl>
                      
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="sharePointEnabled" mb="0">
                          SharePoint
                        </FormLabel>
                        <Switch
                          id="sharePointEnabled"
                          name="sharePointEnabled"
                          isChecked={integrationSettings.sharePointEnabled}
                          onChange={handleIntegrationSettingsChange}
                          colorScheme="brand"
                        />
                      </FormControl>
                      
                      <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="azureDevOpsEnabled" mb="0">
                          Azure DevOps
                        </FormLabel>
                        <Switch
                          id="azureDevOpsEnabled"
                          name="azureDevOpsEnabled"
                          isChecked={integrationSettings.azureDevOpsEnabled}
                          onChange={handleIntegrationSettingsChange}
                          colorScheme="brand"
                        />
                      </FormControl>
                    </VStack>
                  </FormControl>
                  
                  <HStack justify="flex-end">
                    <Button
                      leftIcon={<FiRefreshCw />}
                      variant="outline"
                      onClick={() => {
                        setIntegrationSettings({
                          msGraphEnabled: true,
                          azureOpenAIEnabled: true,
                          azureOpenAIEndpoint: 'https://ukg-openai.openai.azure.com/',
                          azureOpenAIDeployment: 'gpt-4o',
                          azureMLEnabled: false,
                          cosmosDBEnabled: true,
                          azureKeyVaultEnabled: true,
                          msTeamsEnabled: true,
                          sharePointEnabled: false,
                          azureDevOpsEnabled: false
                        });
                      }}
                    >
                      Reset to Defaults
                    </Button>
                    <Button
                      leftIcon={<FiSave />}
                      colorScheme="brand"
                      onClick={() => {
                        toast({
                          title: 'Integration Settings Saved',
                          status: 'success',
                          duration: 2000,
                          isClosable: true,
                        });
                      }}
                    >
                      Save Changes
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
          
          {/* API Keys */}
          <TabPanel>
            <Card bg="dark.700" variant="outline">
              <CardHeader>
                <HStack justify="space-between">
                  <Heading size="md">API Keys & Secrets</Heading>
                  <Button
                    leftIcon={<FiPlus />}
                    colorScheme="brand"
                    size="sm"
                    onClick={() => openApiKeyModal()}
                  >
                    Add New API Key
                  </Button>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <Alert status="warning" variant="subtle" borderRadius="md">
                    <AlertIcon />
                    <Box>
                      <AlertTitle>Security Notice</AlertTitle>
                      <AlertDescription>
                        API keys provide access to sensitive services. Rotate keys regularly and restrict access to authorized personnel only.
                      </AlertDescription>
                    </Box>
                  </Alert>
                  
                  <Box overflowX="auto">
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Name</Th>
                          <Th>Service</Th>
                          <Th>Environment</Th>
                          <Th>Last Rotated</Th>
                          <Th>Status</Th>
                          <Th>Actions</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {apiKeys.map((key) => (
                          <Tr key={key.id}>
                            <Td>{key.name}</Td>
                            <Td>
                              <Badge>
                                {key.service === 'azure_openai' ? 'Azure OpenAI' :
                                 key.service === 'azure_cognitive' ? 'Cognitive Services' :
                                 key.service === 'ms_graph' ? 'Microsoft Graph' : key.service}
                              </Badge>
                            </Td>
                            <Td>
                              <Badge colorScheme={key.environment === 'production' ? 'red' : 'yellow'}>
                                {key.environment}
                              </Badge>
                            </Td>
                            <Td>{key.lastRotated}</Td>
                            <Td>
                              <Badge colorScheme={key.isActive ? 'green' : 'red'}>
                                {key.isActive ? 'Active' : 'Inactive'}
                              </Badge>
                            </Td>
                            <Td>
                              <HStack>
                                <IconButton
                                  icon={<FiRefreshCw />}
                                  aria-label="Rotate key"
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => {
                                    toast({
                                      title: 'Key Rotation',
                                      description: `The API key for ${key.name} has been rotated.`,
                                      status: 'success',
                                      duration: 3000,
                                      isClosable: true,
                                    });
                                  }}
                                />
                                <IconButton
                                  icon={<FiEdit2 />}
                                  aria-label="Edit key"
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => openApiKeyModal(key)}
                                />
                                <IconButton
                                  icon={<FiTrash2 />}
                                  aria-label="Delete key"
                                  size="sm"
                                  variant="ghost"
                                  colorScheme="red"
                                  onClick={() => deleteApiKey(key.id)}
                                />
                              </HStack>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </Box>
                  
                  {apiKeys.length === 0 && (
                    <Box textAlign="center" py={6} color="gray.500">
                      <Text>No API keys have been added yet</Text>
                    </Box>
                  )}
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>
      
      {/* API Key Modal */}
      <Modal isOpen={apiKeyModal.isOpen} onClose={apiKeyModal.onClose}>
        <ModalOverlay />
        <ModalContent bg="dark.700">
          <ModalHeader>{currentApiKey?.id ? 'Edit API Key' : 'Add New API Key'}</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Key Name</FormLabel>
                <Input 
                  value={currentApiKey?.name || ''} 
                  onChange={(e) => setCurrentApiKey({...currentApiKey, name: e.target.value})}
                  placeholder="Key name"
                  bg="dark.800"
                />
              </FormControl>
              
              <FormControl isRequired>
                <FormLabel>Service</FormLabel>
                <Select 
                  value={currentApiKey?.service || ''} 
                  onChange={(e) => setCurrentApiKey({...currentApiKey, service: e.target.value})}
                  placeholder="Select service"
                  bg="dark.800"
                >
                  <option value="azure_openai">Azure OpenAI</option>
                  <option value="azure_cognitive">Azure Cognitive Services</option>
                  <option value="ms_graph">Microsoft Graph API</option>
                  <option value="azure_keyvault">Azure Key Vault</option>
                  <option value="azure_storage">Azure Storage</option>
                </Select>
              </FormControl>
              
              <FormControl isRequired>
                <FormLabel>Environment</FormLabel>
                <Select 
                  value={currentApiKey?.environment || 'production'} 
                  onChange={(e) => setCurrentApiKey({...currentApiKey, environment: e.target.value})}
                  bg="dark.800"
                >
                  <option value="development">Development</option>
                  <option value="staging">Staging</option>
                  <option value="production">Production</option>
                </Select>
              </FormControl>
              
              {/* Only show for new keys */}
              {!currentApiKey?.id && (
                <FormControl>
                  <FormLabel>API Key Value</FormLabel>
                  <InputGroup>
                    <Input
                      type={showApiKeyValue ? 'text' : 'password'}
                      placeholder="Enter API key value"
                      bg="dark.800"
                    />
                    <InputRightElement>
                      <IconButton
                        icon={showApiKeyValue ? <FiEyeOff /> : <FiEye />}
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowApiKeyValue(!showApiKeyValue)}
                        aria-label={showApiKeyValue ? 'Hide' : 'Show'}
                      />
                    </InputRightElement>
                  </InputGroup>
                  <FormHelperText>The key value is stored securely and never displayed again</FormHelperText>
                </FormControl>
              )}
              
              <FormControl display="flex" alignItems="center">
                <FormLabel htmlFor="is-active" mb="0">
                  Active
                </FormLabel>
                <Switch
                  id="is-active"
                  isChecked={currentApiKey?.isActive}
                  onChange={(e) => setCurrentApiKey({...currentApiKey, isActive: e.target.checked})}
                  colorScheme="brand"
                />
              </FormControl>
            </VStack>
          </ModalBody>
          
          <ModalFooter>
            <Button mr={3} onClick={apiKeyModal.onClose}>
              Cancel
            </Button>
            <Button colorScheme="brand" onClick={saveApiKey}>
              {currentApiKey?.id ? 'Update Key' : 'Add Key'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

// Component for Table since it was used but not imported
const Table = ({ children, ...props }) => {
  return (
    <Box as="table" width="100%" {...props}>
      {children}
    </Box>
  );
};

const Thead = ({ children, ...props }) => {
  return (
    <Box as="thead" {...props}>
      {children}
    </Box>
  );
};

const Tbody = ({ children, ...props }) => {
  return (
    <Box as="tbody" {...props}>
      {children}
    </Box>
  );
};

const Tr = ({ children, ...props }) => {
  return (
    <Box as="tr" {...props}>
      {children}
    </Box>
  );
};

const Th = ({ children, ...props }) => {
  return (
    <Box as="th" px="4" py="2" textAlign="left" fontWeight="bold" {...props}>
      {children}
    </Box>
  );
};

const Td = ({ children, ...props }) => {
  return (
    <Box as="td" px="4" py="2" borderTopWidth="1px" borderColor="gray.700" {...props}>
      {children}
    </Box>
  );
};

export default SettingsPage;