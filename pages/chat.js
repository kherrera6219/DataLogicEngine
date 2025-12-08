import { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { marked } from 'marked';
import ProductHeader from '../components/ProductHeader';

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [chatTitle, setChatTitle] = useState('New Conversation');
  const [isLoading, setIsLoading] = useState(false);
  const [inputMode, setInputMode] = useState('text');
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

  const quickPrompts = [
    'Summarize the 13 axes with one example per axis.',
    'Draft a SOC 2 control checklist for a new vendor.',
    'Map these requirements to the honeycomb crosswalk.',
    'Show me the regulatory spiderweb for healthcare.'
  ];

  const composerModes = [
    { id: 'text', label: 'Text', icon: 'type' },
    { id: 'voice', label: 'Voice', icon: 'mic' },
    { id: 'upload', label: 'Upload', icon: 'paperclip' }
  ];

  const personaOptions = [
    { id: 'ke', label: 'Knowledge Expert', icon: 'book' },
    { id: 'se', label: 'Skill Expert', icon: 'tools' },
    { id: 're', label: 'Role Expert', icon: 'person-badge' },
    { id: 'ce', label: 'Context Expert', icon: 'geo-alt' }
  ];

  const liveSignals = [
    { label: 'Latency', value: '42ms', tone: 'success' },
    { label: 'Token stream', value: '2.1k/s', tone: 'info' },
    { label: 'Confidence', value: `${Math.round(settings.confidenceThreshold * 100)}%`, tone: 'warning' }
  ];

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

      <ProductHeader
        title="Streaming chat"
        subtitle="Segmented multimodal composer with persona chips and compliance shortcuts"
        breadcrumbs={[
          { label: 'AI Workbench' },
          { label: 'Chat' }
        ]}
        actions={[
          { label: 'Open Graph', icon: 'diagram-3', href: '/knowledge-graph' },
          { label: 'Compliance pulse', icon: 'shield-check', href: '/compliance-dashboard' }
        ]}
      />

      <div className="chat-shell">
        <aside className="chat-sidebar p-3 d-flex flex-column gap-3">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <p className="section-title mb-1">Sessions</p>
              <h5 className="mb-0">AI Workbench</h5>
            </div>
            <div className="d-flex gap-2">
              <button className="btn btn-outline-light btn-sm rounded-pill" onClick={handleNewChat}>
                <i className="bi bi-plus-lg"></i>
              </button>
              <button className="btn btn-outline-light btn-sm rounded-pill" onClick={() => setInputText('/cmd ')}>
                <i className="bi bi-command"></i>
              </button>
            </div>
          </div>

          <div className="d-grid gap-2">
            {chatHistory.length === 0 && (
              <div className="glass-border p-3 text-center text-white-50">
                <i className="bi bi-chat-square-text fs-3 d-block mb-2"></i>
                Start a new conversation
              </div>
            )}
            {chatHistory.map((chat) => (
              <div
                key={chat.id}
                className={`glass-border p-3 cursor-pointer ${currentChatId === chat.id ? 'bg-primary bg-opacity-10' : ''}`}
                onClick={() => handleChatSelect(chat.id)}
              >
                <div className="d-flex justify-content-between align-items-center">
                  <div className="d-flex align-items-center gap-2">
                    <i className="bi bi-chat-left-text"></i>
                    <strong>{chat.title}</strong>
                  </div>
                  <span className="badge bg-secondary">{new Date(chat.created).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="d-grid gap-2">
            <button className="btn btn-outline-light btn-sm rounded-pill" onClick={handleClearChats}>
              <i className="bi bi-trash me-2"></i> Clear history
            </button>
            <button className="btn btn-outline-light btn-sm rounded-pill">
              <i className="bi bi-cloud-download me-2"></i> Export transcript
            </button>
          </div>
        </aside>

        <section className="chat-window">
          <div className="d-flex justify-content-between align-items-center flex-wrap gap-3">
            <div>
              <p className="section-title mb-1">Streaming chat</p>
              <h5 className="mb-0 text-white">{chatTitle}</h5>
            </div>
            <div className="d-flex gap-2 flex-wrap">
              {liveSignals.map((signal) => (
                <span key={signal.label} className={`badge bg-${signal.tone} bg-opacity-25 text-${signal.tone}`}>
                  {signal.label}: {signal.value}
                </span>
              ))}
            </div>
          </div>

          <div className="d-flex flex-wrap gap-2 align-items-center mb-3">
            <div className="btn-group" role="group" aria-label="Composer modes">
              {composerModes.map((mode) => (
                <button
                  key={mode.id}
                  type="button"
                  className={`btn btn-sm ${inputMode === mode.id ? 'btn-primary' : 'btn-outline-light'}`}
                  onClick={() => setInputMode(mode.id)}
                >
                  <i className={`bi bi-${mode.icon} me-1`}></i>
                  {mode.label}
                </button>
              ))}
            </div>

            <div className="d-flex gap-2 flex-wrap">
              {personaOptions.map((persona) => (
                <button
                  key={persona.id}
                  type="button"
                  className={`btn btn-sm rounded-pill ${settings.personas[persona.id] ? 'btn-outline-success' : 'btn-outline-secondary'}`}
                  onClick={() => setSettings({
                    ...settings,
                    personas: {
                      ...settings.personas,
                      [persona.id]: !settings.personas[persona.id]
                    }
                  })}
                >
                  <i className={`bi bi-${persona.icon} me-1`}></i>
                  {persona.label.split(' ')[0]}
                </button>
              ))}
            </div>

            <div className="ms-auto d-flex gap-2 flex-wrap align-items-center">
              <span className="badge bg-secondary">Context: {settings.enableLocationContext ? 'Location on' : 'Location off'}</span>
              <span className="badge bg-secondary">Agents: {settings.enableResearchAgents ? 'Research on' : 'Research off'}</span>
              <span className="badge bg-secondary">Mode: {inputMode}</span>
            </div>
          </div>

          <div className="overflow-auto mb-3 pb-1" style={{ whiteSpace: 'nowrap' }}>
            <div className="d-flex gap-2 flex-nowrap">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  className="glass-border p-3 rounded-3 text-start text-white-50"
                  style={{ minWidth: '240px' }}
                  onClick={() => setInputText(prompt)}
                >
                  <div className="d-flex align-items-center gap-2 mb-1 text-white">
                    <i className="bi bi-lightning-charge text-primary"></i>
                    <strong>Quick prompt</strong>
                  </div>
                  <span className="small">{prompt}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="flex-grow-1 overflow-auto" style={{ minHeight: '320px' }}>
            {messages.length === 0 ? (
              <div className="glass-border p-4 text-center">
                <h4 className="text-white">Welcome to the UKG Chat System</h4>
                <p className="text-white-50">Pick a persona mix, provide a prompt, or jump into a knowledge graph query.</p>
                <div className="d-flex gap-2 flex-wrap justify-content-center">
                  {quickPrompts.map((prompt) => (
                    <button key={prompt} className="btn btn-outline-light btn-sm rounded-pill" onClick={() => setInputText(prompt)}>
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div key={message.id} className={`message-bubble ${message.type} mb-2`}>
                  <div className="d-flex align-items-start gap-2">
                    <div className="avatar bg-primary bg-opacity-25 rounded-circle d-flex align-items-center justify-content-center" style={{ width: '32px', height: '32px' }}>
                      <i className={`bi ${message.type === 'user' ? 'bi-person' : 'bi-robot'}`}></i>
                    </div>
                    <div className="flex-grow-1">
                      <div
                        className="markdown-content"
                        dangerouslySetInnerHTML={{ __html: marked.parse(message.content) }}
                      ></div>
                      {message.confidence && (
                        <small className="text-white-50">Confidence: {message.confidence}</small>
                      )}
                      {message.type === 'system' && (
                        <div className="d-flex flex-wrap gap-2 mt-2">
                          <span className="badge bg-dark border text-white-50">Sources mapped</span>
                          <span className="badge bg-dark border text-white-50">Confidence badge</span>
                          <button className="btn btn-outline-light btn-sm rounded-pill"><i className="bi bi-diagram-3 me-1"></i>Open in Graph</button>
                          <button className="btn btn-outline-light btn-sm rounded-pill"><i className="bi bi-file-earmark-text me-1"></i>Generate Report</button>
                          <button className="btn btn-outline-light btn-sm rounded-pill"><i className="bi bi-bookmark me-1"></i>Bookmark</button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="message-bubble system mb-2">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <div className="skeleton mt-2" style={{ height: '12px', width: '60%' }}></div>
                <div className="skeleton mt-2" style={{ height: '12px', width: '40%' }}></div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="glass-border p-3 input-rail">
            <div className="d-flex gap-3 flex-wrap small text-white-50 mb-2">
              <span><i className="bi bi-activity me-1"></i>Streaming</span>
              <span><i className="bi bi-lightning-charge me-1"></i>Tokens/sec: 2.1k</span>
              <span><i className="bi bi-speedometer2 me-1"></i>Latency under 200ms</span>
            </div>
            <div className="d-flex gap-2 align-items-center mb-2 flex-wrap">
              <span className="badge bg-secondary">Cmd/Ctrl + K: Command palette</span>
              <span className="badge bg-secondary">Shift + Enter: New line</span>
              <span className="badge bg-secondary">Streaming on</span>
            </div>
            <div className="position-relative">
              <textarea
                className="form-control bg-dark text-white"
                placeholder="Ask a question, paste context, or use /commands..."
                rows="2"
                value={inputText}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                ref={chatInputRef}
              />
              {inputText && (
                <button
                  className="btn btn-sm btn-link position-absolute top-0 end-0 text-secondary"
                  type="button"
                  onClick={() => setInputText('')}
                  style={{ zIndex: 5 }}
                >
                  <i className="bi bi-x-circle"></i>
                </button>
              )}
            </div>
            <div className="d-flex justify-content-between align-items-center mt-3 flex-wrap gap-2">
              <div className="d-flex gap-2 flex-wrap">
                <button className="btn btn-outline-light btn-sm rounded-pill"><i className="bi bi-upload"></i> Upload</button>
                <button className="btn btn-outline-light btn-sm rounded-pill"><i className="bi bi-mic"></i> Voice</button>
                <button className="btn btn-outline-light btn-sm rounded-pill"><i className="bi bi-braces"></i> Code</button>
              </div>
              <div className="d-flex gap-2">
                <button className="btn btn-outline-light rounded-pill" onClick={handleNewChat}>New chat</button>
                <button
                  className="btn btn-primary rounded-pill"
                  type="button"
                  onClick={handleSendMessage}
                  disabled={!inputText.trim() || isLoading}
                >
                  {isLoading ? 'Streaming…' : 'Send'}
                </button>
              </div>
            </div>
          </div>
        </section>

        <aside className="context-panel p-3 d-flex flex-column gap-3">
          <div>
            <p className="section-title mb-1">Context</p>
            <h6 className="mb-2">Personas</h6>
            <div className="d-grid gap-2">
              {personaOptions.map((persona) => (
                <label key={persona.id} className="d-flex align-items-center justify-content-between glass-border p-2">
                  <div className="d-flex align-items-center gap-2">
                    <i className={`bi bi-${persona.icon}`}></i>
                    {persona.label}
                  </div>
                  <div className="form-check form-switch m-0">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      checked={settings.personas[persona.id]}
                      onChange={(e) => setSettings({
                        ...settings,
                        personas: {
                          ...settings.personas,
                          [persona.id]: e.target.checked
                        }
                      })}
                    />
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="glass-border p-3">
            <p className="section-title mb-1">Telemetry</p>
            <div className="d-grid gap-2">
              <div className="d-flex justify-content-between align-items-center">
                <span>Confidence target</span>
                <strong>{settings.confidenceThreshold}</strong>
              </div>
              <input
                type="range"
                className="form-range"
                min="0.6"
                max="0.95"
                step="0.05"
                value={settings.confidenceThreshold}
                onChange={(e) => setSettings({ ...settings, confidenceThreshold: parseFloat(e.target.value) })}
              />
              <div className="form-check form-switch">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="enable-location-context"
                  checked={settings.enableLocationContext}
                  onChange={(e) => setSettings({ ...settings, enableLocationContext: e.target.checked })}
                />
                <label className="form-check-label" htmlFor="enable-location-context">Location context</label>
              </div>
              <div className="form-check form-switch">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="enable-research-agents"
                  checked={settings.enableResearchAgents}
                  onChange={(e) => setSettings({ ...settings, enableResearchAgents: e.target.checked })}
                />
                <label className="form-check-label" htmlFor="enable-research-agents">Research agents</label>
              </div>
            </div>
          </div>

          <div className="glass-border p-3">
            <p className="section-title mb-1">Recent prompts</p>
            <ul className="list-unstyled mb-0">
              {quickPrompts.slice(0, 3).map((prompt) => (
                <li key={prompt} className="mb-2 small">
                  <i className="bi bi-lightning-charge me-2 text-primary"></i>{prompt}
                </li>
              ))}
            </ul>
          </div>

          <div className="glass-border p-3">
            <p className="section-title mb-1">Actions</p>
            <div className="d-grid gap-2">
              <button className="btn btn-outline-light btn-sm rounded-pill"><i className="bi bi-shield-check me-2"></i>Compliance scan</button>
              <button className="btn btn-outline-light btn-sm rounded-pill"><i className="bi bi-diagram-2 me-2"></i>Open knowledge graph</button>
              <button className="btn btn-outline-light btn-sm rounded-pill"><i className="bi bi-file-earmark-text me-2"></i>Generate report</button>
            </div>
          </div>
        </aside>
      </div>
    </Layout>
  );
}