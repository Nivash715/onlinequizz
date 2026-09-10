import { cp, mkdir, rm, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.dirname(fileURLToPath(import.meta.url));
const value = process.env.BACKEND_URL ?? 'https://onlinequizz-2.onrender.com';
if (!value) throw new Error('Set BACKEND_URL to your Render HTTPS origin before building.');
const backend = new URL(value);
if (backend.protocol !== 'https:' || backend.username || backend.password ||
    backend.pathname !== '/' || backend.search || backend.hash) {
  throw new Error('BACKEND_URL must be an HTTPS origin, without credentials, path, query, or fragment.');
}

// Only remove the generated output inside this frontend directory.
const output = path.resolve(root, '.vercel', 'output');
if (!output.startsWith(root + path.sep)) throw new Error('Invalid output path');
await rm(output, { recursive: true, force: true });
await mkdir(path.join(output, 'static'), { recursive: true });
await cp(path.join(root, 'static'), path.join(output, 'static', 'static'), { recursive: true });
await writeFile(path.join(output, 'config.json'), JSON.stringify({
  version: 3,
  routes: [
    { handle: 'filesystem' },
    {
      src: '/(.*)',
      dest: `${backend.origin}/$1`,
      headers: { 'Cache-Control': 'private, no-store' }
    }
  ]
}, null, 2) + '\n');
console.log('Built static assets and Render proxy routes.');
