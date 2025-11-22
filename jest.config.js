const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    // Handle module aliases (this will be automatically configured for you soon)
    '^@/components/(.*)$': '<rootDir>/components/$1',
    '^@/pages/(.*)$': '<rootDir>/pages/$1',
    '^@/utils/(.*)$': '<rootDir>/utils/$1',
    // Mock d3 to avoid ESM issues in Jest
    '^d3$': '<rootDir>/__mocks__/d3.js',
    '^d3-(.*)$': '<rootDir>/__mocks__/d3.js',
    // Mock react-force-graph
    '^react-force-graph-2d$': '<rootDir>/__mocks__/react-force-graph-2d.js',
    // Mock Fluent UI
    '^@fluentui/react-components$': '<rootDir>/__mocks__/@fluentui/react-components.js',
  },
  transformIgnorePatterns: [
    'node_modules/(?!(d3|d3-array|d3-scale|d3-shape|react-force-graph)/)',
  ],
  collectCoverageFrom: [
    'pages/**/*.{js,jsx,ts,tsx}',
    'components/**/*.{js,jsx,ts,tsx}',
    'utils/**/*.{js,jsx,ts,tsx}',
    '!pages/_app.js',
    '!pages/_document.js',
    '!pages/api/**',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
  testMatch: [
    '**/__tests__/**/*.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)',
  ],
  coverageThreshold: {
    global: {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50,
    },
  },
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
