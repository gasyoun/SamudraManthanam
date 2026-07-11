import remarkRstTable from './src/remark/rstTable.mjs';

const config = {
  title: 'nkrya-parallel',
  url: 'https://gasyoun.github.io',
  baseUrl: '/SamudraManthanam/',
  organizationName: 'gasyoun',
  projectName: 'SamudraManthanam',
  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',
  onBrokenAnchors: 'ignore',
  presets: [['classic', {
    docs: { path: '.', routeBasePath: '/', sidebarPath: './sidebars.mjs',
            include: [
              '*.mdx',
              'diplom-rubanova/**.mdx',
            ],
            exclude: ['**/node_modules/**', '**/build/**', '**/.docusaurus/**', '**/src/**'],
            remarkPlugins: [remarkRstTable] },
    blog: false, theme: {} }]],
  themeConfig: { navbar: { title: 'nkrya-parallel', items: [
    { type: 'docSidebar', sidebarId: 'docsSidebar', position: 'left', label: 'Docs' } ] } },
};
export default config;
