import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Flex,
  Heading,
  Text,
  Select,
  Button,
  HStack,
  VStack,
  Card,
  CardHeader,
  CardBody,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  IconButton,
  Tooltip,
  Badge,
  Spinner,
  Grid,
  GridItem
} from '@chakra-ui/react';
import { FiZoomIn, FiZoomOut, FiRefreshCw, FiDownload, FiFilter } from 'react-icons/fi';
import ForceGraph2D from 'react-force-graph-2d';
import { useUKG } from '../contexts/UKGContext';
import { useNotification } from '../contexts/NotificationContext';

// Constants for axis colors
const AXIS_COLORS = {
  1: '#4299E1', // Knowledge (blue)
  2: '#48BB78', // Sectors (green)
  3: '#ECC94B', // Domains (yellow)
  4: '#ED8936', // Methods (orange)
  5: '#9F7AEA', // Contexts (purple)
  6: '#F56565', // Problems (red)
  7: '#38B2AC', // Solutions (teal)
  8: '#F687B3', // Roles (pink)
  9: '#DD6B20', // Experts (orange-dark)
  10: '#805AD5', // Regulations (purple-dark)
  11: '#D53F8C', // Compliance (pink-dark)
  12: '#718096', // Location (gray)
  13: '#2D3748'  // Time (gray-dark)
};

// Node types
const NODE_TYPES = [
  'All',
  'Knowledge',
  'Sector',
  'Domain',
  'Method',
  'Context',
  'Problem',
  'Solution',
  'Role',
  'Expert',
  'Regulation',
  'Compliance',
  'Location',
  'Time'
];

const SimulationMapPage = () => {
  // Graph state
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedAxis, setSelectedAxis] = useState(0); // 0 = all axes
  const [selectedType, setSelectedType] = useState('All');
  const [graphLoading, setGraphLoading] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [layoutStopped, setLayoutStopped] = useState(false);
  
  // References
  const graphRef = useRef(null);
  
  // Contexts
  const { getGraphData } = useUKG();
  const { error: showError, success } = useNotification();
  
  // Load graph data on initial render
  useEffect(() => {
    loadGraphData();
  }, []);
  
  // Load graph data with optional filters
  const loadGraphData = async (filters = {}) => {
    setGraphLoading(true);
    try {
      const result = await getGraphData({
        axis: selectedAxis > 0 ? selectedAxis : undefined,
        nodeType: selectedType !== 'All' ? selectedType.toLowerCase() : undefined,
        ...filters
      });
      
      if (result.success) {
        setGraphData(result.data);
        success('Graph data loaded successfully');
      } else {
        showError('Failed to load graph data');
      }
    } catch (err) {
      console.error('Error loading graph data:', err);
      showError('Error loading graph data');
    } finally {
      setGraphLoading(false);
    }
  };
  
  // Apply filters
  const applyFilters = () => {
    loadGraphData();
  };
  
  // Reset filters
  const resetFilters = () => {
    setSelectedAxis(0);
    setSelectedType('All');
    loadGraphData({ axis: undefined, nodeType: undefined });
  };
  
  // Handle node click
  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };
  
  // Zoom in
  const zoomIn = () => {
    if (graphRef.current) {
      const newZoom = zoomLevel * 1.2;
      setZoomLevel(newZoom);
      graphRef.current.zoom(newZoom);
    }
  };
  
  // Zoom out
  const zoomOut = () => {
    if (graphRef.current) {
      const newZoom = zoomLevel * 0.8;
      setZoomLevel(newZoom);
      graphRef.current.zoom(newZoom);
    }
  };
  
  // Export graph as PNG
  const exportGraph = () => {
    if (graphRef.current) {
      const canvas = document.querySelector('canvas');
      const link = document.createElement('a');
      link.download = 'ukg-graph.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    }
  };
  
  // Custom node paint function
  const paintNode = (node, ctx) => {
    const size = node.size || 8;
    ctx.beginPath();
    
    // Node fill color based on axis
    const axisNum = node.axis_number || 1;
    ctx.fillStyle = AXIS_COLORS[axisNum] || '#888';
    
    // Draw node
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fill();
    
    // Draw node border
    ctx.strokeStyle = node === selectedNode ? '#fff' : '#222';
    ctx.lineWidth = node === selectedNode ? 2 : 1;
    ctx.stroke();
    
    // Add text label for nodes
    if (size > 6 || node === selectedNode) {
      ctx.font = `${size > 12 ? 'bold ' : ''}${Math.max(size, 10)}px Inter`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = '#ffffff';
      // Draw text with background
      const textWidth = ctx.measureText(node.label).width;
      ctx.fillStyle = 'rgba(0,0,0,0.6)';
      ctx.fillRect(node.x - textWidth/2 - 2, node.y + size + 2, textWidth + 4, size + 4);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(node.label, node.x, node.y + size + size/2 + 2);
    }
  };
  
  // Custom link paint function
  const paintLink = (link, ctx) => {
    const sourceNode = link.source;
    const targetNode = link.target;
    
    // Draw link
    ctx.beginPath();
    ctx.moveTo(sourceNode.x, sourceNode.y);
    ctx.lineTo(targetNode.x, targetNode.y);
    
    // Link style based on type
    ctx.strokeStyle = link.color || '#ffffff30';
    ctx.lineWidth = link.width || 1;
    
    // Draw arrow
    const dx = targetNode.x - sourceNode.x;
    const dy = targetNode.y - sourceNode.y;
    const angle = Math.atan2(dy, dx);
    const length = Math.sqrt(dx * dx + dy * dy);
    const size = targetNode.size || 8;
    
    if (length > 0) {
      ctx.stroke();
      
      // Draw arrowhead if needed
      if (link.directed) {
        const arrowLength = Math.min(size, length / 3);
        const arrowWidth = arrowLength / 2;
        
        const x_end = targetNode.x - (size * Math.cos(angle));
        const y_end = targetNode.y - (size * Math.sin(angle));
        
        ctx.beginPath();
        ctx.moveTo(x_end, y_end);
        ctx.lineTo(
          x_end - arrowLength * Math.cos(angle - Math.PI / 6),
          y_end - arrowLength * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          x_end - arrowLength * Math.cos(angle + Math.PI / 6),
          y_end - arrowLength * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fillStyle = link.color || '#ffffff50';
        ctx.fill();
      }
    }
  };
  
  return (
    <Box h="full">
      <Grid templateColumns={{ base: '1fr', lg: '3fr 1fr' }} gap={4} h="full">
        {/* Graph Visualization */}
        <GridItem position="relative" bg="gray.800" borderRadius="md" overflow="hidden">
          {graphLoading && (
            <Flex 
              position="absolute" 
              top="0" 
              left="0" 
              right="0" 
              bottom="0" 
              bg="blackAlpha.700" 
              zIndex="1" 
              justify="center" 
              align="center"
            >
              <VStack>
                <Spinner size="xl" color="brand.500" thickness="4px" />
                <Text>Loading Knowledge Graph...</Text>
              </VStack>
            </Flex>
          )}
          
          {/* Graph Controls */}
          <Box position="absolute" top="10px" right="10px" zIndex="1">
            <VStack spacing={2}>
              <Tooltip label="Zoom In" placement="left">
                <IconButton 
                  icon={<FiZoomIn />} 
                  aria-label="Zoom In" 
                  onClick={zoomIn} 
                  colorScheme="gray" 
                  size="sm"
                />
              </Tooltip>
              <Tooltip label="Zoom Out" placement="left">
                <IconButton 
                  icon={<FiZoomOut />} 
                  aria-label="Zoom Out" 
                  onClick={zoomOut} 
                  colorScheme="gray" 
                  size="sm"
                />
              </Tooltip>
              <Tooltip label="Reset Graph" placement="left">
                <IconButton 
                  icon={<FiRefreshCw />} 
                  aria-label="Reset Graph" 
                  onClick={() => graphRef.current && graphRef.current.zoomToFit(400)} 
                  colorScheme="gray" 
                  size="sm"
                />
              </Tooltip>
              <Tooltip label="Export as PNG" placement="left">
                <IconButton 
                  icon={<FiDownload />} 
                  aria-label="Export" 
                  onClick={exportGraph} 
                  colorScheme="gray" 
                  size="sm"
                />
              </Tooltip>
              <Tooltip label={layoutStopped ? "Resume Layout" : "Pause Layout"} placement="left">
                <IconButton 
                  icon={<FiFilter />} 
                  aria-label="Toggle Layout" 
                  onClick={() => setLayoutStopped(!layoutStopped)} 
                  colorScheme={layoutStopped ? "brand" : "gray"} 
                  size="sm"
                />
              </Tooltip>
            </VStack>
          </Box>
          
          {/* Force Graph Component */}
          {graphData.nodes.length > 0 && (
            <ForceGraph2D
              ref={graphRef}
              graphData={graphData}
              nodeLabel={node => `${node.label} (${NODE_TYPES[node.axis_number || 1]})`}
              linkLabel={link => link.label || 'link'}
              nodeRelSize={8}
              nodeVal={node => node.value || 1}
              nodeColor={() => 'rgba(0,0,0,0)'}  // Use custom painting
              linkColor={() => 'rgba(0,0,0,0)'}  // Use custom painting
              linkWidth={1}
              nodeCanvasObjectMode={() => 'replace'}
              nodeCanvasObject={paintNode}
              linkCanvasObjectMode={() => 'replace'}
              linkCanvasObject={paintLink}
              onNodeClick={handleNodeClick}
              cooldownTicks={layoutStopped ? 0 : Infinity}
              onEngineStop={() => console.log('Engine stopped')}
              linkDirectionalArrowLength={3}
              linkDirectionalArrowRelPos={1}
              warmupTicks={100}
              onNodeHover={node => {
                document.body.style.cursor = node ? 'pointer' : 'default';
              }}
              width={800}
              height={600}
            />
          )}
        </GridItem>
        
        {/* Node Details & Controls Panel */}
        <GridItem>
          <VStack spacing={4} align="stretch" h="full">
            <Card variant="outline" bg="gray.800">
              <CardHeader pb={1}>
                <Heading size="md">Graph Controls</Heading>
              </CardHeader>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <Box>
                    <Text mb={2} fontWeight="medium">Filter by Axis</Text>
                    <Select 
                      value={selectedAxis} 
                      onChange={(e) => setSelectedAxis(Number(e.target.value))}
                      bg="gray.700"
                    >
                      <option value={0}>All Axes</option>
                      <option value={1}>Axis 1: Knowledge</option>
                      <option value={2}>Axis 2: Sectors</option>
                      <option value={3}>Axis 3: Domains</option>
                      <option value={4}>Axis 4: Methods</option>
                      <option value={5}>Axis 5: Contexts</option>
                      <option value={6}>Axis 6: Problems</option>
                      <option value={7}>Axis 7: Solutions</option>
                      <option value={8}>Axis 8: Roles</option>
                      <option value={9}>Axis 9: Experts</option>
                      <option value={10}>Axis 10: Regulations</option>
                      <option value={11}>Axis 11: Compliance</option>
                      <option value={12}>Axis 12: Location</option>
                      <option value={13}>Axis 13: Time</option>
                    </Select>
                  </Box>
                  
                  <Box>
                    <Text mb={2} fontWeight="medium">Filter by Node Type</Text>
                    <Select 
                      value={selectedType} 
                      onChange={(e) => setSelectedType(e.target.value)}
                      bg="gray.700"
                    >
                      {NODE_TYPES.map((type, index) => (
                        <option key={index} value={type}>{type}</option>
                      ))}
                    </Select>
                  </Box>
                  
                  <HStack spacing={2}>
                    <Button colorScheme="brand" flex="1" onClick={applyFilters}>
                      Apply Filters
                    </Button>
                    <Button variant="outline" flex="1" onClick={resetFilters}>
                      Reset
                    </Button>
                  </HStack>
                </VStack>
              </CardBody>
            </Card>
            
            <Card variant="outline" bg="gray.800" flex="1">
              <CardHeader pb={1}>
                <Heading size="md">Node Details</Heading>
              </CardHeader>
              <CardBody overflow="auto">
                {selectedNode ? (
                  <Tabs variant="enclosed" size="sm">
                    <TabList>
                      <Tab>Overview</Tab>
                      <Tab>Properties</Tab>
                      <Tab>Connections</Tab>
                    </TabList>
                    
                    <TabPanels>
                      <TabPanel>
                        <VStack align="stretch" spacing={3}>
                          <Box>
                            <Heading size="sm" mb={1}>{selectedNode.label}</Heading>
                            <HStack>
                              <Badge 
                                colorScheme={Object.keys(AXIS_COLORS)[selectedNode.axis_number - 1] || 'gray'}
                              >
                                {NODE_TYPES[selectedNode.axis_number || 1]}
                              </Badge>
                              <Badge>ID: {selectedNode.id}</Badge>
                            </HStack>
                          </Box>
                          
                          <Text fontSize="sm">
                            {selectedNode.description || 'No description available for this node.'}
                          </Text>
                          
                          {selectedNode.attributes && (
                            <Box>
                              <Text fontWeight="medium" fontSize="sm">Key Attributes:</Text>
                              {Object.entries(selectedNode.attributes).slice(0, 5).map(([key, value]) => (
                                <Text key={key} fontSize="xs">
                                  <strong>{key}:</strong> {String(value).substring(0, 60)}
                                  {String(value).length > 60 ? '...' : ''}
                                </Text>
                              ))}
                            </Box>
                          )}
                        </VStack>
                      </TabPanel>
                      
                      <TabPanel>
                        <VStack align="stretch" spacing={2}>
                          {selectedNode.attributes ? (
                            Object.entries(selectedNode.attributes).map(([key, value]) => (
                              <Box key={key} p={2} bg="gray.700" borderRadius="md">
                                <Text fontSize="xs" color="gray.400">{key}</Text>
                                <Text fontSize="sm" wordBreak="break-word">
                                  {typeof value === 'object' 
                                    ? JSON.stringify(value, null, 2) 
                                    : String(value)
                                  }
                                </Text>
                              </Box>
                            ))
                          ) : (
                            <Text color="gray.500">No properties available</Text>
                          )}
                        </VStack>
                      </TabPanel>
                      
                      <TabPanel>
                        <VStack align="stretch" spacing={2}>
                          <Text fontWeight="medium">Connected Nodes:</Text>
                          {graphData.links
                            .filter(link => 
                              link.source.id === selectedNode.id || 
                              link.target.id === selectedNode.id
                            )
                            .map((link, index) => {
                              const isSource = link.source.id === selectedNode.id;
                              const connectedNode = isSource ? link.target : link.source;
                              
                              return (
                                <Box 
                                  key={index} 
                                  p={2} 
                                  bg="gray.700" 
                                  borderRadius="md"
                                  _hover={{ bg: 'gray.600', cursor: 'pointer' }}
                                  onClick={() => setSelectedNode(connectedNode)}
                                >
                                  <HStack>
                                    <Box 
                                      w="3" 
                                      h="3" 
                                      borderRadius="full" 
                                      bg={AXIS_COLORS[connectedNode.axis_number || 1]}
                                    />
                                    <Text>{connectedNode.label}</Text>
                                    <Badge ml="auto" fontSize="xs">
                                      {isSource ? 'outgoing' : 'incoming'}
                                    </Badge>
                                  </HStack>
                                  <Text fontSize="xs" color="gray.400" ml="5">
                                    {link.label || (isSource ? 'connects to' : 'connected from')}
                                  </Text>
                                </Box>
                              );
                            })}
                          
                          {graphData.links.filter(link => 
                            link.source.id === selectedNode.id || 
                            link.target.id === selectedNode.id
                          ).length === 0 && (
                            <Text color="gray.500">No connections</Text>
                          )}
                        </VStack>
                      </TabPanel>
                    </TabPanels>
                  </Tabs>
                ) : (
                  <Flex 
                    direction="column" 
                    align="center" 
                    justify="center" 
                    h="full" 
                    color="gray.500"
                    textAlign="center"
                    p={4}
                  >
                    <Text mb={2}>No node selected</Text>
                    <Text fontSize="sm">
                      Click on a node in the graph to view its details and properties.
                    </Text>
                  </Flex>
                )}
              </CardBody>
            </Card>
          </VStack>
        </GridItem>
      </Grid>
    </Box>
  );
};

export default SimulationMapPage;