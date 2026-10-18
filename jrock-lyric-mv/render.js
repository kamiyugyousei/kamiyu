const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const out = process.argv[2], times = process.argv[3] ? process.argv[3].split(',').map(Number) : null;
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('console', m => console.log('console:', m.text())); p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('file://' + path.resolve(__dirname, 'mv.html') + '?capture');
  await p.evaluate(() => window.ready);
  const list = times || Array.from({ length: 150 }, (_, i) => i / 30);
  for (let i = 0; i < list.length; i++) {
    const data = await p.evaluate(t => { render(t); return document.getElementById('c').toDataURL('image/png'); }, list[i]);
    const name = times ? `t${list[i].toFixed(2)}.png` : `f${String(i).padStart(4, '0')}.png`;
    fs.writeFileSync(path.join(out, name), Buffer.from(data.split(',')[1], 'base64'));
  }
  await b.close();
})();
