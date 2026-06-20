import '@testing-library/jest-dom'
import { vi } from 'vitest'
import { server } from './msw/server'

// Mock virtual:pwa-register — only exists at build time via vite-plugin-pwa
vi.mock('virtual:pwa-register', () => ({
  registerSW: () => () => {},
}))

// Mock matchMedia for react-hot-toast and responsive design tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
