import { render, screen } from '@testing-library/react'
import ChatMessage from '../../components/ui/ChatMessage'

describe('ChatMessage', () => {
  it('renders system message correctly', () => {
    const content = '<p>Hello from system</p>'
    const timestamp = new Date().toISOString()

    render(
      <ChatMessage
        type="system"
        content={content}
        timestamp={timestamp}
      />
    )

    expect(screen.getByText(/hello from system/i)).toBeInTheDocument()
  })

  it('renders user message correctly', () => {
    const content = 'Hello from user'
    const timestamp = new Date().toISOString()

    render(
      <ChatMessage
        type="user"
        content={content}
        timestamp={timestamp}
      />
    )

    expect(screen.getByText(/hello from user/i)).toBeInTheDocument()
  })

  it('renders error message correctly', () => {
    const content = 'Error message'
    const timestamp = new Date().toISOString()

    render(
      <ChatMessage
        type="error"
        content={content}
        timestamp={timestamp}
      />
    )

    expect(screen.getByText(/error message/i)).toBeInTheDocument()
  })

  it('sanitizes malicious HTML content', () => {
    const maliciousContent = '<script>alert("XSS")</script><p>Safe content</p>'
    const timestamp = new Date().toISOString()

    render(
      <ChatMessage
        type="system"
        content={maliciousContent}
        timestamp={timestamp}
      />
    )

    // Script tags should be removed
    expect(screen.queryByText(/alert/i)).not.toBeInTheDocument()
    // Safe content should remain
    expect(screen.getByText(/safe content/i)).toBeInTheDocument()
  })
})
