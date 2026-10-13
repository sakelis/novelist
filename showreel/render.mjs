// usage: node render.mjs <outDir> [w h fps] [t1,t2,...]   (times => stills only)
import { createRequire } from 'module';
const require = createRequire('/opt/node22/lib/node_modules/');
const { chromium } = require('playwright');
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const [,, outDir, w='1280', h='720', fps='30', times] = process.argv;
fs.mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-angle=swiftshader','--use-gl=angle','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: +w, height: +h } });
page.on('pageerror', e => { console.error('PAGEERR', e.message); process.exit(1); });
page.on('console', m => { if (m.type()==='error') console.error('CONSOLE', m.text()); });
const dir = path.dirname(fileURLToPath(import.meta.url));
await page.goto(`file://${dir}/index.html?render&w=${w}&h=${h}`);
await page.waitForFunction(() => typeof window.frame === 'function');
const list = times ? times.split(',').map(Number) : Array.from({length: 20*+fps}, (_, i) => i/+fps);
let n = 0;
for (const T of list) {
  const data = await page.evaluate(t => { window.frame(t); return document.getElementById('out').toDataURL('image/png'); }, T);
  const name = times ? `still_${T.toFixed(2)}.png` : `f${String(n).padStart(4,'0')}.png`;
  fs.writeFileSync(path.join(outDir, name), Buffer.from(data.split(',')[1], 'base64'));
  if (++n % 60 === 0) console.log('frame', n, '/', list.length);
}
await browser.close();
