import { defineConfig } from 'astro/config';

// 部署 GitHub Pages 时通过环境变量 BASE_URL 设置子路径
// 例：BASE_URL=/ai-course-companion npm run build
const base = process.env.BASE_URL || '/';

export default defineConfig({
  site: 'https://aliangzhendemeng.github.io',
  base,
});
