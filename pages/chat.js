import { useState, useEffect, useRef } from 'react';
import Head from 'next/head';
import Layout from '../components/Layout';
import { marked } from 'marked';
import {
  makeStyles,
  shorthands,
  Button as FluentButton,
  Dialog,
  DialogTrigger,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogContent,
  DialogActions,
  Slider,
  Switch,
  Checkbox,
  Field,
  Spinner,
  tokens,
} from '@fluentui/react-components';
import { bundleIcon, ChatSparkle24Filled, ChatSparkle24Regular, Settings24Filled, Settings24Regular, History24Filled, History24Regular, Delete24Regular, Send24Regular } from '@fluentui/react-icons';
import Sidebar, { SidebarItem } from '../components/ui/Sidebar';
import ChatMessage from '../components/ui/ChatMessage';
import Button from '../components/ui/Button';
import Textarea from '../components/ui/Textarea';
import Text from '../components/ui/Text';

const useStyles = makeStyles({
  layout: {
    display: 'grid',
    gridTemplateColumns: '320px 1fr',
    gap: '24px',
    minHeight: 'calc(100vh - 200px)',
    position: 'relative',
    '@media(max-width: 992px)': {
      gridTemplateColumns: '1fr',
    },
  },
  sidebarToggle: {
    position: 'fixed',
    bottom: '32px',
    right: '32px',
    display: 'none',
    zIndex: 1300,
    '@media(max-width: 992px)': {
      display: 'block',
    },
  },
  chatSurface: {
    backgroundColor: 'var(--colorNeutralBackground2)',
    borderRadius: '24px',
    boxShadow: '0 25px 60px rgba(8, 14, 30, 0.5)',
    border: '1px solid rgba(255,255,255,0.04)',
    display: 'flex',
    flexDirection: 'column',
    minHeight: '600px',
    overflow: 'hidden',
  },
  chatHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    ...shorthands.padding('20px', '24px'),
    borderBottom: '1px solid rgba(255,255,255,0.04)',
  },
  chatTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  messagePane: {
    flex: 1,
    overflowY: 'auto',
    ...shorthands.padding('24px', '24px', '0', '24px'),
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  emptyState: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center',
    gap: '16px',
    color: 'var(--colorNeutralForeground2)',
  },
  suggestions: {
    display: 'flex',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: '12px',
  },
  inputArea: {
    borderTop: '1px solid rgba(255,255,255,0.04)',
    backgroundColor: 'var(--colorNeutralBackground3)',
    ...shorthands.padding('20px', '24px'),
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  inputRow: {
    display: 'flex',
    gap: '12px',
    alignItems: 'flex-end',
    '@media(max-width: 640px)': {
      flexDirection: 'column',
      alignItems: 'stretch',
    },
  },
  textField: {
    flex: 1,
  },
  historyHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '8px',
  },
  personaList: {
    display: 'grid',
    gap: '8px',
  },
});

const ChatIcon = bundleIcon(ChatSparkle24Filled, ChatSparkle24Regular);
const SettingsIcon = bundleIcon(Settings24Filled, Settings24Regular);
const HistoryIcon = bundleIcon(History24Filled, History24Regular);

export default function Chat() {
  const styles = useStyles();
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [chatTitle, setChatTitle] = useState('New conversation');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [settings, setSettings] = useState({
    confidenceThreshold: 0.85,
    enableLocationContext: true,
    enableResearchAgents: true,
    personas: {
      ke: true,
      se: true,
      re: true,
      ce: true,
    },
  });

  const messagesEndRef = useRef(null);
  const chatInputRef = useRef(null);

  useEffect(() => {
    const savedHistory = typeof window !== 'undefined' ? window.localStorage.getItem('ukg_chat_history') : null;
    if (savedHistory) {
      setChatHistory(JSON.parse(savedHistory));
    }
    setMessages([
      {
        id: 'welcome',
        type: 'system',
        content: marked.parse('# Welcome to the UKG Chat System\n\nHow can the enterprise assistants help today?'),
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (chatInputRef.current) {
      chatInputRef.current.style.height = 'auto';
      chatInputRef.current.style.height = `${chatInputRef.current.scrollHeight}px`;
    }
  }, [inputText]);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: marked.parse(inputText),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
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
            .filter(([, isActive]) => isActive)
            .map(([key]) => key.toUpperCase()),
        }),
      });

      const data = await response.json();

      if (!currentChatId && data.chat_id) {
        setCurrentChatId(data.chat_id);
        const newChatItem = {
          id: data.chat_id,
          title: generateChatTitle(inputText),
          created: new Date().toISOString(),
          lastUpdated: new Date().toISOString(),
        };
        setChatHistory((prev) => {
          const updated = [newChatItem, ...prev];
          window.localStorage.setItem('ukg_chat_history', JSON.stringify(updated));
          return updated;
        });
        setChatTitle(newChatItem.title);
      }

      const systemResponse = {
        id: `response-${Date.now()}`,
        type: data.error ? 'error' : 'system',
        content: marked.parse(data.error ? `**Error:** ${data.error}` : data.response || 'No response received.'),
        confidence: data.confidence,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, systemResponse]);
    } catch (error) {
      const errorMessage = {
        id: `error-${Date.now()}`,
        type: 'error',
        content: marked.parse('Sorry, there was an error processing your request. Please try again.'),
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateChatTitle = (message) => {
    if (!message) return 'New conversation';
    return message.length > 42 ? `${message.substring(0, 42)}…` : message;
  };

  const handleChatSelect = (chatId) => {
    const selected = chatHistory.find((chat) => chat.id === chatId);
    if (selected) {
      setCurrentChatId(chatId);
      setChatTitle(selected.title);
      setMessages([
        {
          id: 'resume',
          type: 'system',
          content: marked.parse(`# ${selected.title}\n\nLoading previous insights…`),
          timestamp: new Date().toISOString(),
        },
      ]);
      setIsSidebarOpen(false);
    }
  };

  const handleClearChats = () => {
    if (typeof window !== 'undefined' && window.confirm('Clear all stored conversations?')) {
      setChatHistory([]);
      window.localStorage.removeItem('ukg_chat_history');
      setCurrentChatId(null);
      setChatTitle('New conversation');
      setMessages([
        {
          id: 'welcome',
          type: 'system',
          content: marked.parse('# Welcome to the UKG Chat System\n\nHow can the enterprise assistants help today?'),
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  };

  const renderMessages = () => {
    if (messages.length === 0) {
      return (
        <div className={styles.emptyState}>
          <ChatIcon fontSize={28} />
          <Text fontSize="lg" fontWeight="semibold">
            Start a conversation
          </Text>
          <Text fontSize="sm" color="muted">
            Ask about compliance status, regional operations, or contextual personas to activate Microsoft-aligned insights.
          </Text>
          <div className={styles.suggestions}>
            {['How does the UKG system work?', 'Tell me about the 13 axes of knowledge', 'What are knowledge algorithms?'].map((prompt) => (
              <Button key={prompt} variant="subtle" onClick={() => setInputText(prompt)}>
                {prompt}
              </Button>
            ))}
          </div>
        </div>
      );
    }

    return messages.map((message) => (
      <ChatMessage
        key={message.id}
        type={message.type}
        content={message.content}
        timestamp={message.timestamp}
        metadata={message.confidence ? `Confidence: ${message.confidence}` : undefined}
      />
    ));
  };

  const personaToggles = [
    { id: 'ke', label: 'Knowledge Expert' },
    { id: 'se', label: 'Skill Expert' },
    { id: 're', label: 'Role Expert' },
    { id: 'ce', label: 'Context Expert' },
  ];

  return (
    <Layout>
      <Head>
        <title>UKG Chat Interface</title>
      </Head>

      <div className={styles.layout}>
        <Sidebar
          headerTitle="Conversations"
          headerActions={
            <Button variant="subtle" size="sm" icon={<HistoryIcon />} onClick={() => setIsSidebarOpen(false)}>
              Close
            </Button>
          }
          isOpen={isSidebarOpen}
        >
          <div className={styles.historyHeader}>
            <Text fontWeight="semibold">Chat history</Text>
            <Button variant="subtle" size="sm" icon={<Delete24Regular />} onClick={handleClearChats}>
              Clear
            </Button>
          </div>

          <div>
            {chatHistory.length === 0 && (
              <Text fontSize="sm" color="muted">
                New conversations will be saved here for quick retrieval.
              </Text>
            )}
            {chatHistory.map((chat) => (
              <SidebarItem
                key={chat.id}
                label={chat.title}
                icon={<HistoryIcon />}
                isActive={currentChatId === chat.id}
                onClick={() => handleChatSelect(chat.id)}
              />
            ))}
          </div>
        </Sidebar>

        <div className={styles.chatSurface}>
          <div className={styles.chatHeader}>
            <div className={styles.chatTitle}>
              <ChatIcon fontSize={22} />
              <div>
                <Text fontSize="lg" fontWeight="semibold">
                  UKG Copilot
                </Text>
                <Text fontSize="sm" color="muted">
                  {chatTitle}
                </Text>
              </div>
            </div>

            <Dialog open={settingsOpen} onOpenChange={(event, data) => setSettingsOpen(data.open)}>
              <DialogTrigger disableButtonEnhancement>
                <FluentButton appearance="transparent" icon={<SettingsIcon />}>
                  Conversation settings
                </FluentButton>
              </DialogTrigger>
              <DialogSurface>
                <DialogBody>
                  <DialogTitle>Conversation tuning</DialogTitle>
                  <DialogContent>
                    <Field label="Target confidence">
                      <Slider
                        min={0.6}
                        max={0.95}
                        step={0.05}
                        value={settings.confidenceThreshold}
                        onChange={(event, data) =>
                          setSettings((prev) => ({ ...prev, confidenceThreshold: data.value }))
                        }
                      />
                      <Text fontSize="sm" color="muted">
                        {Math.round(settings.confidenceThreshold * 100)}% precision target
                      </Text>
                    </Field>

                    <Switch
                      checked={settings.enableLocationContext}
                      label="Enable location context"
                      onChange={(event, data) =>
                        setSettings((prev) => ({ ...prev, enableLocationContext: data.checked }))
                      }
                    />
                    <Switch
                      checked={settings.enableResearchAgents}
                      label="Enable research agents"
                      onChange={(event, data) =>
                        setSettings((prev) => ({ ...prev, enableResearchAgents: data.checked }))
                      }
                    />

                    <Field label="Active personas">
                      <div className={styles.personaList}>
                        {personaToggles.map((persona) => (
                          <Checkbox
                            key={persona.id}
                            label={persona.label}
                            checked={settings.personas[persona.id]}
                            onChange={(event, data) =>
                              setSettings((prev) => ({
                                ...prev,
                                personas: {
                                  ...prev.personas,
                                  [persona.id]: data.checked,
                                },
                              }))
                            }
                          />
                        ))}
                      </div>
                    </Field>
                  </DialogContent>
                  <DialogActions>
                    <FluentButton appearance="secondary" onClick={() => setSettingsOpen(false)}>
                      Done
                    </FluentButton>
                  </DialogActions>
                </DialogBody>
              </DialogSurface>
            </Dialog>
          </div>

          <div className={styles.messagePane}>
            {renderMessages()}
            {isLoading && (
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <Spinner size="medium" />
                <Text color="muted">Synthesizing response…</Text>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className={styles.inputArea}>
            <div className={styles.inputRow}>
              <Textarea
                ref={chatInputRef}
                value={inputText}
                onChange={(event, data) => setInputText(data.value)}
                placeholder="Ask a question about compliance, locations, or knowledge pillars…"
                size="large"
                className={styles.textField}
                rows={1}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
              <Button
                variant="primary"
                icon={<Send24Regular />}
                onClick={handleSendMessage}
                disabled={!inputText.trim() || isLoading}
              >
                Send
              </Button>
            </div>
          </div>
        </div>
      </div>

      <Button
        className={styles.sidebarToggle}
        variant="primary"
        icon={<HistoryIcon />}
        onClick={() => setIsSidebarOpen((open) => !open)}
      >
        Conversation history
      </Button>
    </Layout>
  );
}
