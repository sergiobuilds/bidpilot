const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "/usr/bin/google-chrome",
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const url = process.argv[2];
  let text = "";
  for (let attempt = 1; attempt <= 4; attempt += 1) {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(12000);
    text = await page.locator("body").innerText();
    if (text.includes("cortex-final-20260802-a")) break;
  }
  const download = page.getByRole("button", { name: "Download proposal draft" });
  const result = {
    run_loaded: text.includes("cortex-final-20260802-a"),
    completed: text.includes("COMPLETED"),
    review_ready: text.includes("Current edited draft passes the score-map red-team checks."),
    not_ready_warning: text.includes("not review-ready"),
    criterion_headings: ["Technical approach", "Comparable delivery", "Delivery team", "Price"].filter((value) => text.includes(value)),
    download_count: await download.count(),
    download_enabled: (await download.count()) === 1 && !(await download.isDisabled()),
    body_text_length: text.length,
  };
  console.log(JSON.stringify(result));
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
