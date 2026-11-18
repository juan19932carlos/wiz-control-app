import fs from 'node:fs';
import path from 'node:path';
import type { Config, Plugin } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const COMPOSE_FILE = path.resolve(__dirname, '../../compose.prod.yaml');

/** Gives the install guide the real compose.prod.yaml, so the file people download never drifts from the repo. */
function composeFilePlugin(): Plugin<string> {
  return {
    name: 'compose-file',
    loadContent: async () => {
      const compose = fs.readFileSync(COMPOSE_FILE, 'utf8');
      for (const placeholder of [/\$\{WIZ_TARGETS:\?[^}]*\}/, /\$\{WEB_PORT:-\d+\}/]) {
        if (!placeholder.test(compose)) {
          throw new Error(`compose.prod.yaml no longer has ${placeholder}. Update ComposeGenerator.tsx to match.`);
        }
      }
      return compose;
    },
    contentLoaded: async ({ content, actions }) => actions.setGlobalData({ compose: content }),
    getPathsToWatch: () => [COMPOSE_FILE],
  };
}

const config: Config = {
  title: 'WiZ control app',
  tagline: 'Architecture decisions and working journal',
  url: 'https://juan19932carlos.github.io',
  baseUrl: '/wiz-control-app/',
  organizationName: 'juan19932carlos',
  projectName: 'wiz-control-app',
  trailingSlash: false,
  onBrokenLinks: 'throw',

  markdown: {
    format: 'detect',
    mermaid: true,
  },
  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      {
        docs: {
          path: '../decisions',
          routeBasePath: 'decisions',
        },
        blog: false,
        theme: { customCss: './src/css/custom.css' },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    composeFilePlugin,
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'guide',
        path: '../guide',
        routeBasePath: 'guide',
      },
    ],
    [
      '@docusaurus/plugin-content-docs',
      {
        id: 'journal',
        path: '../journal',
        routeBasePath: 'journal',
      },
    ],
  ],

  themeConfig: {
    navbar: {
      title: 'WiZ control app',
      items: [
        { to: '/guide/install', label: 'Install', position: 'right', activeBaseRegex: '/guide' },
        { to: '/decisions/tech-stack', label: 'Decisions', position: 'right', activeBaseRegex: '/decisions' },
        { to: '/journal', label: 'Journal', position: 'right', activeBaseRegex: '/journal' },
      ],
    },
    footer: { style: 'light' },
  } satisfies Preset.ThemeConfig,
};

export default config;
