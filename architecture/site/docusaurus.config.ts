import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

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
        theme: {},
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
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
        { to: '/decisions/tech-stack', label: 'Decisions', position: 'right', activeBaseRegex: '/decisions' },
        { to: '/journal', label: 'Journal', position: 'right', activeBaseRegex: '/journal' },
      ],
    },
    footer: { style: 'light' },
  } satisfies Preset.ThemeConfig,
};

export default config;
