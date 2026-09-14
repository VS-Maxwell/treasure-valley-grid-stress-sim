import { access, readFile } from 'node:fs/promises';

const required = ['index.html','live-grid.html','grid-canvas.js','grid-live.css','legacy.html','data/grid-core.json','watchdog.css','watchdog.js','README.md','LICENSE','LICENSE-APACHE','LICENSE-MIT','NOTICE','.nojekyll'];
const failures = [];
for (const file of required) {
  try { await access(file); } catch { failures.push(`missing required file: ${file}`); }
}
try { await access('.env'); failures.push('tracked or present .env must not enter a release'); } catch {}

const html = await readFile('index.html','utf8');
const legacy = await readFile('legacy.html','utf8');
const liveGrid = await readFile('live-grid.html','utf8');
const canvas = await readFile('grid-canvas.js','utf8');
const js = await readFile('watchdog.js','utf8');
const readme = await readFile('README.md','utf8');
for (const token of ['watchdog.css','watchdog.js','MODELED-SCREENING']) {
  if (!html.includes(token) && !js.includes(token)) failures.push(`missing truth/watchdog token: ${token}`);
}
if ((html + legacy + liveGrid + canvas).includes('127.0.0.1:8080/log')) failures.push('development localhost logger remains in production assets');
if (/INL RAVEN Probabilistic Risk Output/i.test(html + legacy + liveGrid)) failures.push('unreceipted RAVEN values are attributed as validated output');
if (!html.includes('src="live-grid.html"')) failures.push('default wrapper does not load the crash-safe first playable');
if (!canvas.includes('BUILD_STEPS = 32') || canvas.includes('setInterval')) failures.push('first playable is missing bounded animation safeguards');
if (!readme.includes('idealized') || !readme.includes('12 selected buses')) failures.push('model-scope disclosure missing from README');

if (failures.length) {
  console.error('Release validation failed:\n- ' + failures.join('\n- '));
  process.exit(1);
}
console.log('Release validation passed: required files, secret boundary, truth labels, and model-scope disclosures present.');
