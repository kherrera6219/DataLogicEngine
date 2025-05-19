import React, { useState, useRef } from 'react';
import {
  Box,
  Flex,
  Text,
  HStack,
  VStack,
  Button,
  IconButton,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Select,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Card,
  CardBody,
  CardHeader,
  CardFooter,
  Image,
  AspectRatio,
  Badge,
  Divider,
  Grid,
  GridItem,
  InputGroup,
  InputRightElement,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Progress,
  useToast,
  Switch,
  Tag,
  TagLabel,
  TagCloseButton,
  Stack,
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
  FiImage,
  FiVideo,
  FiSliders,
  FiDownload,
  FiUpload,
  FiSave,
  FiTrash2,
  FiRefreshCw,
  FiPlus,
  FiSettings,
  FiPlay,
  FiPause,
  FiAlertCircle,
  FiInfo,
  FiList,
  FiGrid,
  FiCpu,
  FiCheck,
  FiX,
  FiTrendingUp,
  FiZap,
  FiMaximize,
  FiEdit2
} from 'react-icons/fi';

const MediaStudioPage = () => {
  const toast = useToast();
  const [activeTab, setActiveTab] = useState('image');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [viewMode, setViewMode] = useState('grid');
  const previewModal = useDisclosure();
  
  // Image Generation State
  const [imagePrompt, setImagePrompt] = useState('');
  const [imageSize, setImageSize] = useState('1024x1024');
  const [imageStyle, setImageStyle] = useState('photorealistic');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [imageTags, setImageTags] = useState(['Universal Knowledge Graph', 'UKG', '13-axis']);
  
  // Video Generation State
  const [videoPrompt, setVideoPrompt] = useState('');
  const [videoDuration, setVideoDuration] = useState(10);
  const [videoResolution, setVideoResolution] = useState('720p');
  const [videoStyle, setVideoStyle] = useState('cinematic');
  
  // Generated Content
  const [generatedImages, setGeneratedImages] = useState([
    {
      id: 1,
      url: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31',
      prompt: 'A visualization of the Universal Knowledge Graph with interconnected nodes representing the 13-axis system',
      timestamp: '2025-05-19T14:30:00Z',
      width: 1024,
      height: 1024,
      style: 'digital art',
      ukgAxes: [3, 8, 13]
    },
    {
      id: 2,
      url: 'https://images.unsplash.com/photo-1551808525-51a94da548ce',
      prompt: 'An abstract representation of knowledge transfer between quad persona experts',
      timestamp: '2025-05-19T15:15:00Z',
      width: 1024,
      height: 1024,
      style: 'abstract',
      ukgAxes: [8, 9, 10, 11]
    }
  ]);
  
  const [generatedVideos, setGeneratedVideos] = useState([
    {
      id: 1,
      thumbnailUrl: 'https://images.unsplash.com/photo-1550745165-9bc0b252726f',
      url: '#',
      prompt: 'A 3D flythrough of the Universal Knowledge Graph showing data flows between simulation layers',
      timestamp: '2025-05-19T16:20:00Z',
      duration: 15,
      resolution: '720p',
      style: 'cinematic',
      ukgAxes: [1, 2, 3, 4, 5, 6, 7, 8]
    }
  ]);
  
  const [selectedMedia, setSelectedMedia] = useState(null);
  
  // Reference for scrolling to results
  const resultsRef = useRef(null);
  
  // Handle adding a tag
  const handleAddTag = (tag) => {
    if (tag && !imageTags.includes(tag)) {
      setImageTags([...imageTags, tag]);
    }
  };
  
  // Handle removing a tag
  const handleRemoveTag = (tag) => {
    setImageTags(imageTags.filter(t => t !== tag));
  };
  
  // Generate image
  const generateImage = () => {
    if (!imagePrompt) {
      toast({
        title: "Prompt Required",
        description: "Please enter a description of what you want to generate",
        status: "warning",
        duration: 3000,
        isClosable: true
      });
      return;
    }
    
    // Begin generation
    setIsGenerating(true);
    setGenerationProgress(0);
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      setGenerationProgress(prev => {
        const newProgress = prev + Math.random() * 10;
        if (newProgress >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return newProgress;
      });
    }, 500);
    
    // Simulate completion after 5 seconds
    setTimeout(() => {
      clearInterval(progressInterval);
      setGenerationProgress(100);
      
      // Create a new generated image
      const newImage = {
        id: generatedImages.length + 1,
        url: 'https://images.unsplash.com/photo-1580584126903-c17d41830450',
        prompt: imagePrompt,
        timestamp: new Date().toISOString(),
        width: imageSize.split('x')[0],
        height: imageSize.split('x')[1],
        style: imageStyle,
        ukgAxes: [3, 5, 8] // Random UKG axes for simulation
      };
      
      setGeneratedImages([newImage, ...generatedImages]);
      setSelectedMedia(newImage);
      setIsGenerating(false);
      
      // Scroll to results
      if (resultsRef.current) {
        resultsRef.current.scrollIntoView({ behavior: 'smooth' });
      }
      
      toast({
        title: "Image Generated",
        description: "Your image has been created using UKG simulation",
        status: "success",
        duration: 3000,
        isClosable: true
      });
    }, 5000);
  };
  
  // Generate video
  const generateVideo = () => {
    if (!videoPrompt) {
      toast({
        title: "Prompt Required",
        description: "Please enter a description of what you want to generate",
        status: "warning",
        duration: 3000,
        isClosable: true
      });
      return;
    }
    
    // Begin generation
    setIsGenerating(true);
    setGenerationProgress(0);
    
    // Simulate progress (slower for video)
    const progressInterval = setInterval(() => {
      setGenerationProgress(prev => {
        const newProgress = prev + Math.random() * 5;
        if (newProgress >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return newProgress;
      });
    }, 800);
    
    // Simulate completion after 10 seconds
    setTimeout(() => {
      clearInterval(progressInterval);
      setGenerationProgress(100);
      
      // Create a new generated video
      const newVideo = {
        id: generatedVideos.length + 1,
        thumbnailUrl: 'https://images.unsplash.com/photo-1617854818583-09e7f077a156',
        url: '#',
        prompt: videoPrompt,
        timestamp: new Date().toISOString(),
        duration: videoDuration,
        resolution: videoResolution,
        style: videoStyle,
        ukgAxes: [1, 3, 7, 13] // Random UKG axes for simulation
      };
      
      setGeneratedVideos([newVideo, ...generatedVideos]);
      setSelectedMedia(newVideo);
      setIsGenerating(false);
      
      // Scroll to results
      if (resultsRef.current) {
        resultsRef.current.scrollIntoView({ behavior: 'smooth' });
      }
      
      toast({
        title: "Video Generated",
        description: "Your video has been created using UKG simulation",
        status: "success",
        duration: 3000,
        isClosable: true
      });
    }, 10000);
  };
  
  // Format timestamp
  const formatTime = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString([], {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return 'Invalid date';
    }
  };
  
  return (
    <Box h="100%" display="flex" flexDirection="column">
      <Flex mb={6} justify="space-between" align="center">
        <Text fontSize="2xl" fontWeight="bold">Media Studio</Text>
        
        <HStack>
          <Button
            leftIcon={<FiUpload />}
            size="sm"
            variant="outline"
            onClick={() => {
              toast({
                title: "Upload Feature",
                description: "This would allow you to upload your own media for UKG enhancement",
                status: "info",
                duration: 3000,
                isClosable: true
              });
            }}
          >
            Upload Media
          </Button>
          
          <Menu>
            <MenuButton as={Button} rightIcon={<FiSettings />} size="sm">
              Settings
            </MenuButton>
            <MenuList>
              <MenuItem>API Settings</MenuItem>
              <MenuItem>Output Preferences</MenuItem>
              <MenuItem>Advanced UKG Integration</MenuItem>
            </MenuList>
          </Menu>
        </HStack>
      </Flex>
      
      <Tabs 
        variant="soft-rounded" 
        colorScheme="brand" 
        isFitted 
        mb={6}
        index={activeTab === 'image' ? 0 : 1}
        onChange={(index) => setActiveTab(index === 0 ? 'image' : 'video')}
      >
        <TabList>
          <Tab><HStack><FiImage /><Text>Image Generation</Text></HStack></Tab>
          <Tab><HStack><FiVideo /><Text>Video Generation</Text></HStack></Tab>
        </TabList>
        
        <TabPanels mt={4}>
          {/* Image Generation Tab */}
          <TabPanel p={0}>
            <Card bg="dark.700" variant="outline" mb={6}>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <FormControl>
                    <FormLabel fontWeight="semibold">Image Description</FormLabel>
                    <Textarea
                      placeholder="Describe the image you want to generate in detail..."
                      value={imagePrompt}
                      onChange={(e) => setImagePrompt(e.target.value)}
                      rows={3}
                      bg="dark.800"
                      isDisabled={isGenerating}
                    />
                  </FormControl>
                  
                  <HStack spacing={4}>
                    <FormControl>
                      <FormLabel>Size</FormLabel>
                      <Select
                        value={imageSize}
                        onChange={(e) => setImageSize(e.target.value)}
                        bg="dark.800"
                        isDisabled={isGenerating}
                      >
                        <option value="1024x1024">1024×1024</option>
                        <option value="1024x1792">1024×1792 (Portrait)</option>
                        <option value="1792x1024">1792×1024 (Landscape)</option>
                      </Select>
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel>Style</FormLabel>
                      <Select
                        value={imageStyle}
                        onChange={(e) => setImageStyle(e.target.value)}
                        bg="dark.800"
                        isDisabled={isGenerating}
                      >
                        <option value="photorealistic">Photorealistic</option>
                        <option value="digital art">Digital Art</option>
                        <option value="3d render">3D Render</option>
                        <option value="cinematic">Cinematic</option>
                        <option value="abstract">Abstract</option>
                        <option value="anime">Anime</option>
                        <option value="technical">Technical Diagram</option>
                      </Select>
                    </FormControl>
                  </HStack>
                  
                  <FormControl>
                    <FormLabel>Negative Prompt (what to avoid)</FormLabel>
                    <Input
                      placeholder="Elements to exclude from the image..."
                      value={negativePrompt}
                      onChange={(e) => setNegativePrompt(e.target.value)}
                      bg="dark.800"
                      isDisabled={isGenerating}
                    />
                  </FormControl>
                  
                  <FormControl>
                    <FormLabel>Tags</FormLabel>
                    <HStack mb={2}>
                      <Input
                        placeholder="Add tags..."
                        bg="dark.800"
                        size="sm"
                        isDisabled={isGenerating}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            handleAddTag(e.target.value);
                            e.target.value = '';
                          }
                        }}
                      />
                      <IconButton
                        icon={<FiPlus />}
                        size="sm"
                        isDisabled={isGenerating}
                        onClick={(e) => {
                          const input = e.target.previousSibling;
                          handleAddTag(input.value);
                          input.value = '';
                        }}
                      />
                    </HStack>
                    
                    <Flex wrap="wrap" gap={2}>
                      {imageTags.map((tag, index) => (
                        <Tag
                          key={index}
                          size="md"
                          borderRadius="full"
                          variant="solid"
                          colorScheme="brand"
                        >
                          <TagLabel>{tag}</TagLabel>
                          <TagCloseButton onClick={() => handleRemoveTag(tag)} />
                        </Tag>
                      ))}
                    </Flex>
                  </FormControl>
                  
                  <Divider />
                  
                  <HStack justify="space-between">
                    <FormControl display="flex" alignItems="center" maxW="300px">
                      <FormLabel htmlFor="ukg-integration" mb="0" fontSize="sm">
                        UKG Integration
                      </FormLabel>
                      <Switch
                        id="ukg-integration"
                        colorScheme="brand"
                        defaultChecked
                        isDisabled={isGenerating}
                      />
                    </FormControl>
                    
                    <HStack>
                      <Button
                        leftIcon={<FiRefreshCw />}
                        onClick={() => {
                          setImagePrompt('');
                          setNegativePrompt('');
                          setImageStyle('photorealistic');
                          setImageSize('1024x1024');
                        }}
                        isDisabled={isGenerating || !imagePrompt}
                        variant="outline"
                      >
                        Reset
                      </Button>
                      
                      <Button
                        leftIcon={<FiZap />}
                        colorScheme="brand"
                        onClick={generateImage}
                        isLoading={isGenerating && activeTab === 'image'}
                        loadingText="Generating..."
                        isDisabled={isGenerating || !imagePrompt}
                      >
                        Generate Image
                      </Button>
                    </HStack>
                  </HStack>
                  
                  {isGenerating && activeTab === 'image' && (
                    <Box>
                      <Text mb={1} fontSize="sm">Generating image... {Math.round(generationProgress)}%</Text>
                      <Progress
                        value={generationProgress}
                        size="sm"
                        colorScheme="brand"
                        hasStripe
                        isAnimated
                        borderRadius="md"
                      />
                    </Box>
                  )}
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
          
          {/* Video Generation Tab */}
          <TabPanel p={0}>
            <Card bg="dark.700" variant="outline" mb={6}>
              <CardBody>
                <VStack spacing={4} align="stretch">
                  <FormControl>
                    <FormLabel fontWeight="semibold">Video Description</FormLabel>
                    <Textarea
                      placeholder="Describe the video you want to generate in detail..."
                      value={videoPrompt}
                      onChange={(e) => setVideoPrompt(e.target.value)}
                      rows={3}
                      bg="dark.800"
                      isDisabled={isGenerating}
                    />
                  </FormControl>
                  
                  <HStack spacing={4}>
                    <FormControl>
                      <FormLabel>Duration (seconds)</FormLabel>
                      <HStack>
                        <Slider
                          value={videoDuration}
                          min={5}
                          max={30}
                          step={1}
                          onChange={(val) => setVideoDuration(val)}
                          flex="1"
                          isDisabled={isGenerating}
                          colorScheme="brand"
                        >
                          <SliderTrack>
                            <SliderFilledTrack />
                          </SliderTrack>
                          <SliderThumb boxSize={6} />
                        </Slider>
                        <Text width="40px" textAlign="center">{videoDuration}s</Text>
                      </HStack>
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel>Resolution</FormLabel>
                      <Select
                        value={videoResolution}
                        onChange={(e) => setVideoResolution(e.target.value)}
                        bg="dark.800"
                        isDisabled={isGenerating}
                      >
                        <option value="480p">480p</option>
                        <option value="720p">720p (HD)</option>
                        <option value="1080p">1080p (Full HD)</option>
                      </Select>
                    </FormControl>
                  </HStack>
                  
                  <FormControl>
                    <FormLabel>Style</FormLabel>
                    <Select
                      value={videoStyle}
                      onChange={(e) => setVideoStyle(e.target.value)}
                      bg="dark.800"
                      isDisabled={isGenerating}
                    >
                      <option value="cinematic">Cinematic</option>
                      <option value="3d animation">3D Animation</option>
                      <option value="2d animation">2D Animation</option>
                      <option value="data visualization">Data Visualization</option>
                      <option value="lifelike">Lifelike</option>
                      <option value="stylized">Stylized</option>
                    </Select>
                  </FormControl>
                  
                  <Divider />
                  
                  <HStack justify="space-between">
                    <FormControl display="flex" alignItems="center" maxW="300px">
                      <FormLabel htmlFor="audio-enabled" mb="0" fontSize="sm">
                        Generate Audio
                      </FormLabel>
                      <Switch
                        id="audio-enabled"
                        colorScheme="brand"
                        defaultChecked
                        isDisabled={isGenerating}
                      />
                    </FormControl>
                    
                    <HStack>
                      <Button
                        leftIcon={<FiRefreshCw />}
                        onClick={() => {
                          setVideoPrompt('');
                          setVideoStyle('cinematic');
                          setVideoDuration(10);
                          setVideoResolution('720p');
                        }}
                        isDisabled={isGenerating || !videoPrompt}
                        variant="outline"
                      >
                        Reset
                      </Button>
                      
                      <Button
                        leftIcon={<FiZap />}
                        colorScheme="brand"
                        onClick={generateVideo}
                        isLoading={isGenerating && activeTab === 'video'}
                        loadingText="Generating..."
                        isDisabled={isGenerating || !videoPrompt}
                      >
                        Generate Video
                      </Button>
                    </HStack>
                  </HStack>
                  
                  {isGenerating && activeTab === 'video' && (
                    <Box>
                      <Text mb={1} fontSize="sm">Generating video... {Math.round(generationProgress)}%</Text>
                      <Progress
                        value={generationProgress}
                        size="sm"
                        colorScheme="brand"
                        hasStripe
                        isAnimated
                        borderRadius="md"
                      />
                    </Box>
                  )}
                </VStack>
              </CardBody>
            </Card>
          </TabPanel>
        </TabPanels>
      </Tabs>
      
      {/* Results Section */}
      <Box ref={resultsRef}>
        <Flex mb={4} justify="space-between" align="center">
          <Text fontSize="xl" fontWeight="semibold">
            Generated {activeTab === 'image' ? 'Images' : 'Videos'}
          </Text>
          
          <HStack>
            <IconButton
              icon={<FiGrid />}
              aria-label="Grid view"
              size="sm"
              colorScheme={viewMode === 'grid' ? 'brand' : 'gray'}
              variant={viewMode === 'grid' ? 'solid' : 'outline'}
              onClick={() => setViewMode('grid')}
            />
            <IconButton
              icon={<FiList />}
              aria-label="List view"
              size="sm"
              colorScheme={viewMode === 'list' ? 'brand' : 'gray'}
              variant={viewMode === 'list' ? 'solid' : 'outline'}
              onClick={() => setViewMode('list')}
            />
          </HStack>
        </Flex>
        
        {viewMode === 'grid' ? (
          // Grid View
          <Grid
            templateColumns={{ base: "repeat(1, 1fr)", md: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" }}
            gap={4}
          >
            {activeTab === 'image' ? (
              generatedImages.map(image => (
                <GridItem key={image.id}>
                  <Card
                    bg="dark.800"
                    overflow="hidden"
                    borderWidth={selectedMedia?.id === image.id ? "2px" : "1px"}
                    borderColor={selectedMedia?.id === image.id ? "brand.500" : "transparent"}
                    onClick={() => setSelectedMedia(image)}
                    _hover={{ borderColor: "brand.500", cursor: "pointer" }}
                    h="100%"
                  >
                    <AspectRatio ratio={16 / 9} maxH="200px">
                      <Image
                        src={image.url}
                        alt={image.prompt}
                        objectFit="cover"
                      />
                    </AspectRatio>
                    
                    <CardBody py={3}>
                      <VStack align="stretch" spacing={2}>
                        <Text fontWeight="semibold" noOfLines={2}>
                          {image.prompt}
                        </Text>
                        
                        <Flex wrap="wrap" gap={1}>
                          <Badge size="sm">{image.style}</Badge>
                          <Badge size="sm">{image.width}×{image.height}</Badge>
                        </Flex>
                        
                        <HStack justify="space-between" mt={1}>
                          <Text fontSize="xs" color="gray.500">
                            {formatTime(image.timestamp)}
                          </Text>
                          
                          <HStack>
                            <IconButton
                              icon={<FiMaximize />}
                              size="xs"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedMedia(image);
                                previewModal.onOpen();
                              }}
                            />
                            <IconButton
                              icon={<FiDownload />}
                              size="xs"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                toast({
                                  title: "Download Started",
                                  status: "success",
                                  duration: 2000,
                                  isClosable: true
                                });
                              }}
                            />
                          </HStack>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>
                </GridItem>
              ))
            ) : (
              generatedVideos.map(video => (
                <GridItem key={video.id}>
                  <Card
                    bg="dark.800"
                    overflow="hidden"
                    borderWidth={selectedMedia?.id === video.id ? "2px" : "1px"}
                    borderColor={selectedMedia?.id === video.id ? "brand.500" : "transparent"}
                    onClick={() => setSelectedMedia(video)}
                    _hover={{ borderColor: "brand.500", cursor: "pointer" }}
                    h="100%"
                  >
                    <AspectRatio ratio={16 / 9} maxH="200px" position="relative">
                      <Box>
                        <Image
                          src={video.thumbnailUrl}
                          alt={video.prompt}
                          objectFit="cover"
                          w="100%"
                          h="100%"
                        />
                        
                        <Flex
                          position="absolute"
                          top="0"
                          left="0"
                          w="100%"
                          h="100%"
                          align="center"
                          justify="center"
                          bg="rgba(0, 0, 0, 0.3)"
                          opacity="0"
                          _hover={{ opacity: "1" }}
                          transition="opacity 0.2s"
                        >
                          <IconButton
                            icon={<FiPlay />}
                            colorScheme="brand"
                            size="lg"
                            isRound
                            onClick={(e) => {
                              e.stopPropagation();
                              toast({
                                title: "Video Playback",
                                description: "This would play the generated video",
                                status: "info",
                                duration: 2000,
                                isClosable: true
                              });
                            }}
                          />
                        </Flex>
                        
                        <Badge
                          position="absolute"
                          bottom="2"
                          right="2"
                          bg="black"
                          color="white"
                        >
                          {video.duration}s
                        </Badge>
                      </Box>
                    </AspectRatio>
                    
                    <CardBody py={3}>
                      <VStack align="stretch" spacing={2}>
                        <Text fontWeight="semibold" noOfLines={2}>
                          {video.prompt}
                        </Text>
                        
                        <Flex wrap="wrap" gap={1}>
                          <Badge size="sm">{video.style}</Badge>
                          <Badge size="sm">{video.resolution}</Badge>
                        </Flex>
                        
                        <HStack justify="space-between" mt={1}>
                          <Text fontSize="xs" color="gray.500">
                            {formatTime(video.timestamp)}
                          </Text>
                          
                          <HStack>
                            <IconButton
                              icon={<FiMaximize />}
                              size="xs"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedMedia(video);
                                previewModal.onOpen();
                              }}
                            />
                            <IconButton
                              icon={<FiDownload />}
                              size="xs"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                toast({
                                  title: "Download Started",
                                  status: "success",
                                  duration: 2000,
                                  isClosable: true
                                });
                              }}
                            />
                          </HStack>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>
                </GridItem>
              ))
            )}
          </Grid>
        ) : (
          // List View
          <VStack spacing={2} align="stretch">
            {activeTab === 'image' ? (
              generatedImages.map(image => (
                <Card
                  key={image.id}
                  bg="dark.800"
                  direction="row"
                  overflow="hidden"
                  borderWidth={selectedMedia?.id === image.id ? "2px" : "1px"}
                  borderColor={selectedMedia?.id === image.id ? "brand.500" : "transparent"}
                  onClick={() => setSelectedMedia(image)}
                  _hover={{ borderColor: "brand.500", cursor: "pointer" }}
                >
                  <Image
                    src={image.url}
                    alt={image.prompt}
                    objectFit="cover"
                    w="120px"
                    h="100%"
                  />
                  
                  <CardBody py={3}>
                    <Flex justify="space-between" h="100%">
                      <VStack align="start" spacing={1} flex="1">
                        <Text fontWeight="semibold" noOfLines={1}>
                          {image.prompt}
                        </Text>
                        
                        <Flex wrap="wrap" gap={1}>
                          <Badge size="sm">{image.style}</Badge>
                          <Badge size="sm">{image.width}×{image.height}</Badge>
                        </Flex>
                        
                        <Text fontSize="xs" color="gray.500" mt="auto">
                          {formatTime(image.timestamp)}
                        </Text>
                      </VStack>
                      
                      <VStack h="100%" justify="space-between">
                        <HStack>
                          <IconButton
                            icon={<FiMaximize />}
                            size="xs"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedMedia(image);
                              previewModal.onOpen();
                            }}
                          />
                          <IconButton
                            icon={<FiDownload />}
                            size="xs"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              toast({
                                title: "Download Started",
                                status: "success",
                                duration: 2000,
                                isClosable: true
                              });
                            }}
                          />
                        </HStack>
                        
                        <HStack spacing={1}>
                          {image.ukgAxes.map((axis, idx) => (
                            <Badge key={idx} colorScheme="brand" variant="outline" size="sm">
                              A{axis}
                            </Badge>
                          ))}
                        </HStack>
                      </VStack>
                    </Flex>
                  </CardBody>
                </Card>
              ))
            ) : (
              generatedVideos.map(video => (
                <Card
                  key={video.id}
                  bg="dark.800"
                  direction="row"
                  overflow="hidden"
                  borderWidth={selectedMedia?.id === video.id ? "2px" : "1px"}
                  borderColor={selectedMedia?.id === video.id ? "brand.500" : "transparent"}
                  onClick={() => setSelectedMedia(video)}
                  _hover={{ borderColor: "brand.500", cursor: "pointer" }}
                >
                  <Box position="relative" w="210px" h="120px">
                    <Image
                      src={video.thumbnailUrl}
                      alt={video.prompt}
                      objectFit="cover"
                      w="100%"
                      h="100%"
                    />
                    
                    <Flex
                      position="absolute"
                      top="0"
                      left="0"
                      w="100%"
                      h="100%"
                      align="center"
                      justify="center"
                      bg="rgba(0, 0, 0, 0.3)"
                      opacity="0"
                      _hover={{ opacity: "1" }}
                      transition="opacity 0.2s"
                    >
                      <IconButton
                        icon={<FiPlay />}
                        colorScheme="brand"
                        isRound
                        onClick={(e) => {
                          e.stopPropagation();
                          toast({
                            title: "Video Playback",
                            description: "This would play the generated video",
                            status: "info",
                            duration: 2000,
                            isClosable: true
                          });
                        }}
                      />
                    </Flex>
                    
                    <Badge
                      position="absolute"
                      bottom="2"
                      right="2"
                      bg="black"
                      color="white"
                    >
                      {video.duration}s
                    </Badge>
                  </Box>
                  
                  <CardBody py={3}>
                    <Flex justify="space-between" h="100%">
                      <VStack align="start" spacing={1} flex="1">
                        <Text fontWeight="semibold" noOfLines={2}>
                          {video.prompt}
                        </Text>
                        
                        <Flex wrap="wrap" gap={1}>
                          <Badge size="sm">{video.style}</Badge>
                          <Badge size="sm">{video.resolution}</Badge>
                        </Flex>
                        
                        <Text fontSize="xs" color="gray.500" mt="auto">
                          {formatTime(video.timestamp)}
                        </Text>
                      </VStack>
                      
                      <VStack h="100%" justify="space-between">
                        <HStack>
                          <IconButton
                            icon={<FiMaximize />}
                            size="xs"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedMedia(video);
                              previewModal.onOpen();
                            }}
                          />
                          <IconButton
                            icon={<FiDownload />}
                            size="xs"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              toast({
                                title: "Download Started",
                                status: "success",
                                duration: 2000,
                                isClosable: true
                              });
                            }}
                          />
                        </HStack>
                        
                        <HStack spacing={1}>
                          {video.ukgAxes.slice(0, 3).map((axis, idx) => (
                            <Badge key={idx} colorScheme="brand" variant="outline" size="sm">
                              A{axis}
                            </Badge>
                          ))}
                          {video.ukgAxes.length > 3 && (
                            <Badge colorScheme="brand" variant="outline" size="sm">
                              +{video.ukgAxes.length - 3}
                            </Badge>
                          )}
                        </HStack>
                      </VStack>
                    </Flex>
                  </CardBody>
                </Card>
              ))
            )}
          </VStack>
        )}
      </Box>
      
      {/* Preview Modal */}
      <Modal isOpen={previewModal.isOpen} onClose={previewModal.onClose} size="xl">
        <ModalOverlay />
        <ModalContent bg="dark.800">
          <ModalHeader>Media Preview</ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            {selectedMedia && (
              <VStack spacing={4} align="stretch">
                {/* Preview Image */}
                {activeTab === 'image' ? (
                  <Image
                    src={selectedMedia.url}
                    alt={selectedMedia.prompt}
                    borderRadius="md"
                    w="100%"
                  />
                ) : (
                  <AspectRatio ratio={16 / 9}>
                    <Box position="relative" borderRadius="md" overflow="hidden">
                      <Image
                        src={selectedMedia.thumbnailUrl}
                        alt={selectedMedia.prompt}
                        objectFit="cover"
                        w="100%"
                        h="100%"
                      />
                      
                      <Flex
                        position="absolute"
                        top="0"
                        left="0"
                        w="100%"
                        h="100%"
                        align="center"
                        justify="center"
                      >
                        <IconButton
                          icon={<FiPlay />}
                          colorScheme="brand"
                          size="lg"
                          isRound
                          onClick={() => {
                            toast({
                              title: "Video Playback",
                              description: "This would play the generated video",
                              status: "info",
                              duration: 2000,
                              isClosable: true
                            });
                          }}
                        />
                      </Flex>
                    </Box>
                  </AspectRatio>
                )}
                
                {/* Details */}
                <Box>
                  <Text fontWeight="bold" mb={2}>{selectedMedia.prompt}</Text>
                  
                  <Grid templateColumns="repeat(2, 1fr)" gap={4}>
                    <VStack align="start" spacing={1}>
                      <Text fontSize="sm" color="gray.400">Generated</Text>
                      <Text>{formatTime(selectedMedia.timestamp)}</Text>
                    </VStack>
                    
                    <VStack align="start" spacing={1}>
                      <Text fontSize="sm" color="gray.400">Style</Text>
                      <Badge>{selectedMedia.style}</Badge>
                    </VStack>
                    
                    <VStack align="start" spacing={1}>
                      <Text fontSize="sm" color="gray.400">
                        {activeTab === 'image' ? 'Dimensions' : 'Resolution'}
                      </Text>
                      <Text>
                        {activeTab === 'image' 
                          ? `${selectedMedia.width}×${selectedMedia.height}` 
                          : selectedMedia.resolution
                        }
                      </Text>
                    </VStack>
                    
                    <VStack align="start" spacing={1}>
                      <Text fontSize="sm" color="gray.400">UKG Axes</Text>
                      <Flex wrap="wrap" gap={1}>
                        {selectedMedia.ukgAxes.map((axis, idx) => (
                          <Badge key={idx} colorScheme="brand">A{axis}</Badge>
                        ))}
                      </Flex>
                    </VStack>
                  </Grid>
                </Box>
                
                <Divider />
                
                <Box>
                  <Text fontWeight="semibold" mb={2}>UKG Integration</Text>
                  <Text fontSize="sm" mb={3}>
                    This {activeTab === 'image' ? 'image' : 'video'} has been analyzed and enhanced using the Universal Knowledge Graph system. The generation process activated UKG Axes {selectedMedia.ukgAxes.join(', ')} to ensure optimal representation of key concepts.
                  </Text>
                  
                  <Button
                    leftIcon={<FiCpu />}
                    size="sm"
                    colorScheme="brand"
                    variant="outline"
                    onClick={() => {
                      toast({
                        title: "UKG Enhancement",
                        description: "This would apply additional UKG enhancements",
                        status: "info",
                        duration: 2000,
                        isClosable: true
                      });
                      previewModal.onClose();
                    }}
                  >
                    Run UKG Enhancement
                  </Button>
                </Box>
              </VStack>
            )}
          </ModalBody>
          
          <ModalFooter>
            <Button
              leftIcon={<FiEdit2 />}
              mr={3}
              onClick={() => {
                // Set editing parameters
                if (activeTab === 'image' && selectedMedia) {
                  setImagePrompt(selectedMedia.prompt);
                  // Update other fields as needed
                } else if (activeTab === 'video' && selectedMedia) {
                  setVideoPrompt(selectedMedia.prompt);
                  // Update other fields as needed
                }
                previewModal.onClose();
              }}
            >
              Edit Parameters
            </Button>
            
            <Button
              leftIcon={<FiDownload />}
              colorScheme="brand"
              onClick={() => {
                toast({
                  title: "Download Started",
                  status: "success",
                  duration: 2000,
                  isClosable: true
                });
                previewModal.onClose();
              }}
            >
              Download
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default MediaStudioPage;