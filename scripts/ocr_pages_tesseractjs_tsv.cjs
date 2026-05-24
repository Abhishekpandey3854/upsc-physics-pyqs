const fs = require('fs');
const path = require('path');
const { createWorker } = require('tesseract.js');

const root = path.resolve(__dirname, '..');
const pageDir = path.join(root, 'text', 'pages');
const outDir = path.join(root, 'text', 'tesseract_tsv');
fs.mkdirSync(outDir, { recursive: true });

function pages() {
  return fs.readdirSync(pageDir)
    .filter((name) => /^20\d{2}_Paper_I{1,2}_p\d{2}\.png$/.test(name))
    .sort();
}

(async () => {
  const worker = await createWorker('eng');
  for (const pageName of pages()) {
    const outPath = path.join(outDir, pageName.replace(/\.png$/, '.tsv'));
    if (fs.existsSync(outPath) && fs.statSync(outPath).size > 1000) {
      console.log(`skip ${pageName}`);
      continue;
    }
    const ret = await worker.recognize(path.join(pageDir, pageName), {}, { tsv: true });
    fs.writeFileSync(outPath, ret.data.tsv || '', 'utf8');
    console.log(`tsv ${pageName}`);
  }
  await worker.terminate();
})();
