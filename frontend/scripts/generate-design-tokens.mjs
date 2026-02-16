import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const tokenPath = path.join(__dirname, '..', 'design-tokens', 'tokens.json');
const outputPath = path.join(__dirname, '..', 'app', 'generated-tokens.css');

/**
 * @typedef {{ base: Record<string, string>, dark: Record<string, string>, enterprisePresets: Record<string, Record<string, string>> }} TokenSchema
 */

/** @type {TokenSchema} */
const tokens = JSON.parse(readFileSync(tokenPath, 'utf8'));

/**
 * @param {Record<string, string>} values
 */
function renderVariables(values) {
  return Object.entries(values)
    .map(([key, value]) => `  --${key}: ${value};`)
    .join('\n');
}

/**
 * @param {string} selector
 * @param {Record<string, string>} values
 */
function renderBlock(selector, values) {
  return `${selector} {\n${renderVariables(values)}\n}\n`;
}

let cssOutput = '';
cssOutput += '/* Generated file: do not edit directly. Run `npm run tokens:build`. */\n';
cssOutput += renderBlock(':root', tokens.base);
cssOutput += renderBlock('.dark', tokens.dark);

for (const [presetName, overrides] of Object.entries(tokens.enterprisePresets)) {
  if (!overrides || Object.keys(overrides).length === 0) {
    continue;
  }
  cssOutput += renderBlock(`:root[data-enterprise-theme='${presetName}']`, overrides);
}

writeFileSync(outputPath, cssOutput, 'utf8');
console.log(`Design tokens generated: ${outputPath}`);
