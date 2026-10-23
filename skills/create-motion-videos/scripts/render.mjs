#!/usr/bin/env node
// Local deterministic capture. Lemo's bundled static server is used under its MIT license.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawn } from 'node:child_process';

const SKILL = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const HELP = `Usage: node scripts/render.mjs <film-directory> [options]

The directory must contain index.html and window.seek(seconds) or window.render(seconds).
Async functions are awaited. Supply window.DUR, or pass --duration. READY=false is honored.
Output is a SILENT MP4: add supplied/local audio separately after reviewing the picture.

  --out FILE             MP4 destination (required unless --check-only)
  --runtime DIR          Existing runtime/project or node_modules with playwright-core
  --library DIR          Lemo root; defaults to --runtime if it has core/, else bundled assets/lemo
  --fps NUMBER           Output frames per second (default 30)
  --size WIDTHxHEIGHT    Even pixel dimensions (default 1920x1080)
  --from SECONDS         Start within the film (default 0)
  --duration SECONDS     Clip length; defaults to DUR minus --from
  --samples INTEGER      Temporal samples per output frame, 1–16 (default 1; try 4)
  --shutter FRACTION     Exposure fraction of one frame, >0 and <=1 (default 0.5)
  --check-only           Compare PNG hashes after forward, reverse and fresh-page seeks
  --times A,B,C          Absolute check timestamps; default four points in the clip
  --stills DIRECTORY     Save baseline PNGs and check.json during --check-only
  --timeout-ms NUMBER    Asset/readiness/capture timeout (default 30000)
  --allow-network       Permit page requests outside the local film origin (default blocked)
  --overwrite           Permit replacing the named MP4/still/check files
  --help                Show this help without loading a browser

Environment: PLAYWRIGHT_CHROME overrides Chromium; FFMPEG overrides the ffmpeg executable.
Existing CODEX_PRIMARY_RUNTIME_NODE_MODULES dependencies are recognized automatically.
No package, browser or system-tool installation is performed by this script.
`;

function parse(argv) {
  const o = { fps: 30, width: 1920, height: 1080, from: 0, samples: 1, shutter: 0.5, timeout: 30000 };
  const flags = new Set(['check-only', 'allow-network', 'overwrite']);
  const values = new Set(['out', 'runtime', 'library', 'fps', 'size', 'from', 'duration', 'samples', 'shutter', 'times', 'stills', 'timeout-ms']);
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') { o.help = true; continue; }
    if (!a.startsWith('--')) { if (o.film) throw Error('Supply exactly one film directory.'); o.film = path.resolve(a); continue; }
    const k = a.slice(2);
    if (flags.has(k)) { o[k] = true; continue; }
    if (!values.has(k)) throw Error(`Unknown option: ${a}`);
    const v = argv[++i];
    if (v === undefined || v.startsWith('--')) throw Error(`Missing value for ${a}`);
    o[k] = v;
  }
  if (o.help) return o;
  if (!o.film || !fs.existsSync(path.join(o.film, 'index.html'))) throw Error('Supply a film directory containing index.html.');
  if (!o['check-only'] && !o.out) throw Error('--out is required for video export.');
  if (!o['check-only'] && (o.times || o.stills)) throw Error('--times and --stills are used with --check-only.');
  for (const k of ['fps', 'from', 'samples', 'shutter', 'duration']) {
    if (o[k] !== undefined) { o[k] = Number(o[k]); if (!Number.isFinite(o[k])) throw Error(`Invalid --${k}.`); }
  }
  o.timeout = Number(o['timeout-ms'] ?? o.timeout);
  if (!(o.fps > 0 && o.fps <= 240) || o.from < 0 || (o.duration !== undefined && o.duration <= 0)) throw Error('Use fps in (0,240], a nonnegative start and positive duration.');
  if (!Number.isInteger(o.samples) || o.samples < 1 || o.samples > 16 || !(o.shutter > 0 && o.shutter <= 1)) throw Error('Use 1–16 integer samples and shutter in (0,1].');
  if (!Number.isFinite(o.timeout) || o.timeout < 1000) throw Error('--timeout-ms must be at least 1000.');
  if (o.size) {
    const m = /^(\d+)x(\d+)$/.exec(o.size);
    if (!m) throw Error('--size must be WIDTHxHEIGHT.');
    [o.width, o.height] = [Number(m[1]), Number(m[2])];
  }
  if ([o.width, o.height].some(n => n < 16 || n > 8192 || n % 2)) throw Error('Dimensions must be even integers from 16 to 8192.');
  for (const k of ['out', 'runtime', 'library', 'stills']) if (o[k]) o[k] = path.resolve(o[k]);
  if (o.out && !/\.mp4$/i.test(o.out)) throw Error('--out must end in .mp4.');
  if (o.out && fs.existsSync(o.out) && !o.overwrite) throw Error(`Output exists: ${o.out}; choose another path or use --overwrite.`);
  return o;
}

function resolvePlaywright(o, library) {
  const bases = o.runtime ? [o.runtime] : [library, SKILL, process.cwd(), process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES].filter(Boolean);
  for (const base of bases) {
    try {
      const req = createRequire(path.join(base, '__motion_resolve__.cjs'));
      const pkg = req.resolve('playwright-core/package.json');
      return { chromium: req('playwright-core').chromium, modules: path.dirname(path.dirname(pkg)), package: pkg };
    } catch { /* Try the next existing dependency root; never install implicitly. */ }
  }
  throw Error('playwright-core was not found. Prepare a runtime first, then pass --runtime <directory>.');
}

let browser, server, encoder, work;
let cleaning;
async function cleanup() {
  if (cleaning) return cleaning;
  cleaning = (async () => {
    if (encoder && encoder.exitCode === null) {
      encoder.kill('SIGTERM');
      await new Promise(resolve => {
        const timer = setTimeout(() => { encoder.kill('SIGKILL'); resolve(); }, 1500);
        encoder.once('close', () => { clearTimeout(timer); resolve(); });
      });
    }
    if (browser) await browser.close().catch(() => {});
    if (server) { server.closeAllConnections?.(); await new Promise(resolve => server.close(resolve)); }
    if (work) fs.rmSync(work, { recursive: true, force: true });
  })();
  return cleaning;
}
for (const [sig, code] of [['SIGINT', 130], ['SIGTERM', 143]]) process.once(sig, () => {
  console.error(`Stopped by ${sig}; cleaning up this render.`);
  cleanup().finally(() => process.exit(code));
});
// Upstream serve() can emit a startup error (for example a denied localhost bind)
// before returning its server. Clean up the browser/encoder and exit; never resume.
const emergency = reason => {
  console.error(`Unexpected renderer failure: ${reason?.stack || reason}`);
  cleanup().finally(() => process.exit(1));
};
process.once('uncaughtException', emergency);
process.once('unhandledRejection', emergency);

const MIME = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.cjs': 'text/javascript', '.json': 'application/json', '.wasm': 'application/wasm', '.css': 'text/css' };

async function timed(promise, milliseconds, label) {
  let timer;
  try {
    return await Promise.race([promise, new Promise((_, reject) => {
      timer = setTimeout(() => reject(Error(`${label} exceeded ${milliseconds} ms.`)), milliseconds);
    })]);
  } finally { clearTimeout(timer); }
}

async function openPage(o, url, modules) {
  const context = await browser.newContext({ viewport: { width: o.width, height: o.height }, deviceScaleFactor: 1, serviceWorkers: 'block' });
  context.setDefaultTimeout(o.timeout);
  context.setDefaultNavigationTimeout(o.timeout);
  const page = await context.newPage(), errors = new Set(), origin = new URL(url).origin;
  const fail = message => errors.add(message);
  page.on('pageerror', e => fail(`Page error: ${e.message}`));
  page.on('console', m => { if (m.type() === 'error') fail(`Console error: ${m.text()}`); });
  page.on('response', r => { if (r.status() >= 400) fail(`HTTP ${r.status()}: ${r.url()}`); });
  page.on('requestfailed', r => fail(`Request failed: ${r.url()} (${r.failure()?.errorText})`));
  await context.addInitScript(() => { window.__MOTION_CAPTURE__ = true; });
  await context.route('**/*', async route => {
    try {
      const u = new URL(route.request().url());
      if (!o['allow-network'] && u.origin !== origin && !['data:', 'blob:', 'about:'].includes(u.protocol)) {
        fail(`External request blocked: ${u.href}`); await route.abort(); return;
      }
      if (u.origin === origin && u.pathname === '/favicon.ico') { await route.fulfill({ status: 204 }); return; }
      // A separate writable runtime can provide node_modules while /core stays in the pinned library.
      if (u.origin === origin && u.pathname.startsWith('/node_modules/')) {
        const tail = decodeURIComponent(u.pathname.slice('/node_modules/'.length));
        const file = path.resolve(modules, tail);
        if (!file.startsWith(modules + path.sep)) throw Error('Dependency path escapes node_modules.');
        const body = await fs.promises.readFile(file);
        await route.fulfill({ status: 200, contentType: MIME[path.extname(file)] || 'application/octet-stream', body });
        return;
      }
      await route.continue();
    } catch (e) { fail(`Asset load failed: ${e.message}`); await route.abort().catch(() => {}); }
  });
  if (!o['allow-network'] && context.routeWebSocket) await context.routeWebSocket('**/*', ws => {
    fail(`WebSocket blocked during offline capture: ${ws.url()}`); ws.close();
  });
  const healthy = () => { if (errors.size) throw Error([...errors].join('\n')); };
  await page.goto(url, { waitUntil: 'load' });
  healthy();
  try {
    await page.waitForFunction(() => (typeof window.seek === 'function' || typeof window.render === 'function') && (window.READY === undefined || window.READY === true));
  } catch (e) {
    healthy();
    throw Error(`Scene did not expose seek(t)/render(t) with READY=true (or absent) within ${o.timeout} ms: ${e.message}`);
  }
  await timed(page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(async img => {
      await img.decode();
      if (!img.naturalWidth) throw Error(`Image did not load: ${img.currentSrc || img.src}`);
    }));
  }), o.timeout, 'Initial font/image loading');
  healthy();
  return { context, page, healthy, timeout: o.timeout };
}

async function capture(session, t) {
  session.healthy();
  await timed(session.page.evaluate(async time => {
    const draw = typeof window.seek === 'function' ? window.seek : window.render;
    await draw.call(window, time);
    // Flush style/layout and two compositor frames before capturing DOM transforms.
    document.documentElement.getBoundingClientRect();
    await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    await document.fonts.ready;
    await Promise.all([...document.images].map(img => img.decode()));
  }, t), session.timeout, `Drawing time ${t}s`);
  session.healthy();
  const png = await session.page.screenshot({ type: 'png', caret: 'hide' });
  session.healthy();
  return png;
}

async function check(o, session, url, modules, duration) {
  const end = o.from + duration;
  const times = o.times ? o.times.split(',').map(Number) : [o.from, o.from + duration * .37, o.from + duration * .73, Math.max(o.from, end - 1 / o.fps)];
  if (!times.length || times.some(t => !Number.isFinite(t) || t < o.from || t >= end)) throw Error('--times must contain absolute seconds inside the selected clip, excluding its endpoint.');
  const unique = [...new Set(times)].sort((a, b) => a - b), hashes = new Map(), results = [];
  if (o.stills) fs.mkdirSync(o.stills, { recursive: true });
  const write = (file, data) => fs.writeFileSync(file, data, { flag: o.overwrite ? 'w' : 'wx' });
  for (const [i, t] of unique.entries()) {
    const png = await capture(session, t), hash = createHash('sha256').update(png).digest('hex');
    hashes.set(t, hash); results.push({ time: t, sha256: hash });
    if (o.stills) write(path.join(o.stills, `frame_${String(i).padStart(3, '0')}_t_${t.toFixed(6).replace('.', 'p')}.png`), png);
  }
  const compare = async (p, label) => {
    for (const t of [...unique].reverse()) {
      const actualPng = await capture(p, t);
      const hash = createHash('sha256').update(actualPng).digest('hex');
      if (hash !== hashes.get(t) && o.stills) write(path.join(o.stills, `mismatch_${t.toFixed(6)}.png`), actualPng);
      if (hash !== hashes.get(t)) throw Error(`Determinism check failed at ${t}s (${label}). Saved baseline stills, if requested, remain available.`);
    }
  };
  await compare(session, 'reverse seek after other timestamps');
  await session.context.close();
  const fresh = await openPage(o, url, modules);
  await compare(fresh, 'fresh browser context, reverse order');
  await fresh.context.close();
  const report = { passed: true, method: 'Exact PNG SHA-256; forward baseline, reverse seeks, fresh-context reverse seeks.', width: o.width, height: o.height, frames: results };
  if (o.stills) write(path.join(o.stills, 'check.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
}

async function encode(o, session, duration) {
  // Floor to complete frames: no shutter sample can extend beyond the selected clip.
  const frames = Math.floor(duration * o.fps + 1e-7);
  if (frames < 1) throw Error('The clip is shorter than one output frame.');
  fs.mkdirSync(path.dirname(o.out), { recursive: true });
  work = fs.mkdtempSync(path.join(path.dirname(o.out), '.motion-render-'));
  const partial = path.join(work, 'video.mp4'), samples = o.samples;
  const filters = samples > 1
    ? `format=gbrp,tmix=frames=${samples}:weights='${Array(samples).fill(1).join(' ')}':scale=${1 / samples},select='eq(mod(n,${samples}),${samples - 1})',setpts=N/(${o.fps}*TB),format=yuv420p`
    : 'format=yuv420p';
  const args = ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(o.fps * samples), '-c:v', 'png', '-i', 'pipe:0', '-vf', filters,
    '-an', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-r', String(o.fps), '-fps_mode', 'cfr', '-frames:v', String(frames), '-movflags', '+faststart', 'video.mp4'];
  let stderr = '', spawnError;
  const requestedEncoder = process.env.FFMPEG || 'ffmpeg';
  const executable = /[/\\]/.test(requestedEncoder) ? path.resolve(requestedEncoder) : requestedEncoder;
  encoder = spawn(executable, args, { cwd: work, stdio: ['pipe', 'ignore', 'pipe'] });
  encoder.stderr.on('data', b => { stderr = (stderr + b.toString()).slice(-12000); });
  encoder.stdin.on('error', () => {});
  const finished = new Promise((resolve, reject) => {
    encoder.once('error', e => { spawnError = e; reject(e); });
    encoder.once('close', code => code === 0 ? resolve() : reject(Error(`FFmpeg failed (${code}): ${stderr || spawnError?.message || 'no diagnostic'}`)));
  });
  finished.catch(() => {}); // Errors are awaited below; avoid an early unhandled rejection while capturing.
  console.log(`Capturing ${frames} frames at ${o.fps} fps, ${o.width}x${o.height}, ${samples} sample(s)/frame; silent output.`);
  try {
    for (let f = 0; f < frames; f++) {
      for (let s = 0; s < samples; s++) {
        const offset = samples === 1 ? 0 : o.shutter * (s + .5) / samples;
        const png = await capture(session, o.from + (f + offset) / o.fps);
        if (spawnError) throw spawnError;
        await new Promise((resolve, reject) => encoder.stdin.write(png, e => e ? reject(e) : resolve()));
      }
      if (f % Math.max(1, Math.round(o.fps * 5)) === 0 || f === frames - 1) console.log(`Frame ${f + 1}/${frames}`);
    }
    encoder.stdin.end();
    await finished;
  } catch (e) { throw Error(`${e.message}${stderr ? '\n' + stderr : ''}`); }
  session.healthy();
  if (o.overwrite) fs.renameSync(partial, o.out);
  else { fs.linkSync(partial, o.out); fs.unlinkSync(partial); } // Exclusive final creation; no overwrite race.
  console.log(JSON.stringify({ output: o.out, frames, fps: o.fps, duration: frames / o.fps, requestedDuration: duration, width: o.width, height: o.height, samples, shutter: samples > 1 ? o.shutter : null, audio: false }));
}

async function main() {
  const o = parse(process.argv.slice(2));
  if (o.help) { console.log(HELP); return; }
  const library = o.library || (o.runtime && fs.existsSync(path.join(o.runtime, 'core/render/serve.mjs')) ? o.runtime : path.join(SKILL, 'assets/lemo'));
  const serving = path.join(library, 'core/render/serve.mjs');
  if (!fs.existsSync(serving)) throw Error(`Missing bundled server: ${serving}. Supply --library <Lemo-root>.`);
  const runtime = resolvePlaywright(o, library);
  console.log(`Playwright: ${runtime.package}`);
  // Launch before opening a server so a missing browser leaves no listening socket.
  browser = await runtime.chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROME || undefined, args: ['--disable-partial-raster', '--force-color-profile=srgb', '--font-render-hinting=none'], timeout: o.timeout });
  const { serve, pageURL } = await import(pathToFileURL(serving).href);
  const hosted = await serve(library); server = hosted.server;
  const url = new URL(pageURL(library, hosted.port, o.film)); url.searchParams.set('capture', '1');
  const session = await openPage(o, url.href, runtime.modules);
  const declared = await session.page.evaluate(() => Number(window.DUR));
  const duration = o.duration ?? (declared - o.from);
  if (!(Number.isFinite(duration) && duration > 0)) throw Error('Provide positive window.DUR or --duration.');
  if (Number.isFinite(declared) && declared > 0 && o.from + duration > declared + 1e-7) throw Error('The selected clip exceeds window.DUR.');
  if (o['check-only']) await check(o, session, url.href, runtime.modules, duration);
  else await encode(o, session, duration);
}

try { await main(); }
catch (e) { console.error(`ERROR: ${e.message}`); process.exitCode = 1; }
finally { await cleanup(); }
