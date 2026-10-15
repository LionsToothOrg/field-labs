const fs = require('fs');

const css = fs.readFileSync('site/styles.css', 'utf8');

const expectations = [
  ['compact introduction padding', '.intro{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(360px,.8fr);gap:56px;align-items:center;padding:56px 0 46px'],
  ['bounded desktop headline', 'font-size:clamp(38px,5vw,68px)'],
  ['compact bench padding', '.bench{padding:46px 0 76px}'],
  ['compact investigation rows', 'min-height:132px']
];

for (const [label, marker] of expectations) {
  if (!css.includes(marker)) throw new Error(`Workbench budget failed: ${label}`);
}

console.log('Compact desktop workbench budget validated.');
