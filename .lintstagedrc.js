module.exports = {
  // JavaScript/TypeScript files
  '*.{js,jsx,ts,tsx}': [
    'prettier --write',
    'eslint --fix',
    'git add'
  ],
  // Python files
  '*.py': [
    'python -m black',
    'python -m isort',
    'git add'
  ],
  // JSON, YAML, Markdown files
  '*.{json,yml,yaml,md}': [
    'prettier --write',
    'git add'
  ],
  // CSS files
  '*.{css,scss,sass}': [
    'prettier --write',
    'git add'
  ]
}
