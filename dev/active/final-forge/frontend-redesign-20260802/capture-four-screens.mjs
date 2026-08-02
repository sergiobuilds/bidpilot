#!/usr/bin/env node
import { execSync, spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";

const target = process.argv[2] || "http://127.0.0.1:8515";
const out = process.argv[3] || "dev/active/final-forge/frontend-redesign-20260802/four-screen-qa";
const width = Number(process.argv[4] || 1440);
const height = Number(process.argv[5] || 900);
const port = 21000 + (process.pid % 10000);
const profile = `/tmp/bidpilot-four-screen-${process.pid}`;
mkdirSync(out, { recursive: true });

const chrome = spawn("google-chrome", [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  "--no-first-run", "--no-default-browser-check", `--remote-debugging-port=${port}`,
  `--user-data-dir=${profile}`, "about:blank",
], { stdio: "ignore", detached: true });

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
function cleanup() {
  try { process.kill(-chrome.pid, "SIGKILL"); } catch {}
  try { execSync(`rm -rf ${profile}`, { stdio: "ignore" }); } catch {}
}

class CDP {
  constructor(socket) {
    this.socket = socket;
    this.id = 0;
    this.pending = new Map();
    socket.addEventListener("message", event => {
      const message = JSON.parse(event.data);
      if (this.pending.has(message.id)) {
        this.pending.get(message.id)(message);
        this.pending.delete(message.id);
      }
    });
  }
  send(method, params = {}, sessionId) {
    const id = ++this.id;
    return new Promise(resolve => {
      this.pending.set(id, resolve);
      this.socket.send(JSON.stringify({ id, method, params, sessionId }));
    });
  }
}

async function evaluate(cdp, sessionId, expression) {
  const response = await cdp.send("Runtime.evaluate", { expression, returnByValue: true }, sessionId);
  return response.result?.result?.value;
}

async function clickButton(cdp, sessionId, label) {
  const clicked = await evaluate(cdp, sessionId, `(()=>{const b=[...document.querySelectorAll('button')].find(x=>x.textContent.trim().includes(${JSON.stringify(label)}));if(!b)return false;b.click();return true})()`);
  if (!clicked) throw new Error(`Button not found: ${label}`);
  await sleep(4500);
}

async function capture(cdp, sessionId, name) {
  await evaluate(cdp, sessionId, "window.scrollTo(0,0)");
  await sleep(500);
  const report = await evaluate(cdp, sessionId, `(()=>({
    viewport: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    heading: document.querySelector('h1')?.textContent.trim() || '',
    buttons: [...document.querySelectorAll('button')].map(x=>x.textContent.trim()).filter(Boolean),
    primaryActionY: [...document.querySelectorAll('button')].find(x=>x.textContent.includes('Open bid decision'))?.getBoundingClientRect().top ?? null,
    sectionNavigator: (()=>{const e=document.querySelector('.br-check');if(!e)return null;const s=getComputedStyle(e);return {display:s.display,columns:s.gridTemplateColumns,top:e.getBoundingClientRect().top,height:e.getBoundingClientRect().height}})(),
    proposalEditorY: document.querySelector('textarea')?.getBoundingClientRect().top ?? null
  }))()`);
  const shot = (await cdp.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false }, sessionId)).result;
  writeFileSync(`${out}/${name}.png`, Buffer.from(shot.data, "base64"));
  return report;
}

async function main() {
  let version;
  for (let index = 0; index < 80; index += 1) {
    try {
      version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
      break;
    } catch { await sleep(100); }
  }
  if (!version) throw new Error("Chrome DevTools endpoint did not start");
  const socket = new WebSocket(version.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    socket.addEventListener("open", resolve);
    socket.addEventListener("error", reject);
  });
  const cdp = new CDP(socket);
  const { targetId } = (await cdp.send("Target.createTarget", { url: "about:blank" })).result;
  const { sessionId } = (await cdp.send("Target.attachToTarget", { targetId, flatten: true })).result;
  await cdp.send("Page.enable", {}, sessionId);
  await cdp.send("Runtime.enable", {}, sessionId);
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width, height, deviceScaleFactor: 1, mobile: width < 600,
  }, sessionId);
  await cdp.send("Page.navigate", { url: target }, sessionId);
  await sleep(15000);

  const reports = {};
  reports.opportunities = await capture(cdp, sessionId, "01-opportunities");
  await clickButton(cdp, sessionId, "Open bid decision");
  reports.decision = await capture(cdp, sessionId, "02-decision");
  await clickButton(cdp, sessionId, "Build the win plan");
  reports.winPlan = await capture(cdp, sessionId, "03-win-plan");
  await clickButton(cdp, sessionId, "Draft proposal with this strategy");
  reports.proposal = await capture(cdp, sessionId, "04-proposal-room");

  writeFileSync(`${out}/report.json`, JSON.stringify({ width, height, reports }, null, 2));
  console.log(JSON.stringify({ width, height, reports }));
  socket.close();
  cleanup();
}

main().catch(error => {
  console.error(error.message);
  cleanup();
  process.exit(1);
});
