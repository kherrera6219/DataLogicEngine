const nextJest = require('next/jest');

const createJestConfig = nextJest({
  dir: './',
});

const customJestConfig = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/frontend/jest.setup.js'],
  testMatch: ['**/__tests__/**/*.js'],
};

module.exports = createJestConfig(customJestConfig);
