import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Flex,
  Text,
  HStack,
  VStack,
  Button,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Divider,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Select,
  Badge,
  Card,
  CardBody,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverHeader,
  PopoverBody,
  PopoverArrow,
  PopoverCloseButton,
  Portal,
  Tooltip,
  useDisclosure,
  useToast
} from '@chakra-ui/react';
import { 
  FiSave, 
  FiDownload, 
  FiUpload, 
  FiPlus, 
  FiTrash2, 
  FiZoomIn, 
  FiZoomOut, 
  FiGrid, 
  FiEye,
  FiLink,
  FiCircle,
  FiSquare,
  FiTriangle,
  FiEdit2,
  FiMinus,
  FiSettings,
  FiPlusCircle,
  FiLayers,
  FiMoreVertical,
  FiCpu
} from 'react-icons/fi';

const CanvasPage = () => {
  const toast = useToast();
  const canvasRef = useRef(null);
  const [nodes, setNodes] = useState([
    { id: 1, type: 'concept', x: 200, y: 100, text: 'Regulatory Framework', color: '#3182CE' },
    { id: 2, type: 'concept', x: 400, y: 200, text: 'Compliance Requirements', color: '#38A169' },
    { id: 3, type: 'concept', x: 600, y: 100, text: 'Technical Implementation', color: '#DD6B20' },
    { id: 4, type: 'resource', x: 300, y: 300, text: 'FDA Guidelines', color: '#805AD5' },
    { id: 5, type: 'resource', x: 500, y: 350, text: 'HIPAA Standards', color: '#805AD5' }
  ]);
  
  const [edges, setEdges] = useState([
    { id: 1, source: 1, target: 2, label: 'defines', type: 'directed' },
    { id: 2, source: 2, target: 3, label: 'informs', type: 'directed' },
    { id: 3, source: 4, target: 1, label: 'part of', type: 'association' },
    { id: 4, source: 5, target: 2, label: 'contributes to', type: 'association' }
  ]);
  
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [canvasMode, setCanvasMode] = useState('select'); // select, add-node, add-edge, delete
  const [zoom, setZoom] = useState(1);
  const [canvasTitle, setCanvasTitle] = useState('UKG Knowledge Map - Regulatory Compliance');
  const [showGrid, setShowGrid] = useState(true);
  
  // Node editing
  const nodeEditProps = useDisclosure();
  const [nodeForm, setNodeForm] = useState({
    text: '',
    type: 'concept',
    color: '#3182CE',
    description: ''
  });
  
  // UKG integration
  const [ukgAxes, setUkgAxes] = useState([2, 3, 10, 11]);
  const [confidence, setConfidence] = useState(0.92);
  const [showLayers, setShowLayers] = useState(false);
  
  // Canvas simulation
  useEffect(() => {
    if (!canvasRef.current) return;
    const ctx = canvasRef.current.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    
    // Draw grid if enabled
    if (showGrid) {
      drawGrid(ctx);
    }
    
    // Draw edges
    edges.forEach(edge => {
      const source = nodes.find(n => n.id === edge.source);
      const target = nodes.find(n => n.id === edge.target);
      
      if (source && target) {
        drawEdge(ctx, source, target, edge);
      }
    });
    
    // Draw nodes
    nodes.forEach(node => {
      drawNode(ctx, node, node.id === selectedNode?.id);
    });
  }, [nodes, edges, selectedNode, selectedEdge, zoom, showGrid]);
  
  // Draw grid
  const drawGrid = (ctx) => {
    ctx.save();
    ctx.lineWidth = 0.5;
    ctx.strokeStyle = 'rgba(100, 100, 100, 0.2)';
    
    const gridSize = 20;
    const width = ctx.canvas.width;
    const height = ctx.canvas.height;
    
    // Draw vertical lines
    for (let x = 0; x <= width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    
    // Draw horizontal lines
    for (let y = 0; y <= height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    
    ctx.restore();
  };
  
  // Draw a node
  const drawNode = (ctx, node, isSelected) => {
    ctx.save();
    
    // Node shape
    ctx.fillStyle = node.color || '#3182CE';
    ctx.strokeStyle = isSelected ? '#FFFFFF' : '#000000';
    ctx.lineWidth = isSelected ? 3 : 1;
    
    if (node.type === 'concept') {
      // Draw circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, 25, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    } else if (node.type === 'resource') {
      // Draw rectangle
      ctx.beginPath();
      ctx.rect(node.x - 25, node.y - 20, 50, 40);
      ctx.fill();
      ctx.stroke();
    }
    
    // Node text
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(node.text, node.x, node.y);
    
    ctx.restore();
  };
  
  // Draw an edge
  const drawEdge = (ctx, source, target, edge) => {
    ctx.save();
    
    // Edge style
    ctx.strokeStyle = edge.id === selectedEdge?.id ? '#FFFFFF' : '#AAAAAA';
    ctx.lineWidth = edge.id === selectedEdge?.id ? 2 : 1;
    
    // Draw line
    ctx.beginPath();
    ctx.moveTo(source.x, source.y);
    ctx.lineTo(target.x, target.y);
    ctx.stroke();
    
    // Draw arrow if directed
    if (edge.type === 'directed') {
      const angle = Math.atan2(target.y - source.y, target.x - source.x);
      const arrowSize = 10;
      
      ctx.beginPath();
      ctx.moveTo(
        target.x - arrowSize * Math.cos(angle) + arrowSize * Math.sin(angle) * 0.5,
        target.y - arrowSize * Math.sin(angle) - arrowSize * Math.cos(angle) * 0.5
      );
      ctx.lineTo(target.x - arrowSize * Math.cos(angle), target.y - arrowSize * Math.sin(angle));
      ctx.lineTo(
        target.x - arrowSize * Math.cos(angle) - arrowSize * Math.sin(angle) * 0.5,
        target.y - arrowSize * Math.sin(angle) + arrowSize * Math.cos(angle) * 0.5
      );
      ctx.fillStyle = edge.id === selectedEdge?.id ? '#FFFFFF' : '#AAAAAA';
      ctx.fill();
    }
    
    // Draw label
    if (edge.label) {
      const midX = (source.x + target.x) / 2;
      const midY = (source.y + target.y) / 2;
      
      ctx.fillStyle = '#EEEEEE';
      ctx.font = '10px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      // Draw background
      const metrics = ctx.measureText(edge.label);
      const bgPadding = 3;
      ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
      ctx.fillRect(
        midX - metrics.width / 2 - bgPadding,
        midY - 7 - bgPadding,
        metrics.width + bgPadding * 2,
        14 + bgPadding * 2
      );
      
      // Draw text
      ctx.fillStyle = '#FFFFFF';
      ctx.fillText(edge.label, midX, midY);
    }
    
    ctx.restore();
  };
  
  // Handle canvas click
  const handleCanvasClick = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Different behavior based on current mode
    if (canvasMode === 'select') {
      // Check if clicked on a node
      const clickedNode = nodes.find(node => {
        if (node.type === 'concept') {
          return Math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2) <= 25;
        } else if (node.type === 'resource') {
          return (
            x >= node.x - 25 &&
            x <= node.x + 25 &&
            y >= node.y - 20 &&
            y <= node.y + 20
          );
        }
        return false;
      });
      
      if (clickedNode) {
        setSelectedNode(clickedNode);
        setSelectedEdge(null);
        return;
      }
      
      // Check if clicked on an edge
      const clickedEdge = edges.find(edge => {
        const source = nodes.find(n => n.id === edge.source);
        const target = nodes.find(n => n.id === edge.target);
        
        if (!source || !target) return false;
        
        // Check if click is near the line
        const lineLength = Math.sqrt((target.x - source.x) ** 2 + (target.y - source.y) ** 2);
        const distance = Math.abs(
          (target.y - source.y) * x - (target.x - source.x) * y + target.x * source.y - target.y * source.x
        ) / lineLength;
        
        // Check if click is between the endpoints
        const dotProduct = (x - source.x) * (target.x - source.x) + (y - source.y) * (target.y - source.y);
        const squaredLength = (target.x - source.x) ** 2 + (target.y - source.y) ** 2;
        
        return distance < 10 && dotProduct >= 0 && dotProduct <= squaredLength;
      });
      
      if (clickedEdge) {
        setSelectedEdge(clickedEdge);
        setSelectedNode(null);
        return;
      }
      
      // If clicked on empty space
      setSelectedNode(null);
      setSelectedEdge(null);
    } else if (canvasMode === 'add-node') {
      // Add a new node at click position
      const newNode = {
        id: Math.max(0, ...nodes.map(n => n.id)) + 1,
        type: nodeForm.type,
        x: x,
        y: y,
        text: nodeForm.text || 'New Node',
        color: nodeForm.color
      };
      
      setNodes([...nodes, newNode]);
      setSelectedNode(newNode);
      setCanvasMode('select');
      
      toast({
        title: "Node Added",
        description: `Added new ${nodeForm.type} node: ${nodeForm.text || 'New Node'}`,
        status: "success",
        duration: 2000,
        isClosable: true,
      });
    } else if (canvasMode === 'delete') {
      // Check if clicked on a node to delete
      const nodeIndex = nodes.findIndex(node => {
        if (node.type === 'concept') {
          return Math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2) <= 25;
        } else if (node.type === 'resource') {
          return (
            x >= node.x - 25 &&
            x <= node.x + 25 &&
            y >= node.y - 20 &&
            y <= node.y + 20
          );
        }
        return false;
      });
      
      if (nodeIndex !== -1) {
        const deletedNode = nodes[nodeIndex];
        const newNodes = [...nodes];
        newNodes.splice(nodeIndex, 1);
        setNodes(newNodes);
        
        // Also remove any edges connected to this node
        const newEdges = edges.filter(
          edge => edge.source !== deletedNode.id && edge.target !== deletedNode.id
        );
        setEdges(newEdges);
        
        toast({
          title: "Node Deleted",
          description: `Deleted node: ${deletedNode.text}`,
          status: "info",
          duration: 2000,
          isClosable: true,
        });
      }
      
      // Check if clicked on an edge to delete
      const edgeIndex = edges.findIndex(edge => {
        const source = nodes.find(n => n.id === edge.source);
        const target = nodes.find(n => n.id === edge.target);
        
        if (!source || !target) return false;
        
        const lineLength = Math.sqrt((target.x - source.x) ** 2 + (target.y - source.y) ** 2);
        const distance = Math.abs(
          (target.y - source.y) * x - (target.x - source.x) * y + target.x * source.y - target.y * source.x
        ) / lineLength;
        
        const dotProduct = (x - source.x) * (target.x - source.x) + (y - source.y) * (target.y - source.y);
        const squaredLength = (target.x - source.x) ** 2 + (target.y - source.y) ** 2;
        
        return distance < 10 && dotProduct >= 0 && dotProduct <= squaredLength;
      });
      
      if (edgeIndex !== -1) {
        const deletedEdge = edges[edgeIndex];
        const newEdges = [...edges];
        newEdges.splice(edgeIndex, 1);
        setEdges(newEdges);
        
        toast({
          title: "Edge Deleted",
          description: `Deleted relationship: ${deletedEdge.label || 'unnamed'}`,
          status: "info",
          duration: 2000,
          isClosable: true,
        });
      }
    }
  };
  
  // Handle node dragging
  const handleDragStart = (e) => {
    if (canvasMode !== 'select' || !selectedNode) return;
    
    const rect = canvasRef.current.getBoundingClientRect();
    const startX = e.clientX - rect.left;
    const startY = e.clientY - rect.top;
    
    const offsetX = startX - selectedNode.x;
    const offsetY = startY - selectedNode.y;
    
    const handleDrag = (e) => {
      const x = e.clientX - rect.left - offsetX;
      const y = e.clientY - rect.top - offsetY;
      
      setNodes(nodes.map(node => 
        node.id === selectedNode.id ? { ...node, x, y } : node
      ));
    };
    
    const handleDragEnd = () => {
      document.removeEventListener('mousemove', handleDrag);
      document.removeEventListener('mouseup', handleDragEnd);
    };
    
    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', handleDragEnd);
  };
  
  // Export canvas as image
  const exportCanvas = () => {
    const canvas = canvasRef.current;
    const dataURL = canvas.toDataURL('image/png');
    
    const a = document.createElement('a');
    a.href = dataURL;
    a.download = `${canvasTitle || 'ukg-knowledge-map'}.png`;
    a.click();
    
    toast({
      title: "Export Complete",
      description: "Canvas exported as PNG image",
      status: "success",
      duration: 2000,
      isClosable: true,
    });
  };
  
  // Open node editor
  const openNodeEditor = () => {
    if (selectedNode) {
      setNodeForm({
        text: selectedNode.text,
        type: selectedNode.type,
        color: selectedNode.color,
        description: selectedNode.description || ''
      });
      nodeEditProps.onOpen();
    } else if (canvasMode === 'add-node') {
      nodeEditProps.onOpen();
    }
  };
  
  // Update node
  const updateNode = () => {
    if (selectedNode) {
      setNodes(nodes.map(node => 
        node.id === selectedNode.id 
          ? { ...node, text: nodeForm.text, color: nodeForm.color, description: nodeForm.description } 
          : node
      ));
      
      setSelectedNode(prev => ({
        ...prev,
        text: nodeForm.text,
        color: nodeForm.color,
        description: nodeForm.description
      }));
      
      nodeEditProps.onClose();
      
      toast({
        title: "Node Updated",
        description: `Updated node: ${nodeForm.text}`,
        status: "success",
        duration: 2000,
        isClosable: true,
      });
    }
  };
  
  // Add an edge between two nodes
  const addEdge = () => {
    if (!selectedNode) {
      toast({
        title: "Select a Node",
        description: "Please select a source node first",
        status: "warning",
        duration: 2000,
        isClosable: true,
      });
      return;
    }
    
    // Set mode to add-edge and store the source node
    if (canvasMode !== 'add-edge-start' && canvasMode !== 'add-edge-end') {
      setCanvasMode('add-edge-start');
      toast({
        title: "Select Target Node",
        description: "Now click on the target node to create a connection",
        status: "info",
        duration: 2000,
        isClosable: true,
      });
    } else if (canvasMode === 'add-edge-start') {
      // When a target node is selected
      if (selectedNode) {
        const newEdge = {
          id: Math.max(0, ...edges.map(e => e.id)) + 1,
          source: selectedNode.id,
          target: 0, // Will be set when second node is selected
          label: 'relates to',
          type: 'directed'
        };
        
        setSelectedEdge(newEdge);
        setCanvasMode('add-edge-end');
      }
    } else if (canvasMode === 'add-edge-end') {
      // Complete the edge creation
      if (selectedNode && selectedEdge) {
        const sourceNode = nodes.find(n => n.id === selectedEdge.source);
        if (sourceNode.id !== selectedNode.id) {
          const finalEdge = {
            ...selectedEdge,
            target: selectedNode.id
          };
          
          setEdges([...edges, finalEdge]);
          setSelectedEdge(null);
          setCanvasMode('select');
          
          toast({
            title: "Edge Added",
            description: `Added new relationship: ${finalEdge.label}`,
            status: "success",
            duration: 2000,
            isClosable: true,
          });
        } else {
          toast({
            title: "Invalid Target",
            description: "Cannot connect a node to itself",
            status: "error",
            duration: 2000,
            isClosable: true,
          });
          setCanvasMode('select');
        }
      }
    }
  };
  
  // Run UKG Analysis
  const runUkgAnalysis = () => {
    toast({
      title: "UKG Analysis Started",
      description: "Mapping knowledge graph to UKG 13-axis system...",
      status: "info",
      duration: 2000,
      isClosable: true,
    });
    
    // Simulate UKG analysis
    setTimeout(() => {
      setUkgAxes([2, 3, 8, 10, 11, 13]);
      setConfidence(0.96);
      
      toast({
        title: "UKG Analysis Complete",
        description: "Knowledge graph mapped to 6 UKG axes with 96% confidence",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    }, 2000);
  };
  
  return (
    <Box h="100%" display="flex" flexDirection="column">
      <HStack mb={4} justify="space-between">
        <Text fontSize="2xl" fontWeight="bold">Canvas Mode</Text>
        
        <HStack>
          <Button
            leftIcon={<FiLayers />}
            size="sm"
            variant={showLayers ? "solid" : "outline"}
            colorScheme="brand"
            onClick={() => setShowLayers(!showLayers)}
          >
            UKG Layers
          </Button>
          
          <Button
            leftIcon={<FiCpu />}
            size="sm"
            colorScheme="green"
            onClick={runUkgAnalysis}
          >
            Run UKG Analysis
          </Button>
        </HStack>
      </HStack>
      
      <Flex flex="1" gap={4}>
        {/* Left Panel - Toolbox */}
        <VStack 
          spacing={4} 
          align="stretch" 
          minW="60px" 
          bg="dark.700" 
          p={2} 
          borderRadius="md"
        >
          <Tooltip label="Select Mode" placement="right">
            <IconButton
              icon={<FiEdit2 />}
              aria-label="Select Mode"
              size="lg"
              colorScheme={canvasMode === 'select' ? 'brand' : 'gray'}
              variant={canvasMode === 'select' ? 'solid' : 'ghost'}
              onClick={() => setCanvasMode('select')}
            />
          </Tooltip>
          
          <Tooltip label="Add Node" placement="right">
            <IconButton
              icon={<FiPlusCircle />}
              aria-label="Add Node"
              size="lg"
              colorScheme={canvasMode === 'add-node' ? 'brand' : 'gray'}
              variant={canvasMode === 'add-node' ? 'solid' : 'ghost'}
              onClick={() => {
                setCanvasMode('add-node');
                setNodeForm({
                  text: '',
                  type: 'concept',
                  color: '#3182CE',
                  description: ''
                });
                openNodeEditor();
              }}
            />
          </Tooltip>
          
          <Tooltip label="Add Connection" placement="right">
            <IconButton
              icon={<FiLink />}
              aria-label="Add Connection"
              size="lg"
              isDisabled={!selectedNode}
              colorScheme={canvasMode.startsWith('add-edge') ? 'brand' : 'gray'}
              variant={canvasMode.startsWith('add-edge') ? 'solid' : 'ghost'}
              onClick={addEdge}
            />
          </Tooltip>
          
          <Tooltip label="Delete" placement="right">
            <IconButton
              icon={<FiTrash2 />}
              aria-label="Delete"
              size="lg"
              colorScheme={canvasMode === 'delete' ? 'red' : 'gray'}
              variant={canvasMode === 'delete' ? 'solid' : 'ghost'}
              onClick={() => setCanvasMode('delete')}
            />
          </Tooltip>
          
          <Divider my={2} />
          
          <Tooltip label="Zoom In" placement="right">
            <IconButton
              icon={<FiZoomIn />}
              aria-label="Zoom In"
              size="lg"
              variant="ghost"
              onClick={() => setZoom(Math.min(zoom + 0.1, 2))}
            />
          </Tooltip>
          
          <Tooltip label="Zoom Out" placement="right">
            <IconButton
              icon={<FiZoomOut />}
              aria-label="Zoom Out"
              size="lg"
              variant="ghost"
              onClick={() => setZoom(Math.max(zoom - 0.1, 0.5))}
            />
          </Tooltip>
          
          <Tooltip label="Toggle Grid" placement="right">
            <IconButton
              icon={<FiGrid />}
              aria-label="Toggle Grid"
              size="lg"
              variant={showGrid ? 'solid' : 'ghost'}
              colorScheme={showGrid ? 'brand' : 'gray'}
              onClick={() => setShowGrid(!showGrid)}
            />
          </Tooltip>
          
          <Divider my={2} />
          
          <Tooltip label="Save Canvas" placement="right">
            <IconButton
              icon={<FiSave />}
              aria-label="Save Canvas"
              size="lg"
              variant="ghost"
              onClick={() => {
                toast({
                  title: "Canvas Saved",
                  description: "Your knowledge map has been saved to the UKG system",
                  status: "success",
                  duration: 2000,
                  isClosable: true,
                });
              }}
            />
          </Tooltip>
          
          <Tooltip label="Export as Image" placement="right">
            <IconButton
              icon={<FiDownload />}
              aria-label="Export as Image"
              size="lg"
              variant="ghost"
              onClick={exportCanvas}
            />
          </Tooltip>
        </VStack>
        
        {/* Main Canvas Area */}
        <Box 
          flex="1" 
          bg="dark.800" 
          borderRadius="md" 
          position="relative"
          onMouseDown={handleDragStart}
          onClick={handleCanvasClick}
        >
          <canvas 
            ref={canvasRef} 
            width="800" 
            height="600"
            style={{ 
              width: '100%', 
              height: '100%',
              background: 'rgb(23, 25, 35)'
            }}
          />
          
          {/* Canvas Title */}
          <HStack
            position="absolute"
            top="10px"
            left="10px"
            bg="rgba(0, 0, 0, 0.6)"
            px={3}
            py={1}
            borderRadius="md"
          >
            <Text fontSize="sm" fontWeight="bold">{canvasTitle}</Text>
            <IconButton
              icon={<FiEdit2 />}
              aria-label="Edit Title"
              size="xs"
              variant="ghost"
            />
          </HStack>
          
          {/* Canvas Info */}
          <Box
            position="absolute"
            bottom="10px"
            left="10px"
            bg="rgba(0, 0, 0, 0.6)"
            px={3}
            py={1}
            borderRadius="md"
          >
            <HStack spacing={3}>
              <Text fontSize="xs">Nodes: {nodes.length}</Text>
              <Text fontSize="xs">Connections: {edges.length}</Text>
              <Text fontSize="xs">Zoom: {Math.round(zoom * 100)}%</Text>
            </HStack>
          </Box>
          
          {/* UKG Layers Panel */}
          {showLayers && (
            <Box
              position="absolute"
              top="10px"
              right="10px"
              bg="rgba(0, 0, 0, 0.7)"
              borderRadius="md"
              p={4}
              maxW="300px"
            >
              <HStack mb={2} justify="space-between">
                <Text fontWeight="bold">UKG Analysis</Text>
                <Badge colorScheme={confidence >= 0.95 ? "green" : "yellow"}>
                  {Math.round(confidence * 100)}%
                </Badge>
              </HStack>
              
              <Text fontSize="sm" mb={3}>
                This knowledge map has been analyzed using the UKG 13-axis system.
              </Text>
              
              <Text fontSize="sm" fontWeight="semibold" mb={2}>
                Active UKG Axes:
              </Text>
              
              <Flex wrap="wrap" gap={2} mb={3}>
                {ukgAxes.map(axis => (
                  <Badge key={axis} colorScheme="brand">
                    Axis {axis}
                  </Badge>
                ))}
              </Flex>
              
              <Divider my={2} />
              
              <Text fontSize="xs" color="gray.400">
                Analyzed with UKG Layers 2, 3, and 4
              </Text>
            </Box>
          )}
        </Box>
        
        {/* Right Panel - Properties */}
        <Card w="300px" bg="dark.700" variant="outline">
          <Tabs variant="soft-rounded" colorScheme="brand" size="sm">
            <TabList px={4} pt={4}>
              <Tab>Properties</Tab>
              <Tab>UKG Context</Tab>
            </TabList>
            
            <TabPanels>
              <TabPanel>
                {selectedNode ? (
                  <VStack align="stretch" spacing={4}>
                    <Text fontWeight="bold">Selected Node</Text>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Text</FormLabel>
                      <Input 
                        value={selectedNode.text} 
                        readOnly 
                        size="sm"
                        bg="dark.800"
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Type</FormLabel>
                      <Badge>
                        {selectedNode.type.charAt(0).toUpperCase() + selectedNode.type.slice(1)}
                      </Badge>
                    </FormControl>
                    
                    <Box>
                      <Text fontSize="sm" mb={1}>Color</Text>
                      <Box 
                        bg={selectedNode.color} 
                        w="100%" 
                        h="24px" 
                        borderRadius="md"
                      />
                    </Box>
                    
                    <Button
                      leftIcon={<FiEdit2 />}
                      size="sm"
                      onClick={openNodeEditor}
                    >
                      Edit Node
                    </Button>
                    
                    <Divider />
                    
                    <Box>
                      <Text fontSize="sm" mb={2}>Connections</Text>
                      <VStack align="stretch" spacing={2}>
                        {edges
                          .filter(edge => edge.source === selectedNode.id || edge.target === selectedNode.id)
                          .map(edge => {
                            const isSource = edge.source === selectedNode.id;
                            const connectedNodeId = isSource ? edge.target : edge.source;
                            const connectedNode = nodes.find(n => n.id === connectedNodeId);
                            
                            return (
                              <HStack key={edge.id} bg="dark.800" p={2} borderRadius="md">
                                <Text fontSize="xs">
                                  {isSource ? 'To' : 'From'}: {connectedNode?.text}
                                </Text>
                                <Badge size="sm">{edge.label}</Badge>
                              </HStack>
                            );
                          })}
                      </VStack>
                    </Box>
                  </VStack>
                ) : selectedEdge ? (
                  <VStack align="stretch" spacing={4}>
                    <Text fontWeight="bold">Selected Connection</Text>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Label</FormLabel>
                      <Input 
                        value={selectedEdge.label} 
                        readOnly
                        size="sm"
                        bg="dark.800"
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Type</FormLabel>
                      <Badge>
                        {selectedEdge.type.charAt(0).toUpperCase() + selectedEdge.type.slice(1)}
                      </Badge>
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Connection</FormLabel>
                      <HStack>
                        <Text fontSize="sm">
                          {nodes.find(n => n.id === selectedEdge.source)?.text}
                        </Text>
                        <Text fontSize="sm">→</Text>
                        <Text fontSize="sm">
                          {nodes.find(n => n.id === selectedEdge.target)?.text}
                        </Text>
                      </HStack>
                    </FormControl>
                    
                    <Button
                      leftIcon={<FiTrash2 />}
                      size="sm"
                      colorScheme="red"
                      variant="outline"
                      onClick={() => {
                        setEdges(edges.filter(edge => edge.id !== selectedEdge.id));
                        setSelectedEdge(null);
                        
                        toast({
                          title: "Connection Deleted",
                          status: "info",
                          duration: 2000,
                          isClosable: true,
                        });
                      }}
                    >
                      Delete Connection
                    </Button>
                  </VStack>
                ) : (
                  <VStack align="stretch" spacing={4}>
                    <Text fontWeight="bold">Canvas Properties</Text>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Title</FormLabel>
                      <Input 
                        value={canvasTitle} 
                        onChange={(e) => setCanvasTitle(e.target.value)}
                        size="sm"
                        bg="dark.800"
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Canvas Size</FormLabel>
                      <HStack>
                        <Input 
                          value="800" 
                          size="sm"
                          bg="dark.800"
                          type="number"
                          w="80px"
                        />
                        <Text>×</Text>
                        <Input 
                          value="600" 
                          size="sm"
                          bg="dark.800"
                          type="number"
                          w="80px"
                        />
                      </HStack>
                    </FormControl>
                    
                    <Box>
                      <Text fontWeight="semibold" fontSize="sm" mb={2}>Canvas Statistics</Text>
                      <HStack>
                        <VStack align="stretch" flex="1">
                          <Text fontSize="xs" color="gray.400">Nodes</Text>
                          <Text fontWeight="bold">{nodes.length}</Text>
                        </VStack>
                        <VStack align="stretch" flex="1">
                          <Text fontSize="xs" color="gray.400">Connections</Text>
                          <Text fontWeight="bold">{edges.length}</Text>
                        </VStack>
                        <VStack align="stretch" flex="1">
                          <Text fontSize="xs" color="gray.400">Complexity</Text>
                          <Text fontWeight="bold">Medium</Text>
                        </VStack>
                      </HStack>
                    </Box>
                  </VStack>
                )}
              </TabPanel>
              
              <TabPanel>
                <VStack align="stretch" spacing={4}>
                  <Text fontWeight="bold">UKG Integration</Text>
                  
                  <Card bg="dark.800" size="sm">
                    <CardBody>
                      <VStack align="stretch" spacing={3}>
                        <HStack justify="space-between">
                          <Text fontSize="sm">Confidence</Text>
                          <Badge colorScheme={confidence >= 0.95 ? "green" : "yellow"}>
                            {Math.round(confidence * 100)}%
                          </Badge>
                        </HStack>
                        
                        <HStack justify="space-between">
                          <Text fontSize="sm">Mapped Axes</Text>
                          <Badge>{ukgAxes.length} / 13</Badge>
                        </HStack>
                        
                        <HStack justify="space-between">
                          <Text fontSize="sm">UKG Layers</Text>
                          <Badge>2, 3, 4</Badge>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>
                  
                  <Box>
                    <Text fontSize="sm" fontWeight="semibold" mb={2}>
                      Active UKG Axes:
                    </Text>
                    
                    <Flex wrap="wrap" gap={2} mb={3}>
                      {ukgAxes.map(axis => (
                        <Badge key={axis} colorScheme="brand">
                          Axis {axis}
                        </Badge>
                      ))}
                    </Flex>
                  </Box>
                  
                  <Box>
                    <Text fontSize="sm" fontWeight="semibold" mb={2}>
                      UKG Analysis:
                    </Text>
                    
                    <Text fontSize="sm">
                      This knowledge map provides a conceptual framework for regulatory compliance 
                      with strong mappings to Axis 10 (Regulatory Expert) and Axis 11 (Compliance Expert).
                      The framework can be applied across industries with appropriate domain-specific adaptations.
                    </Text>
                  </Box>
                  
                  <Button
                    leftIcon={<FiCpu />}
                    size="sm"
                    onClick={runUkgAnalysis}
                  >
                    Run UKG Analysis
                  </Button>
                </VStack>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Card>
      </Flex>
      
      {/* Node Editor Popover */}
      <Popover
        isOpen={nodeEditProps.isOpen}
        onClose={nodeEditProps.onClose}
        placement="right"
        closeOnBlur={false}
      >
        <PopoverContent bg="dark.700" borderColor="gray.600">
          <PopoverArrow bg="dark.700" />
          <PopoverCloseButton />
          <PopoverHeader fontWeight="bold">
            {selectedNode ? 'Edit Node' : 'Add New Node'}
          </PopoverHeader>
          <PopoverBody>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel fontSize="sm">Node Text</FormLabel>
                <Input 
                  value={nodeForm.text} 
                  onChange={(e) => setNodeForm({...nodeForm, text: e.target.value})}
                  placeholder="Enter node text"
                  size="sm"
                  bg="dark.800"
                />
              </FormControl>
              
              <FormControl>
                <FormLabel fontSize="sm">Node Type</FormLabel>
                <Select 
                  value={nodeForm.type} 
                  onChange={(e) => setNodeForm({...nodeForm, type: e.target.value})}
                  size="sm"
                  bg="dark.800"
                >
                  <option value="concept">Concept</option>
                  <option value="resource">Resource</option>
                </Select>
              </FormControl>
              
              <FormControl>
                <FormLabel fontSize="sm">Node Color</FormLabel>
                <Select 
                  value={nodeForm.color} 
                  onChange={(e) => setNodeForm({...nodeForm, color: e.target.value})}
                  size="sm"
                  bg="dark.800"
                >
                  <option value="#3182CE">Blue</option>
                  <option value="#38A169">Green</option>
                  <option value="#805AD5">Purple</option>
                  <option value="#DD6B20">Orange</option>
                  <option value="#E53E3E">Red</option>
                </Select>
              </FormControl>
              
              <FormControl>
                <FormLabel fontSize="sm">Description</FormLabel>
                <Textarea 
                  value={nodeForm.description} 
                  onChange={(e) => setNodeForm({...nodeForm, description: e.target.value})}
                  placeholder="Optional description"
                  size="sm"
                  bg="dark.800"
                  rows={3}
                />
              </FormControl>
              
              <Button
                onClick={selectedNode ? updateNode : () => {
                  setCanvasMode('add-node');
                  nodeEditProps.onClose();
                }}
                colorScheme="brand"
                size="sm"
              >
                {selectedNode ? 'Update Node' : 'Create Node'}
              </Button>
            </VStack>
          </PopoverBody>
        </PopoverContent>
      </Popover>
    </Box>
  );
};

export default CanvasPage;