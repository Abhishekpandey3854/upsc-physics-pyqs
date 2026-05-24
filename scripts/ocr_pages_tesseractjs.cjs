const fs = require('fs');
const path = require('path');
const { createWorker } = require('tesseract.js');

const root = path.resolve(__dirname, '..');
const pageDir = path.join(root, 'text', 'pages');
const outDir = path.join(root, 'text', 'tesseract_ocr');
fs.mkdirSync(outDir, { recursive: true });

function groupPages() {
  const files = fs.readdirSync(pageDir)
    .filter((name) => /^20\d{2}_Paper_I{1,2}_p\d{2}\.png$/.test(name))
    .sort();
  const grouped = new Map();
  for (const file of files) {
    const stem = file.replace(/_p\d{2}\.png$/, '');
    if (!grouped.has(stem)) grouped.set(stem, []);
    grouped.get(stem).push(file);
  }
  return grouped;
}

(async () => {
  const worker = await createWorker('eng');
  const grouped = groupPages();
  for (const [stem, pages] of grouped) {
    const outPath = path.join(outDir, `${stem}.txt`);
    if (fs.existsSync(outPath) && fs.statSync(outPath).size > 1000) {
      console.log(`skip ${stem}`);
      continue;
    }
    const chunks = [];
    for (const pageName of pages) {
      const pageNo = pageName.match(/_p(\d{2})\.png$/)[1];
      const { data: { text } } = await worker.recognize(path.join(pageDir, pageName));
      chunks.push(`\n--- PAGE ${Number(pageNo)} ---\n${text}`);
      console.log(`ocr ${pageName}`);
    }
    fs.writeFileSync(outPath, chunks.join('\n'), 'utf8');
  }
  await worker.terminate();
})();
