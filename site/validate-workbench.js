const fs = require('fs');

const css = fs.readFileSync('site/styles.css', 'utf8');

const expectations = [
  ['bounded spatial introduction', '.intro{min-height:330px;display:grid;grid-template-columns:repeat(12,1fr);gap:18px;align-items:center;padding:42px 0 34px'],
  ['bounded desktop headline', 'font-size:clamp(38px,4.4vw,64px)'],
  ['compact bench padding', '.bench{padding:42px 0 86px}'],
  ['compact investigation rows', 'min-height:132px'],
  ['offset investigation index', '.lab-row:nth-of-type(2){margin-left:12%}'],
  ['spatial investigation canvas', '.investigation{position:relative;display:grid;grid-template-columns:repeat(12,1fr)'],
  ['linear responsive fallback', '.lab-row,.lab-row:nth-of-type(n){width:100%;margin-left:0']
];

for (const [label, marker] of expectations) {
  if (!css.includes(marker)) throw new Error(`Workbench budget failed: ${label}`);
}

console.log('Spatial desktop workbench budget validated.');
