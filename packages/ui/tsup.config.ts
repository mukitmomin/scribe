import { defineConfig } from 'tsup';

export default defineConfig({
    entry: ['src/index.tsx'],
    format: ['cjs', 'esm'],
    dts: {
        compilerOptions: {
            skipLibCheck: true,
        },
    },
    external: ['react', 'react-dom', /\.module\.css$/],
    // Keep CSS external - they'll be handled by Next.js
    outExtension({ format }) {
        return {
            js: format === 'cjs' ? '.js' : '.mjs',
        };
    },
    onSuccess: async () => {
        // Copy CSS files to dist
        const { execSync } = await import('child_process');
        execSync('cp -r src/**/*.css dist/ 2>/dev/null || true', { stdio: 'inherit' });
    },
});
