import { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { marked } from 'marked';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [chatTitle, setChatTitle] = useState('New Conversation');
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState({
    confidenceThreshold: 0.85,
    enableLocationContext: true,
    enableResearchAgents: true,
    personas: {
      ke: true,
      se: true,
      re: true, 
      ce: true
    }
  });

  const messagesEndRef = useRef(null);
  const chatInputRef = useRef(null);

  // Initialize chat
  useEffect(() => {
    // Load chat history from local storage or API
    const loadChatHistory = async () => {
      try {
        // This would be replaced with an API call in a real implementation
        const savedHistory = localStorage.getItem('ukg_chat_history');
        if (savedHistory) {
          setChatHistory(JSON.parse(savedHistory));
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    };

    loadChatHistory();

    // Add welcome message
    setMessages([{
      id: 'welcome',
      type: 'system',
      content: `# Welcome to the UKG Chat System\n\nA comprehensive AI knowledge system with a 13-axis Universal Knowledge Graph. How can I help you today?`
    }]);
  }, []);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize text area
  useEffect(() => {
    if (chatInputRef.current) {
      chatInputRef.current.style.height = 'auto';
      chatInputRef.current.style.height = chatInputRef.current.scrollHeight + 'px';
    }
  }, [inputText]);

  const handleInputChange = (e) => {
    setInputText(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    // Add user message to chat
    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputText,
      timestamp: new Date().toISOString()
    };

    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      // Call API to get response
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: inputText,
          target_confidence: settings.confidenceThreshold,
          chat_id: currentChatId,
          use_location_context: settings.enableLocationContext,
          use_research_agents: settings.enableResearchAgents,
          active_personas: Object.entries(settings.personas)
            .filter(([_, isActive]) => isActive)
            .map(([key]) => key.toUpperCase())
        }),
      });

      const data = await response.json();

      // Update chat ID if this is a new conversation
      if (!currentChatId && data.chat_id) {
        setCurrentChatId(data.chat_id);

        // Create a new chat history item
        const newChatItem = {
          id: data.chat_id,
          title: generateChatTitle(inputText),
          created: new Date().toISOString(),
          lastUpdated: new Date().toISOString()
        };

        setChatHistory(prev => [newChatItem, ...prev]);
        setChatTitle(newChatItem.title);

        // Save to local storage (would be an API call in real implementation)
        localStorage.setItem('ukg_chat_history', JSON.stringify([newChatItem, ...chatHistory]));
      }

      // Add system response to chat
      const systemResponse = {
        id: `response-${Date.now()}`,
        type: 'system',
        content: data.error ? `Error: ${data.error}` : data.response,
        confidence: data.confidence,
        timestamp: new Date().toISOString()
      };

      setMessages(prevMessages => [...prevMessages, systemResponse]);
    } catch (error) {
      console.error('Error sending message:', error);

      // Add error message
      const errorMessage = {
        id: `error-${Date.now()}`,
        type: 'error',
        content: 'Sorry, there was an error processing your request. Please try again.',
        timestamp: new Date().toISOString()
      };

      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([{
      id: 'welcome',
      type: 'system',
      content: `# Welcome to the UKG Chat System\n\nA comprehensive AI knowledge system with a 13-axis Universal Knowledge Graph. How can I help you today?`
    }]);
    setCurrentChatId(null);
    setChatTitle('New Conversation');
  };

  const handleChatSelect = (chatId) => {
    // In a real implementation, this would load messages from the API
    const selectedChat = chatHistory.find(chat => chat.id === chatId);
    if (selectedChat) {
      setCurrentChatId(chatId);
      setChatTitle(selectedChat.title);
      setMessages([
        {
          id: 'welcome',
          type: 'system',
          content: `# ${selectedChat.title}\n\nContinuing your previous conversation.`
        }
      ]);
    }
  };

  const handleClearChats = () => {
    if (confirm('Are you sure you want to clear all chat history? This cannot be undone.')) {
      setChatHistory([]);
      localStorage.removeItem('ukg_chat_history');
      handleNewChat();
    }
  };

  const handleSaveSettings = () => {
    // In a real implementation, this would save settings to the API
    const modal = document.getElementById('settings-modal');
    if (modal) {
      const bootstrapModal = bootstrap.Modal.getInstance(modal);
      bootstrapModal.hide();
    }
  };

  const generateChatTitle = (firstMessage) => {
    if (!firstMessage) return 'New Conversation';
    // Truncate and clean up the message to create a title
    return firstMessage.length > 30 
      ? firstMessage.substring(0, 30) + '...' 
      : firstMessage;
  };

  // Import responsive utilities
  useEffect(() => {
    import('../utils/responsive').then(module => {
      const cleanupHandler = module.initResponsiveHandlers();
      return () => cleanupHandler();
    });
  }, []);

  return (
    <Layout>
      <Head>
        <title>UKG Chat Interface</title>
      </Head>

      <div className="chat-container">
        <div className="chat-sidebar">
          <div className="sidebar-header">
            <h5 className="mb-0">Chat History</h5>
            <button className="btn btn-sm btn-outline-light d-flex align-items-center">
              <i className="bi bi-plus-lg"></i>
            </button>
          </div>
          <div className="chat-history">
            {chatHistory.map((chat, index) => (
              <div 
                key={index} 
                className={`chat-history-item ${currentChatId === chat.id ? 'active' : ''}`}
                onClick={() => handleChatSelect(chat.id)}
              >
                <i className="bi bi-chat-left-text"></i>
                {chat.title}
              </div>
            ))}
            {chatHistory.length === 0 && (
              <div className="text-center text-muted p-3">
                <i className="bi bi-chat-square-text fs-3 mb-2"></i>
                <p>No chat history yet</p>
              </div>
            )}
          </div>
          <div className="sidebar-footer">
            <button className="btn btn-outline-light btn-sm w-100 d-flex align-items-center justify-content-center">
              <i className="bi bi-trash me-2"></i>
              Clear History
            </button>
          </div>
        </div>

        {/* Sidebar toggle button for mobile */}
        <button className="sidebar-toggle">
          <i className="bi bi-list"></i>
        </button>

        <div className="chat-main">
          <div className="chat-header">
            <h5 className="mb-0 d-flex align-items-center">
              <i className="bi bi-robot me-2 d-none d-sm-inline"></i>
              UKG Chat Assistant
            </h5>
            <div className="d-flex gap-2">
              <button className="btn btn-sm btn-outline-light d-flex align-items-center">
                <i className="bi bi-gear"></i>
                <span className="ms-1 d-none d-md-inline">Settings</span>
              </button>
              <button className="btn btn-sm btn-outline-light d-flex align-items-center">
                <i className="bi bi-question-circle"></i>
                <span className="ms-1 d-none d-md-inline">Help</span>
              </button>
            </div>
          </div>
          <div className="chat-messages" id="chat-messages">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h2>Welcome to the UKG Chat System</h2>
                <p>A comprehensive AI knowledge system with a 13-axis Universal Knowledge Graph.</p>
                <div className="suggestion-chips">
                  <div 
                    className="chip" 
                    onClick={() => setInputText("How does the UKG system work?")}
                  >
                    How does the UKG system work?
                  </div>
                  <div 
                    className="chip"
                    onClick={() => setInputText("Tell me about the 13 axes of knowledge")}
                  >
                    Tell me about the 13 axes of knowledge
                  </div>
                  <div 
                    className="chip"
                    onClick={() => setInputText("What are knowledge algorithms?")}
                  >
                    What are knowledge algorithms?
                  </div>
                </div>
              </div>
            ) : (
              messages.map(message => (
                <div key={message.id} className={`message ${message.type}`}>
                  {message.type === 'user' ? (
                    <>
                      <div className="message-avatar">
                        <i className="bi bi-person-circle"></i>
                      </div>
                      <div className="message-content">
                        <div className="message-text">{message.content}</div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="message-avatar system-avatar">
                        <i className="bi bi-robot"></i>
                      </div>
                      <div className="message-content">
                        <div 
                          className="message-text markdown-content"
                          dangerouslySetInnerHTML={{ __html: marked.parse(message.content) }}
                        ></div>
                        {message.confidence && (
                          <div className="message-metadata">
                            <span className="confidence-badge">
                              Confidence: {message.confidence}
                            </span>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              ))
            )}
            {isLoading && (
              <div className="message system">
                <div className="message-avatar system-avatar">
                  <i className="bi bi-robot"></i>
                </div>
                <div className="message-content">
                  <div className="message-text">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-input-container">
            <div className="position-relative w-100">
              <textarea 
                id="chat-input" 
                className="form-control" 
                placeholder="Ask a question..." 
                rows="1"
                value={inputText}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                ref={chatInputRef}
              />
              {inputText && (
                <button 
                  className="btn btn-sm btn-link position-absolute top-50 end-0 translate-middle-y text-secondary me-2"
                  type="button"
                  onClick={() => setInputText('')}
                  style={{ zIndex: 5 }}
                >
                  <i className="bi bi-x-circle"></i>
                </button>
              )}
            </div>
            <div className="input-buttons">
              <button 
                className="btn btn-outline-light d-flex align-items-center justify-content-center" 
                type="button"
                title="Upload file"
              >
                <i className="bi bi-paperclip"></i>
              </button>
              <button 
                className="btn btn-primary d-flex align-items-center justify-content-center" 
                type="button"
                onClick={handleSendMessage}
                disabled={!inputText.trim() || isLoading}
                style={{ minWidth: '48px', minHeight: '38px' }}
              >
                {isLoading ? (
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                ) : (
                  <i className="bi bi-send"></i>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Settings Modal */}
        <div className="modal fade" id="settings-modal" tabIndex="-1" aria-hidden="true">
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Chat Settings</h5>
                <button type="button" className="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <label htmlFor="confidence-threshold" className="form-label">
                    Target Confidence: <span id="confidence-value">{settings.confidenceThreshold}</span>
                  </label>
                  <input 
                    type="range" 
                    className="form-range" 
                    id="confidence-threshold" 
                    min="0.6" 
                    max="0.95" 
                    step="0.05" 
                    value={settings.confidenceThreshold}
                    onChange={(e) => setSettings({
                      ...settings,
                      confidenceThreshold: parseFloat(e.target.value)
                    })}
                  />
                </div>
                <div className="mb-3 form-check form-switch">
                  <input 
                    className="form-check-input" 
                    type="checkbox" 
                    id="enable-location-context"
                    checked={settings.enableLocationContext}
                    onChange={(e) => setSettings({
                      ...settings,
                      enableLocationContext: e.target.checked
                    })}
                  />
                  <label className="form-check-label" htmlFor="enable-location-context">
                    Enable Location Context
                  </label>
                </div>
                <div className="mb-3 form-check form-switch">
                  <input 
                    className="form-check-input" 
                    type="checkbox" 
                    id="enable-research-agents"
                    checked={settings.enableResearchAgents}
                    onChange={(e) => setSettings({
                      ...settings,
                      enableResearchAgents: e.target.checked
                    })}
                  />
                  <label className="form-check-label" htmlFor="enable-research-agents">
                    Enable Research Agents
                  </label>
                </div>
                <div className="mb-3">
                  <label className="form-label">Active Personas</label>
                  <div className="persona-toggles">
                    <div className="form-check form-switch">
                      <input 
                        className="form-check-input" 
                        type="checkbox" 
                        id="persona-ke"
                        checked={settings.personas.ke}
                        onChange={(e) => setSettings({
                          ...settings,
                          personas: {
                            ...settings.personas,
                            ke: e.target.checked
                          }
                        })}
                      />
                      <label className="form-check-label" htmlFor="persona-ke">
                        Knowledge Expert
                      </label>
                    </div>
                    <div className="form-check form-switch">
                      <input 
                        className="form-check-input" 
                        type="checkbox" 
                        id="persona-se"
                        checked={settings.personas.se}
                        onChange={(e) => setSettings({
                          ...settings,
                          personas: {
                            ...settings.personas,
                            se: e.target.checked
                          }
                        })}
                      />
                      <label className="form-check-label" htmlFor="persona-se">
                        Skill Expert
                      </label>
                    </div>
                    <div className="form-check form-switch">
                      <input 
                        className="form-check-input" 
                        type="checkbox" 
                        id="persona-re"
                        checked={settings.personas.re}
                        onChange={(e) => setSettings({
                          ...settings,
                          personas: {
                            ...settings.personas,
                            re: e.target.checked
                          }
                        })}
                      />
                      <label className="form-check-label" htmlFor="persona-re">
                        Role Expert
                      </label>
                    </div>
                    <div className="form-check form-switch">
                      <input 
                        className="form-check-input" 
                        type="checkbox" 
                        id="persona-ce"
                        checked={settings.personas.ce}
                        onChange={(e) => setSettings({
                          ...settings,
                          personas: {
                            ...settings.personas,
                            ce: e.target.checked
                          }
                        })}
                      />
                      <label className="form-check-label" htmlFor="persona-ce">
                        Context Expert
                      </label>
                    </div>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" className="btn btn-primary" id="save-settings" onClick={handleSaveSettings}>
                  Save changes
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}