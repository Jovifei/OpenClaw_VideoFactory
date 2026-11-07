/** Capture-only adapter using the website repo's EXISTING @playwright/test.
 * No test mocks, no backend replacement, no desktop automation, no model download.
 * Results remain captured_unreviewed until reviewed independently by local Codex.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const ORIGIN = 'https://photo.joviluma.com';
const fail = code => { throw new Error(`product_capture:${code}`); };
export const digest = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
export function safeUrl(raw) {
  const u = new URL(raw, ORIGIN);
  if (u.origin !== ORIGIN || !['/', '/sites', '/fireglow', '/cloudsea'].includes(u.pathname) ||
      u.username || u.password || u.hash) fail('url_not_allowed');
  const keys = new Set(['lat','lng','name','elevation','model','view','panel','overlay','night','time','date','mode']);
  for (const [key,value] of u.searchParams) if (!keys.has(key) || value.length > 160) fail('query_not_allowed');
  return u.href;
}
export function validatePlan(p) {
  if (!p || p.schema_version !== '1.0' || p.site_origin !== ORIGIN ||
      p.selector_status !== 'confirmed_against_live_page' || !Array.isArray(p.shots) ||
      p.shots.length < 1 || p.shots.length > 8) fail('plan_not_confirmed');
  if (!p.viewport || !Number.isInteger(p.viewport.width) || !Number.isInteger(p.viewport.height) ||
      p.viewport.width < 360 || p.viewport.width > 1920 || p.viewport.height < 500 || p.viewport.height > 1200 ||
      ![1,2,3].includes(p.device_scale_factor)) fail('viewport_invalid');
  const ids = new Set();
  for (const s of p.shots) {
    if (!/^[a-z][a-z0-9_-]{1,30}$/.test(s.id) || ids.has(s.id)) fail('shot_id_invalid');
    ids.add(s.id);safeUrl(s.url);
    if (!Array.isArray(s.ready_selectors) || !s.ready_selectors.length ||
        s.ready_selectors.some(x => typeof x !== 'string' || !x || x.length > 200) ||
        !Array.isArray(s.required_text) || !s.required_text.length ||
        s.required_text.some(x => typeof x !== 'string' || !x || x.length > 80) ||
        typeof s.require_map_tiles !== 'boolean' || !Array.isArray(s.actions)) fail('readiness_invalid');
    if(s.actions.length > 12) fail('too_many_actions');
    for(const action of s.actions) {
      if(!['click','fill','press'].includes(action.type) || typeof action.selector !== 'string' || !action.selector ||
          action.selector.length > 200 || (action.type === 'fill' && (typeof action.value !== 'string' || action.value.length > 160)) ||
          (action.type === 'press' && !['Enter','Escape','Tab'].includes(action.value))) fail('action_invalid');
    }
  }
  return p;
}
export async function waitForVisibleText(page, text) {
  const matches = page.getByText(text, {exact: false});
  const count = await matches.count();
  for (let index = 0; index < count; index += 1) {
    if (await matches.nth(index).isVisible()) return;
  }
  if (!count) fail(`required_text_missing:${text}`);
  fail(`required_text_not_visible:${text}`);
}
export async function capture(plan, {siteRoot,browserExecutable,out}) {
  validatePlan(plan);
  const req = createRequire(path.join(path.resolve(siteRoot),'package.json'));
  const {chromium} = req('@playwright/test'); // no npx, no install, no browser download
  if(!(await fs.stat(browserExecutable)).isFile()) fail('approved_browser_missing');
  await fs.mkdir(out,{recursive:false}); // caller must give a new attempt folder
  const receipts=[];
  let browser;
  try {
    browser=await chromium.launch({headless:true,executablePath:path.resolve(browserExecutable)});
    const context=await browser.newContext({viewport:plan.viewport,deviceScaleFactor:plan.device_scale_factor,
      locale:'zh-CN',timezoneId:'Asia/Shanghai',permissions:[],serviceWorkers:'block'});
    // Default no microphone/camera/geolocation, no saved account/cookies or mocked API responses.
    for(const shot of plan.shots) {
      const page=await context.newPage();
      const failures=[];
      page.on('response',response=>{if(response.status()>=400) {
        const u=new URL(response.url());failures.push({origin:u.origin,path:u.pathname,status:response.status()});
      }});
      page.on('requestfailed',request=>{const u=new URL(request.url());failures.push({origin:u.origin,path:u.pathname,status:'request_failed'});});
      try {
        const response=await page.goto(safeUrl(shot.url),{waitUntil:'domcontentloaded',timeout:45000});
        if(!response || !response.ok()) fail('document_load_failed');
        safeUrl(page.url());
        for(const action of shot.actions) {
          const locator=page.locator(action.selector);
          if(action.type==='click')await locator.click({timeout:15000});
          if(action.type==='fill')await locator.fill(action.value,{timeout:15000});
          if(action.type==='press')await locator.press(action.value,{timeout:15000});
        }
        safeUrl(page.url());
        for(const selector of shot.ready_selectors)await page.locator(selector).waitFor({state:'visible',timeout:45000});
        for(const text of shot.required_text)await waitForVisibleText(page,text);
        await page.evaluate(async()=>{await document.fonts.ready;});
        if(shot.require_map_tiles)await page.waitForFunction(()=>{
          const images=[...document.querySelectorAll('img.leaflet-tile')].filter(e=>{
            const b=e.getBoundingClientRect();return b.right>0 && b.bottom>0 && b.left<innerWidth && b.top<innerHeight;
          });
          return images.length>0 && images.every(img=>img.complete && img.naturalWidth>1);
        },null,{timeout:45000});
        const capturedAt=new Date().toISOString();
        const bytes=await page.screenshot({type:'png',fullPage:false,animations:'disabled',caret:'hide',scale:'device'});
        const name=`${shot.id}.png`;
        await fs.writeFile(path.join(out,name),bytes,{flag:'wx'});
        const body=await page.locator('body').innerText();
        receipts.push({id:shot.id,filename:name,sha256:digest(bytes),source_url:safeUrl(page.url()),
          captured_at:capturedAt,status:'captured_unreviewed',method:'live_browser_no_mock',
          viewport:plan.viewport,device_scale_factor:plan.device_scale_factor,
          title:await page.title(),required_text:shot.required_text,
          body_sha256:digest(Buffer.from(body,'utf8')),network_failures:failures,
          mocked:false});
      } finally {await page.close();}
    }
    await context.close();
    const receipt={schema_version:'1.0',status:'captured_unreviewed',site_origin:ORIGIN,
      plan_sha256:digest(Buffer.from(JSON.stringify(plan))),captures:receipts};
    await fs.writeFile(path.join(out,'capture_manifest.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
    return receipt;
  } catch(error) {
    await fs.writeFile(path.join(out,'capture_failure.json'),JSON.stringify({status:'failed',partial_captures:receipts,
      error:error instanceof Error?error.message:'capture_failed',human_approval:false},null,2)+'\n',{flag:'wx'});
    throw error;
  } finally {if(browser)await browser.close();}
}
function args(argv) {
  const allowed=['--plan','--site-root','--browser','--out'];const result={};
  for(let i=0;i<argv.length;i+=2){if(!allowed.includes(argv[i]) || !argv[i+1] || argv[i+1].startsWith('--') || result[argv[i]])fail('arguments');result[argv[i]]=argv[i+1];}
  if(allowed.some(x=>!result[x]))fail('arguments');return result;
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const a=args(process.argv.slice(2));
  capture(JSON.parse(await fs.readFile(a['--plan'],'utf8')),{siteRoot:a['--site-root'],browserExecutable:a['--browser'],out:path.resolve(a['--out'])})
    .then(r=>console.log(JSON.stringify({status:r.status,captures:r.captures.length})))
    .catch(e=>{console.error(e.message);process.exitCode=1;});
}
