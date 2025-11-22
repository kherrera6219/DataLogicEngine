import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/router'
import LoginPage from '../../pages/login'

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: jest.fn(),
}))

// Mock fetch
global.fetch = jest.fn()

describe('LoginPage', () => {
  const mockPush = jest.fn()

  beforeEach(() => {
    useRouter.mockReturnValue({
      push: mockPush,
      pathname: '/login',
      query: {},
      asPath: '/login',
    })
    fetch.mockClear()
    mockPush.mockClear()
  })

  it('renders login form', () => {
    render(<LoginPage />)

    expect(screen.getByText('Universal Knowledge Graph')).toBeInTheDocument()
    expect(screen.getByText('Role Selection & Login')).toBeInTheDocument()
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
  })

  it('renders all role options', () => {
    render(<LoginPage />)

    expect(screen.getByText('Acquisition Expert')).toBeInTheDocument()
    expect(screen.getByText('Industry Expert')).toBeInTheDocument()
    expect(screen.getByText('Regulatory Expert')).toBeInTheDocument()
    expect(screen.getByText('Compliance Expert')).toBeInTheDocument()
  })

  it('disables submit button when fields are empty', () => {
    render(<LoginPage />)

    const submitButton = screen.getByRole('button', { name: /login/i })
    expect(submitButton).toBeDisabled()
  })

  it('enables submit button when all required fields are filled', () => {
    render(<LoginPage />)

    // Select a role
    fireEvent.click(screen.getByText('Acquisition Expert'))

    // Fill in username and password
    fireEvent.change(screen.getByLabelText('Username'), {
      target: { value: 'testuser' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'testpass123' },
    })

    const submitButton = screen.getByRole('button', { name: /login/i })
    expect(submitButton).not.toBeDisabled()
  })

  it('displays error message on failed login', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ success: false, error: 'Invalid credentials' }),
    })

    render(<LoginPage />)

    // Select role and fill in credentials
    fireEvent.click(screen.getByText('Acquisition Expert'))
    fireEvent.change(screen.getByLabelText('Username'), {
      target: { value: 'testuser' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'wrongpass' },
    })

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
  })

  it('redirects to knowledge-graph on successful login', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        user: { username: 'testuser', id: 1 },
      }),
    })

    render(<LoginPage />)

    // Select role and fill in credentials
    fireEvent.click(screen.getByText('Industry Expert'))
    fireEvent.change(screen.getByLabelText('Username'), {
      target: { value: 'testuser' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'testpass123' },
    })

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/knowledge-graph')
    })
  })

  it('stores user data in localStorage on successful login', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        user: { username: 'testuser', id: 1 },
      }),
    })

    render(<LoginPage />)

    // Select role and fill in credentials
    fireEvent.click(screen.getByText('Compliance Expert'))
    fireEvent.change(screen.getByLabelText('Username'), {
      target: { value: 'testuser' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'testpass123' },
    })

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /login/i }))

    await waitFor(() => {
      expect(localStorage.setItem).toHaveBeenCalledWith('userRole', 'compliance')
      expect(localStorage.setItem).toHaveBeenCalledWith('username', 'testuser')
    })
  })
})
