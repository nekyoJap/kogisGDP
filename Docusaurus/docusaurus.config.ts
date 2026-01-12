import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: '仕様書ドキュメント',
  tagline: 'プロジェクト仕様書',
  favicon: 'img/favicon.ico',

  // 本番環境のURL設定（デプロイ時に更新）
  url: 'https://your-docusaurus-site.example.com',
  baseUrl: '/',

  // GitHub pages デプロイメント設定（使用する場合）
  organizationName: 'your-org',
  projectName: 'your-project',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // 国際化設定
  i18n: {
    defaultLocale: 'ja',
    locales: ['ja'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          // ドキュメント編集リンク（使用する場合）
          // editUrl: 'https://github.com/your-org/your-project/tree/main/',
        },
        blog: false, // 仕様書なのでブログ機能は無効化
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // ソーシャルカード画像（任意）
    // image: 'img/docusaurus-social-card.jpg',
    navbar: {
      title: '仕様書',
      logo: {
        alt: 'Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'ドキュメント',
        },
        // GitHub リンク（使用する場合）
        // {
        //   href: 'https://github.com/your-org/your-project',
        //   label: 'GitHub',
        //   position: 'right',
        // },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'ドキュメント',
          items: [
            {
              label: 'はじめに',
              to: '/docs/intro',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Your Project. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;