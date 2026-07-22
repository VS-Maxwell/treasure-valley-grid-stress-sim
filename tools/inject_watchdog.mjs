import { readFile, writeFile } from 'node:fs/promises';

const path = 'index.html';
let html = await readFile(path, 'utf8');
if (!html.includes('watchdog.css')) {
  html = html.replace(
    '<link href="https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet"/>',
    '<link href="https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet"/>\n<link href="watchdog.css" rel="stylesheet"/>'
  );
}
if (!html.includes('<script src="watchdog.js"></script>')) {
  html = html.replace('</body>', '<script src="watchdog.js"></script>\n</body>');
}
html = html.replace(/<title>.*?<\/title>/, '<title>Treasure Valley Earth-State Watchdog — Grid, Water, Land &amp; Risk</title>');
html = html.replace(/<script>\s*window\.addEventListener\('error',[\s\S]*?<\/script>\s*(?=<meta charset)/, '');
html = html.replace('INL RAVEN Probabilistic Risk Output', 'RAVEN-STYLE SCREENING · UNVALIDATED');
await writeFile(path, html, 'utf8');
console.log('Injected Earth-state watchdog release shell.');
