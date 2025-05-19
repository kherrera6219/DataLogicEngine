import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Flex,
  Text,
  Heading,
  HStack,
  VStack,
  Button,
  IconButton,
  Select,
  Badge,
  Card,
  CardBody,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Tooltip,
  Grid,
  GridItem,
  Divider,
  Progress,
  useToast
} from '@chakra-ui/react';
import {
  FiZoomIn,
  FiZoomOut,
  FiRefreshCw,
  FiDownload,
  FiInfo,
  FiSettings,
  FiCpu,
  FiLayers,
  FiActivity,
  FiGrid,
  FiMap,
  FiMaximize,
  FiSearch,
  FiPlus,
  FiMinus
} from 'react-icons/fi';

// Attempt to load ForceGraph if running in browser
let ForceGraph2D = null;
if (typeof window !== 'undefined') {
  try {
    // Dynamic import for the force graph
    ForceGraph2D = require('react-force-graph-2d').default;
  } catch (e) {
    console.error("Failed to load ForceGraph component", e);
  }
}

const SimulationMapPage = () => {
  const toast = useToast();
  const graphRef = useRef(null);
  const [activeAxis, setActiveAxis] = useState(1);
  const [viewMode, setViewMode] = useState('2d');
  const [graphData, setGraphData] = useState({
    nodes: [],
    links: []
  });
  const [selectedNode, setSelectedNode] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [simulationProgress, setSimulationProgress] = useState(0);
  const [zoomLevel, setZoomLevel] = useState(1);
  
  // Pillar level data (Axis 1)
  const pillarLevels = [
    { id: 'PL01', name: 'Mathematics', category: 'Formal Sciences' },
    { id: 'PL02', name: 'Physical Sciences', category: 'Natural Sciences' },
    { id: 'PL03', name: 'Life Sciences', category: 'Natural Sciences' },
    { id: 'PL04', name: 'Computer Science', category: 'Formal Sciences' },
    { id: 'PL05', name: 'Engineering', category: 'Applied Sciences' },
    { id: 'PL10', name: 'Economics', category: 'Social Sciences' },
    { id: 'PL15', name: 'Psychology', category: 'Social Sciences' },
    { id: 'PL20', name: 'Law', category: 'Humanities' },
    { id: 'PL25', name: 'Philosophy', category: 'Humanities' },
    { id: 'PL30', name: 'Management', category: 'Applied Sciences' },
    { id: 'PL35', name: 'Politics', category: 'Social Sciences' },
    { id: 'PL40', name: 'Medicine', category: 'Applied Sciences' },
    { id: 'PL45', name: 'Art', category: 'Humanities' },
    { id: 'PL48', name: 'Multi-dimensional Systems', category: 'Meta-discipline' }
  ];
  
  // Sector data (Axis 2)
  const sectors = [
    { id: 'SEC01', name: 'Government', subsectors: ['Federal', 'State', 'Local'] },
    { id: 'SEC02', name: 'Technology', subsectors: ['Software', 'Hardware', 'Services'] },
    { id: 'SEC03', name: 'Healthcare', subsectors: ['Providers', 'Insurance', 'Pharma'] },
    { id: 'SEC04', name: 'Finance', subsectors: ['Banking', 'Investment', 'Insurance'] },
    { id: 'SEC05', name: 'Education', subsectors: ['K-12', 'Higher Ed', 'Corporate'] },
    { id: 'SEC06', name: 'Manufacturing', subsectors: ['Automotive', 'Electronics', 'Consumer Goods'] },
    { id: 'SEC07', name: 'Energy', subsectors: ['Oil & Gas', 'Renewable', 'Utilities'] },
    { id: 'SEC08', name: 'Defense', subsectors: ['Military', 'Intelligence', 'Aerospace'] },
    { id: 'SEC09', name: 'Transportation', subsectors: ['Air', 'Rail', 'Road', 'Maritime'] },
    { id: 'SEC10', name: 'Agriculture', subsectors: ['Farming', 'Processing', 'Distribution'] }
  ];
  
  // Domain data (Axis 3)
  const domains = [
    { id: 'DOM01', name: 'Federal Government', sector: 'SEC01' },
    { id: 'DOM02', name: 'State Government', sector: 'SEC01' },
    { id: 'DOM03', name: 'Software Development', sector: 'SEC02' },
    { id: 'DOM04', name: 'Cloud Services', sector: 'SEC02' },
    { id: 'DOM05', name: 'Hospitals', sector: 'SEC03' },
    { id: 'DOM06', name: 'Pharmaceutical Companies', sector: 'SEC03' },
    { id: 'DOM07', name: 'Commercial Banking', sector: 'SEC04' },
    { id: 'DOM08', name: 'Investment Banking', sector: 'SEC04' },
    { id: 'DOM09', name: 'K-12 Education', sector: 'SEC05' },
    { id: 'DOM10', name: 'Higher Education', sector: 'SEC05' },
    { id: 'DOM11', name: 'Automotive Manufacturing', sector: 'SEC06' },
    { id: 'DOM12', name: 'Electronics Manufacturing', sector: 'SEC06' },
    { id: 'DOM13', name: 'Renewable Energy', sector: 'SEC07' },
    { id: 'DOM14', name: 'Oil & Gas', sector: 'SEC07' },
    { id: 'DOM15', name: 'Military Defense', sector: 'SEC08' },
    { id: 'DOM16', name: 'Intelligence', sector: 'SEC08' },
    { id: 'DOM17', name: 'Air Transportation', sector: 'SEC09' },
    { id: 'DOM18', name: 'Rail Transportation', sector: 'SEC09' },
    { id: 'DOM19', name: 'Crop Farming', sector: 'SEC10' },
    { id: 'DOM20', name: 'Food Processing', sector: 'SEC10' }
  ];
  
  // Method data (Axis 4)
  const methods = [
    { id: 'MTH01', name: 'Research Methods', type: 'mega' },
    { id: 'MTH02', name: 'Analysis Methods', type: 'mega' },
    { id: 'MTH03', name: 'Design Methods', type: 'mega' },
    { id: 'MTH04', name: 'Implementation Methods', type: 'mega' },
    { id: 'MTH05', name: 'Evaluation Methods', type: 'mega' }
  ];
  
  // Simulated UKG axes
  const ukgAxes = [
    { id: 1, name: 'Knowledge (Pillar Levels)', entityCount: pillarLevels.length },
    { id: 2, name: 'Sectors', entityCount: sectors.length },
    { id: 3, name: 'Domains', entityCount: domains.length },
    { id: 4, name: 'Methods', entityCount: methods.length },
    { id: 5, name: 'Roles', entityCount: 24 },
    { id: 6, name: 'Problems', entityCount: 53 },
    { id: 7, name: 'Solutions', entityCount: 67 },
    { id: 8, name: 'Knowledge Expert', entityCount: 42 },
    { id: 9, name: 'Sector Expert', entityCount: 32 },
    { id: 10, name: 'Regulatory Expert', entityCount: 38 },
    { id: 11, name: 'Compliance Expert', entityCount: 29 },
    { id: 12, name: 'Location', entityCount: 187 },
    { id: 13, name: 'Time', entityCount: 35 }
  ];
  
  // Generate graph data based on active axis
  useEffect(() => {
    let nodes = [];
    let links = [];
    
    switch (activeAxis) {
      case 1: // Pillar Levels (Axis 1)
        // Create category nodes
        const categories = [...new Set(pillarLevels.map(pl => pl.category))];
        nodes = [
          ...categories.map(category => ({
            id: category,
            name: category,
            val: 10,
            color: '#3182CE',
            group: 'category'
          })),
          ...pillarLevels.map(pl => ({
            id: pl.id,
            name: `${pl.id}: ${pl.name}`,
            val: 5,
            color: '#38A169',
            group: 'pillar'
          }))
        ];
        
        // Create links from categories to pillars
        links = pillarLevels.map(pl => ({
          source: pl.category,
          target: pl.id
        }));
        break;
        
      case 2: // Sectors (Axis 2)
        nodes = sectors.map(sector => ({
          id: sector.id,
          name: sector.name,
          val: 8,
          color: '#DD6B20',
          group: 'sector'
        }));
        
        // Add subsector nodes
        sectors.forEach(sector => {
          sector.subsectors.forEach((subsector, idx) => {
            const subsectorId = `${sector.id}_SUB${idx + 1}`;
            nodes.push({
              id: subsectorId,
              name: subsector,
              val: 4,
              color: '#ED8936',
              group: 'subsector'
            });
            
            links.push({
              source: sector.id,
              target: subsectorId
            });
          });
        });
        break;
        
      case 3: // Domains (Axis 3)
        // Add sectors first
        nodes = sectors.map(sector => ({
          id: sector.id,
          name: sector.name,
          val: 8,
          color: '#DD6B20',
          group: 'sector'
        }));
        
        // Add domains
        domains.forEach(domain => {
          nodes.push({
            id: domain.id,
            name: domain.name,
            val: 5,
            color: '#805AD5',
            group: 'domain'
          });
          
          links.push({
            source: domain.sector,
            target: domain.id
          });
        });
        break;
        
      default:
        // For other axes, create a placeholder visualization
        // Central node
        nodes.push({
          id: 'axis',
          name: `Axis ${activeAxis}: ${ukgAxes.find(a => a.id === activeAxis)?.name}`,
          val: 15,
          color: '#3182CE',
          group: 'axis'
        });
        
        // Create sample entities
        for (let i = 1; i <= 15; i++) {
          const entityId = `entity${i}`;
          nodes.push({
            id: entityId,
            name: `Sample Entity ${i}`,
            val: 5 + Math.random() * 5,
            color: ['#38A169', '#DD6B20', '#805AD5', '#E53E3E', '#F6AD55'][Math.floor(Math.random() * 5)],
            group: 'entity'
          });
          
          links.push({
            source: 'axis',
            target: entityId
          });
          
          // Add some cross-connections
          if (i > 1 && Math.random() > 0.7) {
            links.push({
              source: entityId,
              target: `entity${Math.floor(Math.random() * (i - 1)) + 1}`
            });
          }
        }
        break;
    }
    
    setGraphData({ nodes, links });
    
  }, [activeAxis]);
  
  // Run a simulation
  const runUkgSimulation = () => {
    setSimulating(true);
    setSimulationProgress(0);
    
    toast({
      title: 'UKG Simulation Started',
      description: `Running simulation across Axis ${activeAxis} and related dimensions`,
      status: 'info',
      duration: 3000,
      isClosable: true
    });
    
    // Simulate progress updates
    const interval = setInterval(() => {
      setSimulationProgress(prev => {
        const newProgress = prev + Math.random() * 10;
        if (newProgress >= 100) {
          clearInterval(interval);
          
          toast({
            title: 'Simulation Complete',
            description: 'UKG simulation completed successfully',
            status: 'success',
            duration: 3000,
            isClosable: true
          });
          
          setSimulating(false);
          return 100;
        }
        return newProgress;
      });
    }, 600);
  };
  
  // Download current visualization
  const downloadVisualization = () => {
    if (graphRef.current) {
      const canvas = document.querySelector('canvas');
      if (canvas) {
        const image = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.href = image;
        link.download = `ukg-axis-${activeAxis}-visualization.png`;
        link.click();
        
        toast({
          title: 'Download Complete',
          description: 'Visualization downloaded as PNG image',
          status: 'success',
          duration: 2000,
          isClosable: true
        });
      }
    }
  };
  
  // Zoom controls
  const zoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 0.2, 2.5));
    if (graphRef.current) {
      graphRef.current.zoom(zoomLevel + 0.2);
    }
  };
  
  const zoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 0.2, 0.5));
    if (graphRef.current) {
      graphRef.current.zoom(zoomLevel - 0.2);
    }
  };
  
  const resetView = () => {
    setZoomLevel(1);
    if (graphRef.current) {
      graphRef.current.centerAt();
      graphRef.current.zoom(1);
    }
  };
  
  // Render node information panel
  const renderNodeInfo = () => {
    if (!selectedNode) {
      return (
        <Box p={4} textAlign="center" color="gray.500">
          <Text>Select a node to view details</Text>
        </Box>
      );
    }
    
    return (
      <VStack spacing={4} align="stretch">
        <Flex justify="space-between" align="center">
          <Heading size="md">{selectedNode.name}</Heading>
          <Badge colorScheme="blue">{selectedNode.group}</Badge>
        </Flex>
        
        <Divider />
        
        <Box>
          <Text fontWeight="bold" mb={1}>Node ID</Text>
          <Text>{selectedNode.id}</Text>
        </Box>
        
        <Box>
          <Text fontWeight="bold" mb={1}>Group</Text>
          <Text>{selectedNode.group}</Text>
        </Box>
        
        <Box>
          <Text fontWeight="bold" mb={1}>Connected Nodes</Text>
          <Text>
            {graphData.links.filter(link => link.source.id === selectedNode.id || link.target.id === selectedNode.id).length}
          </Text>
        </Box>
        
        <Divider />
        
        <HStack spacing={4}>
          <Button
            leftIcon={<FiCpu />}
            colorScheme="brand"
            onClick={() => {
              toast({
                title: 'Node Simulation',
                description: `Running UKG simulation on ${selectedNode.name}`,
                status: 'info',
                duration: 2000,
                isClosable: true
              });
            }}
            size="sm"
          >
            Simulate This Node
          </Button>
          
          <Button
            leftIcon={<FiMaximize />}
            onClick={() => {
              if (graphRef.current) {
                graphRef.current.centerAt(selectedNode.x, selectedNode.y, 1000);
                graphRef.current.zoom(1.5, 1000);
              }
            }}
            size="sm"
          >
            Focus
          </Button>
        </HStack>
        
        <Divider />
        
        <Box>
          <Text fontWeight="bold" mb={2}>UKG Cross-Axis Connections</Text>
          
          <VStack align="stretch" spacing={2}>
            {[...Array(3)].map((_, i) => {
              const randomAxis = ukgAxes[Math.floor(Math.random() * ukgAxes.length)];
              return (
                <HStack key={i} bg="dark.800" p={2} borderRadius="md">
                  <Badge>Axis {randomAxis.id}</Badge>
                  <Text fontSize="sm" flex="1">
                    {randomAxis.name}
                  </Text>
                  <Badge colorScheme="green">
                    {Math.floor(Math.random() * 10) + 1} links
                  </Badge>
                </HStack>
              );
            })}
          </VStack>
        </Box>
      </VStack>
    );
  };
  
  return (
    <Box h="100%" display="flex" flexDirection="column">
      <HStack mb={4} justify="space-between">
        <Heading size="lg">Universal Knowledge Graph Simulation Map</Heading>
        
        <HStack>
          <Select 
            value={activeAxis} 
            onChange={(e) => setActiveAxis(parseInt(e.target.value))}
            bg="dark.800"
            minW="260px"
          >
            {ukgAxes.map(axis => (
              <option key={axis.id} value={axis.id}>
                Axis {axis.id}: {axis.name}
              </option>
            ))}
          </Select>
          
          <Button
            leftIcon={<FiCpu />}
            colorScheme="brand"
            onClick={runUkgSimulation}
            isLoading={simulating}
            loadingText="Simulating..."
          >
            Run UKG Simulation
          </Button>
        </HStack>
      </HStack>
      
      {simulating && (
        <Box mb={4}>
          <Text mb={1}>Simulating UKG across axes... {Math.round(simulationProgress)}%</Text>
          <Progress
            value={simulationProgress}
            size="sm"
            colorScheme="brand"
            hasStripe
            isAnimated
          />
        </Box>
      )}
      
      <Flex flex="1" gap={4}>
        {/* Graph Visualization */}
        <Box flex="1" position="relative" bg="dark.800" borderRadius="md" overflow="hidden">
          {/* When ForceGraph2D is loaded */}
          {ForceGraph2D && (
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              nodeLabel="name"
              nodeColor={node => node.color}
              nodeVal={node => node.val}
              linkColor={() => '#5A6268'}
              onNodeClick={node => setSelectedNode(node)}
              cooldownTicks={100}
              onEngineStop={() => console.log('Engine stopped')}
              width={window.innerWidth - 600}
              height={600}
              backgroundColor="#1A1D23"
            />
          )}
          
          {/* Fall back when ForceGraph2D is not loaded */}
          {!ForceGraph2D && (
            <Flex h="100%" align="center" justify="center" direction="column">
              <Text fontSize="lg" mb={4}>Graph Visualization</Text>
              <Text color="gray.500">
                Force Graph component not loaded. Please refresh or check dependencies.
              </Text>
            </Flex>
          )}
          
          {/* Control panel overlay */}
          <HStack 
            position="absolute" 
            top="10px" 
            right="10px"
            bg="rgba(0, 0, 0, 0.6)"
            p={2}
            borderRadius="md"
            spacing={2}
          >
            <Tooltip label="Zoom In">
              <IconButton
                icon={<FiZoomIn />}
                onClick={zoomIn}
                size="sm"
                variant="ghost"
                aria-label="Zoom in"
              />
            </Tooltip>
            
            <Tooltip label="Zoom Out">
              <IconButton
                icon={<FiZoomOut />}
                onClick={zoomOut}
                size="sm"
                variant="ghost"
                aria-label="Zoom out"
              />
            </Tooltip>
            
            <Tooltip label="Reset View">
              <IconButton
                icon={<FiRefreshCw />}
                onClick={resetView}
                size="sm"
                variant="ghost"
                aria-label="Reset view"
              />
            </Tooltip>
            
            <Tooltip label="Download Visualization">
              <IconButton
                icon={<FiDownload />}
                onClick={downloadVisualization}
                size="sm"
                variant="ghost"
                aria-label="Download"
              />
            </Tooltip>
          </HStack>
          
          {/* Legend overlay */}
          <Box
            position="absolute"
            bottom="10px"
            left="10px"
            bg="rgba(0, 0, 0, 0.6)"
            p={3}
            borderRadius="md"
            maxW="300px"
          >
            <Text fontWeight="bold" mb={2}>Legend</Text>
            
            <Grid templateColumns="1fr 3fr" gap={2}>
              <Box w="16px" h="16px" borderRadius="full" bg="#3182CE" />
              <Text fontSize="sm">Category / Axis</Text>
              
              <Box w="16px" h="16px" borderRadius="full" bg="#38A169" />
              <Text fontSize="sm">Pillar Level</Text>
              
              <Box w="16px" h="16px" borderRadius="full" bg="#DD6B20" />
              <Text fontSize="sm">Sector</Text>
              
              <Box w="16px" h="16px" borderRadius="full" bg="#ED8936" />
              <Text fontSize="sm">Subsector</Text>
              
              <Box w="16px" h="16px" borderRadius="full" bg="#805AD5" />
              <Text fontSize="sm">Domain</Text>
            </Grid>
          </Box>
        </Box>
        
        {/* Right Panel - Details & Controls */}
        <Card w="300px" bg="dark.700" variant="outline">
          <Tabs variant="soft-rounded" colorScheme="brand" size="sm">
            <TabList px={4} pt={4}>
              <Tab>Details</Tab>
              <Tab>UKG Layers</Tab>
            </TabList>
            
            <TabPanels>
              <TabPanel>
                {renderNodeInfo()}
              </TabPanel>
              
              <TabPanel>
                <VStack align="stretch" spacing={4}>
                  <Heading size="sm">Simulation Layers</Heading>
                  
                  <VStack align="stretch" spacing={2}>
                    {[...Array(10)].map((_, i) => {
                      const layerNum = i + 1;
                      return (
                        <HStack key={layerNum} bg="dark.800" p={2} borderRadius="md">
                          <Badge colorScheme="brand">L{layerNum}</Badge>
                          <Text fontSize="sm" flex="1">
                            {
                              layerNum === 1 ? "Entry Layer" :
                              layerNum === 2 ? "Knowledge Layer" :
                              layerNum === 3 ? "Research Agents" :
                              layerNum === 4 ? "POV Engine" :
                              layerNum === 5 ? "Integration Layer" :
                              layerNum === 6 ? "Analysis Layer" :
                              layerNum === 7 ? "AGI System" :
                              layerNum === 8 ? "Quantum Computer" :
                              layerNum === 9 ? "Recursive AGI Core" :
                              "Self-Awareness Engine"
                            }
                          </Text>
                          <Badge colorScheme={layerNum <= 7 ? "green" : "gray"}>
                            {layerNum <= 7 ? "Active" : "Standby"}
                          </Badge>
                        </HStack>
                      );
                    })}
                  </VStack>
                  
                  <Divider />
                  
                  <Box>
                    <Heading size="sm" mb={3}>UKG Axes Overview</Heading>
                    
                    <VStack align="stretch" spacing={2}>
                      <Text fontSize="sm">
                        The Universal Knowledge Graph uses a 13-axis system to organize and synthesize knowledge across multiple domains and perspectives.
                      </Text>
                      
                      <Text fontSize="sm">
                        Current visualization shows Axis {activeAxis}: {ukgAxes.find(a => a.id === activeAxis)?.name} with {ukgAxes.find(a => a.id === activeAxis)?.entityCount} mapped entities.
                      </Text>
                    </VStack>
                  </Box>
                  
                  <Button
                    leftIcon={<FiActivity />}
                    colorScheme="brand"
                    size="sm"
                    onClick={() => {
                      toast({
                        title: "Layer Activation",
                        description: "This would activate additional UKG layers for deeper analysis",
                        status: "info",
                        duration: 2000,
                        isClosable: true
                      });
                    }}
                  >
                    Activate Layer 8-10
                  </Button>
                </VStack>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Card>
      </Flex>
    </Box>
  );
};

export default SimulationMapPage;