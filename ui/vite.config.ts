import { defineConfig } from 'vite';
import basicSsl from '@vitejs/plugin-basic-ssl';
import react from '@vitejs/plugin-react';

export default defineConfig(({ command }) => {
  if (command === 'serve') {
    // `vite` or `vite dev`
    return {
      plugins: [basicSsl(), react()],
      server: {
        https: {}, // use default self-signed cert
      },
    };
  } else {
    // `vite build`
    return {
      plugins: [react()],
      server: {
        host: true,
        port: 5173,
      },
      build: {
        outDir: 'dist',
      },
    };
  }
});
