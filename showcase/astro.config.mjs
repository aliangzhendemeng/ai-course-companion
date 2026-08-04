import { defineConfig } from 'astro/config';

// 部署 GitHub Pages 时需设 base: '/ai-course-companion/'；本地预览留空
export default defineConfig({
  site: 'https://aliangzhendemeng.github.io',
  // base: '/ai-course-companion/',
});
