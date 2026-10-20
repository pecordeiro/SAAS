// Concatena src/lib/*.js em um único escopo (os Code nodes do n8n não importam arquivos locais).
const fs = require('fs'), path = require('path');
const ORDER = ['csv', 'dedup', 'score', 'suppression', 'funnel', 'draft', 'metrics'];
const dir = path.join(__dirname, '..', 'src', 'lib');

function bundleSource() {
  return ORDER.map(f => fs.readFileSync(path.join(dir, f + '.js'), 'utf8')).join('\n');
}
function load() {
  const src = bundleSource();
  const names = [...src.matchAll(/^(?:function|const)\s+([A-Za-z_]\w*)/gm)].map(m => m[1]);
  return new Function(src + '\nreturn {' + names.join(',') + '};')();
}
module.exports = { bundleSource, load };
