# Chat Interface Wireframe - 2025 Design

## Overview
Modern AI-first chat interface with advanced features: streaming responses, voice input, file upload, code syntax highlighting, regeneration, and contextual actions.

---

## Desktop View (1920x1080)

```
╔════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ [Logo] DataLogicEngine    💬 UKG Chat Assistant                [⚙️ Settings] [👤 User]  [🔔 Notif]   ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║ SIDEBAR (280px)    │                    MAIN CHAT AREA (1360px)                 │  CONTEXT (280px)    ║
║ ════════════       │                    ═════════════════                        │  ═══════════        ║
║                    │                                                             │                     ║
║ ┌─────────────┐    │  ┌─────────────────────────────────────────────────────┐  │  ┌───────────────┐  ║
║ │[+ New Chat ]│    │  │  Chat: "Procurement Compliance Query"        [⋮]    │  │  │ 📍 Context    │  ║
║ └─────────────┘    │  └─────────────────────────────────────────────────────┘  │  │               │  ║
║                    │                                                             │  │ Location:     │  ║
║ 🔍 [Search...]     │  ╔═══════════════════════════════════════════════════════╗│  │ Washington DC │  ║
║                    │  ║                                                       ║│  │               │  ║
║ Recent Chats       │  ║  ┌──────────────────────────────────────────────┐   ║│  │ Active Axes:  │  ║
║ ────────────       │  ║  │ 👤 User                         2:34 PM      │   ║│  │ [1] [3] [6]   │  ║
║                    │  ║  │                                              │   ║│  │ [7] [12]      │  ║
║ ● Today            │  ║  │ What are the DFARS compliance requirements  │   ║│  │               │  ║
║  📝 Procurement... │  ║  │ for cloud service providers?                │   ║│  │ Personas:     │  ║
║  📝 Regulatory...  │  ║  │                                              │   ║│  │ ☑ Knowledge   │  ║
║  📝 SOC2 Audit...  │  ║  └──────────────────────────────────────────────┘   ║│  │ ☑ Skill       │  ║
║                    │  ║                                                       ║│  │ ☑ Role        │  ║
║ ● Yesterday        │  ║  ┌──────────────────────────────────────────────┐   ║│  │ ☑ Context     │  ║
║  📝 Honeycomb...   │  ║  │ 🤖 Assistant              ⚡ Confidence: 0.92│   ║│  │               │  ║
║  📝 Timeline...    │  ║  │                                              │   ║│  │ Settings:     │  ║
║                    │  ║  │ DFARS (Defense Federal Acquisition         │   ║│  │               │  ║
║ ● Last 7 days     │  ║  │ Regulation Supplement) compliance for       │   ║│  │ Confidence:   │  ║
║  📝 Knowledge...   │  ║  │ cloud service providers includes:           │   ║│  │ ▬▬▬▬●▬▬ 0.85  │  ║
║                    │  ║  │                                              │   ║│  │               │  ║
║ [Show More]        │  ║  │ **Key Requirements:**                       │   ║│  │ [Advanced]    │  ║
║                    │  ║  │                                              │   ║│  └───────────────┘  ║
║ ─────────          │  ║  │ 1. **DFARS 252.204-7012** - Safeguarding   │   ║│                     ║
║                    │  ║  │    • FedRAMP Moderate baseline             │   ║│  ┌───────────────┐  ║
║ Collections        │  ║  │    • NIST SP 800-171 compliance            │   ║│  │ 🔗 Sources    │  ║
║ ───────────        │  ║  │    • Incident reporting within 72 hours    │   ║│  │               │  ║
║                    │  ║  │                                              │   ║│  │ • FAR 52.2... │  ║
║ 📁 Compliance      │  ║  │ 2. **DFARS 252.239-7010** - Cloud Computing│   ║│  │ • DFARS 25... │  ║
║ 📁 Regulatory      │  ║  │    • Data location requirements            │   ║│  │ • NIST SP...  │  ║
║ 📁 Acquisition     │  ║  │    • Government access rights              │   ║│  │               │  ║
║ 📁 Industry        │  ║  │    • Security controls documentation       │   ║│  │ [View All]    │  ║
║                    │  ║  │                                              │   ║│  └───────────────┘  ║
║ ─────────          │  ║  │ ```yaml                                     │   ║│                     ║
║                    │  ║  │ # Example Configuration                     │   ║│  ┌───────────────┐  ║
║ [🗑️ Clear All]    │  ║  │ compliance:                                 │   ║│  │ 💡 Suggestions│  ║
║                    │  ║  │   dfars: "252.204-7012"                    │   ║│  │               │  ║
║ Settings           │  ║  │   fedramp: "Moderate"                      │   ║│  │ • "Show me... │  ║
║ ────────           │  ║  │   nist: "800-171"                          │   ║│  │ • "Explain... │  ║
║                    │  ║  │ ```                                         │   ║│  │ • "Compare... │  ║
║ Theme: [🌙 Dark]   │  ║  │                                              │   ║│  │               │  ║
║ Language: [EN ▼]   │  ║  │ **Related Requirements:**                   │   ║│  └───────────────┘  ║
║                    │  ║  │ • FedRAMP authorization required            │   ║│                     ║
║ Shortcuts          │  ║  │ • DoD Cloud Computing SRG compliance        │   ║│                     ║
║ ─────────          │  ║  │ • Continuous monitoring & annual assessment │   ║│                     ║
║ ⌘K Command Menu    │  ║  │                                              │   ║│                     ║
║ / Focus Search     │  ║  │ Would you like me to provide specific       │   ║│                     ║
║ ⌘N New Chat        │  ║  │ implementation guidance for any of these?   │   ║│                     ║
║                    │  ║  │                                              │   ║│                     ║
║                    │  ║  │ ┌────────────────────────────────────────┐  │   ║│                     ║
║                    │  ║  │ │ 💬 Related Questions                   │  │   ║│                     ║
║                    │  ║  │ │ • What is FedRAMP Moderate?            │  │   ║│                     ║
║                    │  ║  │ │ • NIST 800-171 implementation steps?  │  │   ║│                     ║
║                    │  ║  │ │ • Cloud provider comparison?           │  │   ║│                     ║
║                    │  ║  │ └────────────────────────────────────────┘  │   ║│                     ║
║                    │  ║  │                                              │   ║│                     ║
║                    │  ║  │ [👍] [👎] [🔄 Regenerate] [📋 Copy] [🔗]   │   ║│                     ║
║                    │  ║  └──────────────────────────────────────────────┘   ║│                     ║
║                    │  ║                                                       ║│                     ║
║                    │  ║  ┌──────────────────────────────────────────────┐   ║│                     ║
║                    │  ║  │ 👤 User                         2:36 PM      │   ║│                     ║
║                    │  ║  │                                              │   ║│                     ║
║                    │  ║  │ Explain FedRAMP Moderate                    │   ║│                     ║
║                    │  ║  └──────────────────────────────────────────────┘   ║│                     ║
║                    │  ║                                                       ║│                     ║
║                    │  ║  ┌──────────────────────────────────────────────┐   ║│                     ║
║                    │  ║  │ 🤖 Assistant           ⚡ Streaming... ●●●  │   ║│                     ║
║                    │  ║  │                                              │   ║│                     ║
║                    │  ║  │ FedRAMP (Federal Risk and Authorization     │   ║│                     ║
║                    │  ║  │ Management Program) Moderate is a...▊       │   ║│                     ║
║                    │  ║  │                                              │   ║│                     ║
║                    │  ║  └──────────────────────────────────────────────┘   ║│                     ║
║                    │  ║                                                       ║│                     ║
║                    │  ║  ↓ Scroll for more                                   ║│                     ║
║                    │  ╚═══════════════════════════════════════════════════════╝│                     ║
║                    │                                                             │                     ║
║                    │  ┌───────────────────────────────────────────────────────┐│                     ║
║                    │  │ ┌─────────────────────────────────────────────────┐  ││                     ║
║                    │  │ │ 💬 Ask a question, describe a task...    [📎] │  ││  ← Auto-resize      ║
║                    │  │ │                                          [🎤] │  ││     textarea        ║
║                    │  │ └─────────────────────────────────────────────────┘  ││                     ║
║                    │  │                                                       ││                     ║
║                    │  │ Suggestion chips:                                     ││                     ║
║                    │  │ [💡 Examples] [🎯 Templates] [⌨️ Shortcuts]          ││                     ║
║                    │  │                                                       ││                     ║
║                    │  │                                  [↑ Send] or Enter    ││                     ║
║                    │  └───────────────────────────────────────────────────────┘│                     ║
╠════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  Model: GPT-4 Turbo | Tokens: 2,340 / 8,000 | Response time: 2.3s                                     ║
╚════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## Tablet View (768x1024)

```
┌────────────────────────────────────────────────────┐
│ ☰  DataLogicEngine - Chat    [⚙️] [👤] [🔔]       │
├────────────────────────────────────────────────────┤
│                                                    │
│ [🔍 Search chats...]                [+ New Chat]  │
│                                                    │
│ ╔════════════════════════════════════════════════╗ │
│ ║                                                ║ │
│ ║  ┌──────────────────────────────────────────┐ ║ │
│ ║  │ 👤 User                      2:34 PM     │ ║ │
│ ║  │                                          │ ║ │
│ ║  │ What are the DFARS compliance           │ ║ │
│ ║  │ requirements for cloud providers?       │ ║ │
│ ║  └──────────────────────────────────────────┘ ║ │
│ ║                                                ║ │
│ ║  ┌──────────────────────────────────────────┐ ║ │
│ ║  │ 🤖 Assistant      ⚡ Confidence: 0.92   │ ║ │
│ ║  │                                          │ ║ │
│ ║  │ DFARS compliance includes...            │ ║ │
│ ║  │                                          │ ║ │
│ ║  │ **Key Requirements:**                   │ ║ │
│ ║  │ 1. DFARS 252.204-7012                  │ ║ │
│ ║  │ 2. DFARS 252.239-7010                  │ ║ │
│ ║  │                                          │ ║ │
│ ║  │ [View Full Response ▼]                  │ ║ │
│ ║  │                                          │ ║ │
│ ║  │ [👍] [👎] [🔄] [📋] [🔗] [More ⋯]      │ ║ │
│ ║  └──────────────────────────────────────────┘ ║ │
│ ║                                                ║ │
│ ║  ↓ Scroll for more messages                   ║ │
│ ╚════════════════════════════════════════════════╝ │
│                                                    │
│ ┌────────────────────────────────────────────────┐ │
│ │ 💬 Type your message...         [📎] [🎤]     │ │
│ │                                                │ │
│ └────────────────────────────────────────────────┘ │
│                                       [↑ Send]     │
│                                                    │
│ [💡 Suggestions] [📍 Context] [🔗 Sources]        │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## Mobile View (375x812)

```
┌─────────────────────────────┐
│ ☰  Chat        [⋮]          │
├─────────────────────────────┤
│                             │
│ ╔═════════════════════════╗ │
│ ║                         ║ │
│ ║ ┌─────────────────────┐ ║ │
│ ║ │ 👤 You    2:34 PM   │ ║ │
│ ║ │                     │ ║ │
│ ║ │ What are DFARS     │ ║ │
│ ║ │ requirements?      │ ║ │
│ ║ └─────────────────────┘ ║ │
│ ║                         ║ │
│ ║ ┌─────────────────────┐ ║ │
│ ║ │ 🤖 AI    ⚡ 0.92   │ ║ │
│ ║ │                     │ ║ │
│ ║ │ DFARS compliance    │ ║ │
│ ║ │ includes:           │ ║ │
│ ║ │                     │ ║ │
│ ║ │ 1. 252.204-7012    │ ║ │
│ ║ │ 2. 252.239-7010    │ ║ │
│ ║ │                     │ ║ │
│ ║ │ [Full ▼]           │ ║ │
│ ║ │                     │ ║ │
│ ║ │ [👍][👎][🔄][⋯]   │ ║ │
│ ║ └─────────────────────┘ ║ │
│ ║                         ║ │
│ ║ ↓ Scroll               ║ │
│ ╚═════════════════════════╝ │
│                             │
│ ┌───────────────────────┐   │
│ │ 💬 Message...   [🎤] │   │
│ └───────────────────────┘   │
│                  [↑ Send]   │
│                             │
│ [💡][📍][🔗]  ← Quick tabs │
└─────────────────────────────┘
```

---

## Key Features & Components

### 1. **Three-Column Layout (Desktop)**

#### Left Sidebar (280px)
- **New Chat Button**: Prominent, always visible
- **Search**: Fuzzy search across all chats
- **Recent Chats**: Grouped by time (Today, Yesterday, Last 7 days)
- **Collections**: Folder organization
- **Settings**: Quick access to preferences
- **Keyboard Shortcuts**: Visual guide

#### Main Chat Area (1360px)
- **Chat Header**: Title, menu, context info
- **Messages Area**: Scrollable conversation
- **Input Section**: Multi-line textarea with actions
- **Suggestion Chips**: Contextual quick actions

#### Right Context Panel (280px)
- **Location Context**: Current geographic setting
- **Active Axes**: Which knowledge dimensions are active
- **Active Personas**: Expert types engaged
- **Confidence Slider**: Target threshold
- **Sources**: Referenced documents
- **Suggestions**: Related questions

### 2. **Message Components**

#### User Message
```
┌──────────────────────────────────────────────┐
│ 👤 User                         2:34 PM      │
│                                              │
│ Message content here...                      │
│ Can span multiple lines                      │
│                                              │
└──────────────────────────────────────────────┘
```

#### AI Response Message
```
┌──────────────────────────────────────────────┐
│ 🤖 Assistant              ⚡ Confidence: 0.92│
│                                              │
│ **Formatted Markdown Content**               │
│                                              │
│ • Bullet points                              │
│ • Code blocks with syntax highlighting       │
│ • Tables, links, etc.                        │
│                                              │
│ ┌────────────────────────────────────────┐  │
│ │ 💬 Related Questions                   │  │
│ │ • Follow-up 1                          │  │
│ │ • Follow-up 2                          │  │
│ └────────────────────────────────────────┘  │
│                                              │
│ [👍] [👎] [🔄 Regenerate] [📋 Copy] [🔗]   │
└──────────────────────────────────────────────┘
```

#### System/Info Message
```
┌──────────────────────────────────────────────┐
│ ℹ️ System                                    │
│                                              │
│ Chat saved. You can access this conversation │
│ from your history.                           │
└──────────────────────────────────────────────┘
```

#### Loading/Streaming State
```
┌──────────────────────────────────────────────┐
│ 🤖 Assistant           ⚡ Streaming... ●●●  │
│                                              │
│ Response is being generated in real-time.   │
│ Content appears as it's created...▊         │
│                                              │
│ [⏸ Pause] [⏹ Stop]                          │
└──────────────────────────────────────────────┘
```

### 3. **Input Section**

```
┌───────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────────┐  │
│ │ 💬 Ask a question, describe a task...    [📎] │  │ ← Auto-resize
│ │                                          [🎤] │  │   textarea
│ └─────────────────────────────────────────────────┘  │
│                                                       │
│ Suggestion chips (contextual):                       │
│ [💡 Examples] [🎯 Templates] [⌨️ Shortcuts]          │
│                                                       │
│ Attachments: [📄 policy.pdf] [❌]                    │
│                                                       │
│                                  [↑ Send] or Enter    │
└───────────────────────────────────────────────────────┘
```

**Features**:
- Auto-resize as you type
- File attachment support (drag & drop)
- Voice input button
- Enter to send, Shift+Enter for new line
- Character/token counter
- Clear button when text present

### 4. **Command Palette (Cmd/Ctrl + K)**

```
╔═══════════════════════════════════════════════════╗
║ Command Palette                          [ESC]    ║
╠═══════════════════════════════════════════════════╣
║ 🔍 [Type to search...]_______________            ║
╟───────────────────────────────────────────────────╢
║                                                   ║
║ 📝 Actions                                        ║
║   → New Chat                            ⌘N       ║
║   → Clear Current Chat                  ⌘⇧C      ║
║   → Export Chat                         ⌘E       ║
║   → Share Chat                          ⌘⇧S      ║
║                                                   ║
║ 🔍 Navigation                                     ║
║   → Go to Knowledge Graph               ⌘K       ║
║   → Go to Compliance Dashboard          ⌘D       ║
║   → Go to Settings                      ⌘,       ║
║                                                   ║
║ 📍 Context                                        ║
║   → Change Location                              ║
║   → Toggle Personas                              ║
║   → Adjust Confidence                            ║
║                                                   ║
║ 🎨 Appearance                                     ║
║   → Toggle Theme                        ⌘T       ║
║   → Increase Font Size                  ⌘+       ║
║   → Decrease Font Size                  ⌘-       ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
```

### 5. **Code Block with Syntax Highlighting**

```
┌─────────────────────────────────────────────────┐
│ 📄 example.yaml                   [📋 Copy]     │
├─────────────────────────────────────────────────┤
│  1  # DFARS Compliance Configuration            │
│  2  compliance:                                 │
│  3    dfars: "252.204-7012"                    │
│  4    fedramp:                                  │
│  5      level: "Moderate"                       │
│  6      authorization: true                     │
│  7    nist:                                     │
│  8      standard: "800-171"                     │
│  9      controls: 110                           │
│ 10    monitoring:                               │
│ 11      continuous: true                        │
│ 12      frequency: "annual"                     │
└─────────────────────────────────────────────────┘
```

**Features**:
- Language detection
- Line numbers
- Copy to clipboard button
- Syntax highlighting
- Wrap/scroll toggle

### 6. **Contextual Actions on Hover**

When hovering over an AI response:
```
┌──────────────────────────────────────────────┐
│ [👍] [👎] [🔄] [📋] [🔗] [💾] [🔊] [⋯]      │
└──────────────────────────────────────────────┘
```

- **👍/👎**: Feedback
- **🔄**: Regenerate response
- **📋**: Copy to clipboard
- **🔗**: Share/get link
- **💾**: Save to collection
- **🔊**: Text-to-speech
- **⋯**: More options (report, edit, etc.)

### 7. **Voice Input Modal**

```
╔═══════════════════════════════════════╗
║     🎤 Listening...                   ║
╠═══════════════════════════════════════╣
║                                       ║
║         ◉ ◉ ◉ ◉ ◉                     ║  ← Audio waveform
║        ◉ ◉ ◉ ◉ ◉ ◉                    ║     animation
║         ◉ ◉ ◉ ◉ ◉                     ║
║                                       ║
║  "What are the DFARS requirements..." ║  ← Live transcript
║                                       ║
║                                       ║
║      [⏹ Stop]    [❌ Cancel]          ║
║                                       ║
╚═══════════════════════════════════════╝
```

### 8. **File Upload/Attachment**

```
╔═══════════════════════════════════════════════════╗
║ 📎 Attach Files                          [❌]     ║
╠═══════════════════════════════════════════════════╣
║                                                   ║
║     ┌───────────────────────────────────┐        ║
║     │  Drag & drop files here           │        ║
║     │           or                      │        ║
║     │     [📁 Browse Files]             │        ║
║     └───────────────────────────────────┘        ║
║                                                   ║
║  Supported: PDF, DOCX, TXT, CSV, XLSX, PNG, JPG  ║
║  Max size: 25 MB per file                        ║
║                                                   ║
║  Attached files:                                  ║
║  ┌──────────────────────────────────────────┐    ║
║  │ 📄 procurement-policy.pdf    2.3 MB [❌] │    ║
║  │ 📊 budget-2024.xlsx          856 KB [❌] │    ║
║  └──────────────────────────────────────────┘    ║
║                                                   ║
║                    [Upload & Send]               ║
╚═══════════════════════════════════════════════════╝
```

---

## Interaction Patterns

### 1. **Message Streaming**
- Responses appear word-by-word in real-time
- Smooth scrolling to keep latest content visible
- Pause/Stop buttons during generation
- Typing indicator before streaming starts

### 2. **Auto-Scroll Behavior**
- Auto-scroll when new messages arrive
- Disable auto-scroll if user scrolls up
- "New messages ↓" button to jump to bottom
- Smooth scroll animation

### 3. **Optimistic UI**
- User message appears immediately
- Show "Sending..." state briefly
- Display error and retry option if failed
- Queue messages when offline

### 4. **Keyboard Shortcuts**
- `Enter`: Send message
- `Shift + Enter`: New line
- `Cmd/Ctrl + K`: Command palette
- `Cmd/Ctrl + N`: New chat
- `Cmd/Ctrl + /`: Focus input
- `Cmd/Ctrl + ↑/↓`: Navigate messages
- `Escape`: Close modals/cancel

### 5. **Smart Suggestions**
- Contextual quick replies based on last message
- "Related Questions" after AI responses
- Template suggestions for common tasks
- Recent/frequently used prompts

### 6. **Multi-Modal Input**
- Text (primary)
- Voice (speech-to-text)
- File upload
- Drag & drop
- Paste images from clipboard

---

## Accessibility Features

### Keyboard Navigation
- Tab through all interactive elements
- Arrow keys to navigate chat history
- Shortcuts for common actions
- Focus indicators on all controls

### Screen Reader Support
- ARIA live regions for new messages
- Descriptive labels for all buttons
- Alternative text for icons
- Semantic HTML structure

### Visual Accessibility
- High contrast mode support
- Adjustable font sizes
- Focus indicators (minimum 3:1 contrast)
- Color is not sole indicator

### Cognitive Accessibility
- Clear, consistent layout
- Progress indicators for loading
- Error messages with solutions
- Undo for destructive actions

---

## Animation & Transitions

### Message Animations
```css
/* Message fade in & slide up */
@keyframes messageEnter {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Streaming cursor blink */
@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Thinking indicator pulse */
@keyframes thinkingPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.6; }
}
```

### Micro-interactions
- Button press: Scale down slightly
- Hover: Lift with shadow
- Copy: Checkmark animation
- Send: Slide up & fade
- Like/Dislike: Scale pulse

---

## Performance Optimizations

1. **Virtual Scrolling**: Only render visible messages
2. **Lazy Load**: Load chat history on scroll
3. **Debounce**: Input typing, search
4. **Memoization**: React.memo for message components
5. **Code Splitting**: Split large dependencies
6. **Image Optimization**: Compress, lazy load
7. **WebSocket**: Real-time streaming
8. **Local Storage**: Cache recent chats

---

## States & Edge Cases

### Loading States
- Initial chat load: Skeleton screen
- Message sending: Pulse animation
- Response streaming: Typing indicator
- File upload: Progress bar

### Empty States
- No chats yet: Welcome message with examples
- No search results: Helpful message with suggestions
- No internet: Offline indicator with retry

### Error States
- Message send failed: Retry button
- API error: Error message with action
- File upload failed: Clear error description
- Rate limit: Wait time indicator

---

## Future Enhancements

1. **Multi-Agent Chat**: See different expert personas respond
2. **Branching Conversations**: Fork chats at any point
3. **Collaborative**: Share and co-edit chats
4. **Advanced Search**: Semantic search across all chats
5. **Voice Output**: Text-to-speech for responses
6. **Video/Image Generation**: Multimodal outputs
7. **Real-time Collaboration**: Multiple users in one chat
8. **Custom AI Models**: Select different models per chat

---

## Technical Implementation

### Tech Stack
- **Framework**: Next.js 15, React 19
- **Styling**: Tailwind CSS 4, Framer Motion
- **State**: Zustand (chat state), React Query (API)
- **Real-time**: WebSocket (Socket.io or native)
- **Markdown**: react-markdown with syntax highlighting
- **Code**: Prism.js or Shiki
- **Voice**: Web Speech API
- **Storage**: IndexedDB for offline support

### API Integration
```typescript
// Send message
POST /api/chat/message
{
  "chat_id": "uuid",
  "message": "string",
  "context": {...},
  "stream": true
}

// Response (streaming)
data: {"type": "token", "content": "word"}
data: {"type": "token", "content": " another"}
data: {"type": "done", "metadata": {...}}
```

---

This chat interface represents the cutting edge of AI-first conversation design for 2025, balancing power user features with accessibility and ease of use.
