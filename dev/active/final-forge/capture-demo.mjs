#!/usr/bin/env node
import { execSync, spawn } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";

const target = process.argv[2] || "http://127.0.0.1:8505";
const out = process.argv[3] || "dev/active/final-forge/demo-frames";
const port = 19000 + (process.pid % 10000);
const profile = `/tmp/bidpilot-demo-${process.pid}`;
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

async function main() {
  let version;
  for (let index = 0; index < 60; index += 1) {
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
    width: 1440, height: 900, deviceScaleFactor: 1, mobile: false,
  }, sessionId);
  await cdp.send("Page.navigate", { url: target }, sessionId);
  await sleep(15000);

  const scenes = [
    ["01-verdict", null],
    ["02-score-map", "Official weighted evaluation score map"],
    ["03-win-position", "Selected Win Position"],
    ["04-proposal", "Proposal sections"],
    ["05-owned-work", "Owned pursuit work"],
    ["06-provenance", "Execution provenance"],
  ];
  for (const [name, heading] of scenes) {
    const expression = heading
      ? `(()=>{const e=[...document.querySelectorAll('h1,h2,h3')].find(x=>x.textContent.trim()===${JSON.stringify(heading)});if(!e)return false;e.scrollIntoView({block:'start'});window.scrollBy(0,-70);return true})()`
      : "(()=>{window.scrollTo(0,0);return true})()";
    await cdp.send("Runtime.evaluate", { expression }, sessionId);
    await sleep(900);
    const shot = (await cdp.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false }, sessionId)).result;
    writeFileSync(`${out}/${name}.png`, Buffer.from(shot.data, "base64"));
    console.log(`${name}.png`);
  }
  socket.close();
  cleanup();
}

main().catch(error => {
  console.error(error.message);
  cleanup();
  process.exit(1);
});
