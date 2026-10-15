const fs = require('fs');

const html = fs.readFileSync('site/index.html', 'utf8');
const css = fs.readFileSync('site/styles.css', 'utf8');

const requiredHtml = [
  'Engineering problems,',
  'THE BENCH',
  'Transaction Reliability',
  'AI Workflow Boundaries',
  'id="lab-01"',
  'id="lab-02"',
  'id="run-race"',
  'id="run-boundary"',
  'SYNTHETIC BY DEFAULT',
  'SOURCE + EVIDENCE'
];

const forbiddenHtml = [
  'Real problems.<br>Rebuilt from<br><em>first principles.</em>',
  'ANATOMY OF A SYSTEM'
];

const requiredCss = [
  '--bg:#070a12',
  '--cyan:#4de2ff',
  '--violet:#a679ff',
  '--gold:#ffc857',
  '--green:#58e6a9',
  '--red:#ff6b7a'
];

for (const marker of requiredHtml) {
  if (!html.includes(marker)) throw new Error(`Missing required public-site marker: ${marker}`);
}

for (const marker of forbiddenHtml) {
  if (html.includes(marker)) throw new Error(`Removed oversized-hero marker is still present: ${marker}`);
}

for (const marker of requiredCss) {
  if (!css.includes(marker)) throw new Error(`Missing restored Field Labs palette token: ${marker}`);
}

console.log('Field Labs public workbench structure validated.');
