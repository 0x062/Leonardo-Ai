// leonardo_puppeteer.js
// Automasi UI Leonardo.ai dengan Puppeteer
// Persiapan: siapkan .env dengan:
// LEONARDO_EMAIL=alamat_email_kamu
// LEONARDO_PASSWORD=password_kamu
// DOWNLOAD_DIR: folder tempat menyimpan hasil

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

(async () => {
  const { LEONARDO_EMAIL, LEONARDO_PASSWORD, DOWNLOAD_DIR = './downloads' } = process.env;
  if (!LEONARDO_EMAIL || !LEONARDO_PASSWORD) {
    console.error('Silakan set LEONARDO_EMAIL dan LEONARDO_PASSWORD di .env');
    process.exit(1);
  }
  if (!fs.existsSync(DOWNLOAD_DIR)) fs.mkdirSync(DOWNLOAD_DIR, { recursive: true });

  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();

  const client = await page.target().createCDPSession();
  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: path.resolve(DOWNLOAD_DIR),
    });

  await page.goto('https://leonardo.ai/login', { waitUntil: 'networkidle2' });
  await page.type('input[name="email"]', LEONARDO_EMAIL);
  await page.type('input[name="password"]', LEONARDO_PASSWORD);
  await Promise.all([
    page.click('button[type="submit"]'),
    page.waitForNavigation({ waitUntil: 'networkidle2' }),
  ]);

  // 2. Generate Gambar Anime
  await page.goto('https://leonardo.ai/text-to-image', { waitUntil: 'networkidle2' });
  // Pilih model Anime XL jika perlu, atau skip jika default
  // Enter prompt
  const prompt = fs.readFileSync('prompt.txt', 'utf-8').trim();
  await page.click('textarea[placeholder="Enter your prompt..."]');
  await page.keyboard.type(prompt, { delay: 50 });
  // Submit
  await Promise.all([
    page.click('button:has-text("Generate")'),
    page.waitForSelector('.generation-result img', { timeout: 120000 }),
  ]);
  // Download hasil varian pertama
  const imgUrl = await page.$eval('.generation-result img', el => el.src);
  const view = await page.goto(imgUrl);
  fs.writeFileSync(path.resolve(DOWNLOAD_DIR, 'generated_anime.png'), await view.buffer());

  // 3. Generate Video Motion
  await page.goto('https://leonardo.ai/video-generator', { waitUntil: 'networkidle2' });
  // Upload image
  const [fileChooser] = await Promise.all([
    page.waitForFileChooser(),
    page.click('button:has-text("Upload Image")'),
  ]);
  await fileChooser.accept([path.resolve(DOWNLOAD_DIR, 'generated_anime.png')]);
  // Set duration & motion
  await page.select('select[name="motion_type"]', 'pan_left');
  await page.type('input[name="duration"]', '30');
  // Generate
  await Promise.all([
    page.click('button:has-text("Generate Video")'),
    page.waitForSelector('.video-result video', { timeout: 180000 }),
  ]);
  // Download video
  const vidUrl = await page.$eval('.video-result video source', el => el.src);
  const vidView = await page.goto(vidUrl);
  fs.writeFileSync(path.resolve(DOWNLOAD_DIR, 'anime_motion_video.mp4'), await vidView.buffer());

  // Clean up: hapus image lokal
  fs.unlinkSync(path.resolve(DOWNLOAD_DIR, 'generated_anime.png'));

  console.log('Video siap:', path.resolve(DOWNLOAD_DIR, 'anime_motion_video.mp4'));
  await browser.close();
})();
