import { rmSync } from 'node:fs';
import { resolve } from 'node:path';

rmSync(resolve(process.cwd(), 'dist-electron'), { force: true, recursive: true });
