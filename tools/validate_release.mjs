import { access, readFile } from 'node:fs/promises';

const required = ['index.html','live-grid.html','grid-canvas.js','grid-live.css','legacy.html','data/grid-core.json','watchdog.css','watchdog.js','README.md','docs/BUILD_STATUS.md','docs/CRASH_INVESTIGATION.md','LICENSE','LICENSE-APACHE','LICENSE-MIT','NOTICE','.nojekyll'];
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
if (!js.includes('MODELED-SCREENING')) failures.push('missing truth label in preserved watchdog module');
if ((html + legacy + liveGrid + canvas).includes('127.0.0.1:8080/log')) failures.push('development localhost logger remains in production assets');
if (/INL RAVEN Probabilistic Risk Output/i.test(html + legacy + liveGrid)) failures.push('unreceipted RAVEN values are attributed as validated output');
if (!html.includes('src="grid-canvas.js"') || html.includes('<iframe') || html.includes('watchdog.js')) {
  failures.push('default route must load the bounded Canvas renderer directly without an iframe or auto-opening watchdog layer');
}
if (!html.includes('full 4D simulator in progress')) failures.push('default route does not disclose that the full simulator is incomplete');
if (!canvas.includes('BUILD_STEPS = 32') || canvas.includes('setInterval')) failures.push('first playable is missing bounded animation safeguards');
if (!readme.includes('idealized') || !readme.includes('12 selected buses')) failures.push('model-scope disclosure missing from README');

if (failures.length) {
  console.error('Release validation failed:\n- ' + failures.join('\n- '));
  process.exit(1);
}
console.log('Release validation passed: required files, secret boundary, truth labels, and model-scope disclosures present.');
