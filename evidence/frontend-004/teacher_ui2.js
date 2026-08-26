const puppeteer = require("puppeteer-core");
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const OUT = "C:\\Users\\sushr\\ai_tutor\\evidence\\frontend-004\\";

const nav = (p, path) =>
  p.evaluate((path) => {
    [...document.querySelectorAll("a[data-path]")].find((a) => a.dataset.path === path)?.click();
  }, path);
const settle = (p, ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.launch({
    executablePath: EDGE,
    headless: "new",
    args: ["--disable-gpu"],
    defaultViewport: { width: 1600, height: 1000 },
  });
  const p = await b.newPage();
  p.on("pageerror", (e) => console.log("PAGEERROR:", e.message.slice(0, 200)));

  await p.goto("http://localhost:5173/login", { waitUntil: "networkidle2" });
  await p.type('input[type="email"]', "ravi@example.edu");
  await p.type('input[type="password"]', "demo1234");
  await p.click('button[type="submit"]');
  await p.waitForFunction(() => location.pathname === "/teacher", { timeout: 45000 });
  await p.waitForSelector('a[data-path="dashboard"]', { timeout: 30000 });
  await settle(p, 1500);

  // 1. overview: real tiles, no fabricated persona/mastery
  await settle(p, 2000);
  const overview = await p.evaluate(() => {
    const t = document.body.textContent ?? "";
    return {
      classSize: (t.match(/Class size/), [...document.querySelectorAll("span")].some((x) => /^\d+$/.test((x.textContent ?? "").trim()) && t.includes("Class size"))),
      tiles: ["Class size", "Open uncertainty flags", "Top misconception share", "Open prerequisite gaps"].every((s) => t.includes(s)),
      noAvgMastery: !t.includes("Avg. Mastery"),
      noSarah: !t.includes("Dr. Sarah Ascent"),
      gapsList: t.includes("Top Learning Gaps") && t.includes("From Computer Science Workshop 1"),
      flagsList: t.includes("Latest Uncertainty Flags"),
    };
  });
  console.log("overview:", JSON.stringify(overview));
  await p.screenshot({ path: OUT + "overview.png" });

  // 2. reasoning paths
  await nav(p, "reasoning-path-breakdown");
  await p.waitForFunction(() => document.body.textContent.includes("Reasoning Path Breakdown"), { timeout: 20000 });
  await settle(p, 2500);
  const rp = await p.evaluate(() => {
    const t = document.body.textContent ?? "";
    const chips = [...document.querySelectorAll("button")].filter((x) => (x.textContent ?? "").match(/^[a-z-]{4,}$/)).map((x) => x.textContent);
    return {
      chips: chips.slice(0, 8),
      realAnswer: t.includes("A real student answered"),
      exampleCount: [...document.querySelectorAll("article")].length,
      reasoningShown: t.includes("The reasoning behind it"),
    };
  });
  console.log("reasoning-paths:", JSON.stringify(rp));
  await p.screenshot({ path: OUT + "reasoning-paths.png" });

  // 3. before/after BEFORE any approval (after === null state)
  await nav(p, "tracking");
  await p.waitForFunction(() => document.body.textContent.includes("Before / After Tracking"), { timeout: 20000 });
  await settle(p, 2500);
  const ba0 = await p.evaluate(() => {
    const t = document.body.textContent ?? "";
    return {
      selectorChips: [...document.querySelectorAll("button")].filter((x) => (x.textContent ?? "").length > 15).length,
      beforeCard: t.includes("Before the reteach") && /confirmed this reasoning/.test(t),
      afterNull: t.includes("No reteach approved for this misconception yet"),
    };
  });
  console.log("before-after (no reteach yet):", JSON.stringify(ba0));

  // 4. approve the reteach draft, then re-check before/after
  await nav(p, "suggested-reteach");
  await p.waitForFunction(() => document.body.textContent.includes("Suggested Reteach"), { timeout: 20000 });
  await settle(p, 2000);
  const approved = await p.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find((x) =>
      (x.textContent ?? "").includes("Approve & assign"),
    );
    if (!btn) return "no draft to approve";
    btn.click();
    return "clicked";
  });
  console.log("approve draft:", approved);
  await settle(p, 4000);
  await nav(p, "tracking");
  await p.waitForFunction(() => document.body.textContent.includes("Before / After Tracking"), { timeout: 20000 });
  await settle(p, 2500);
  const ba1 = await p.evaluate(() => {
    const t = document.body.textContent ?? "";
    return {
      afterPresent: t.includes("After the reteach") && !t.includes("No reteach approved"),
      notMeasured: t.includes("Not measured yet") || t.includes("Nobody has been asked"),
      zeroVsNullHonest: !/delta of zero|0pp/.test(t) || t.includes("Not measured yet"),
    };
  });
  console.log("before-after (reteach just approved):", JSON.stringify(ba1));
  await p.screenshot({ path: OUT + "before-after.png" });

  // 5. verification queue: approve one, reject one
  await nav(p, "content-verification");
  await p.waitForFunction(() => document.body.textContent.includes("Content Verification"), { timeout: 20000 });
  await settle(p, 2500);
  const vq0 = await p.evaluate(() => ({
    cards: [...document.querySelectorAll("article")].length,
    pending: document.body.textContent.includes("PENDING"),
    foundFor: document.body.textContent.includes("Found for:"),
  }));
  console.log("verification queue:", JSON.stringify(vq0));
  // approve the first
  await p.evaluate(() => {
    [...document.querySelectorAll("button")].find((x) => (x.textContent ?? "").trim() === "Approve")?.click();
  });
  await settle(p, 3000);
  // reject flow on the next pending
  const rej = await p.evaluate(() => {
    const btn = [...document.querySelectorAll("button")].find((x) => (x.textContent ?? "").includes("Reject…"));
    if (!btn) return "none pending";
    btn.click();
    return "reject open";
  });
  if (rej === "reject open") {
    await settle(p, 500);
    await p.type('input[placeholder*="Why is this being rejected"]', "Not aligned with the CSW2 syllabus scope");
    await p.evaluate(() => {
      [...document.querySelectorAll("button")].find((x) => (x.textContent ?? "").includes("Confirm reject"))?.click();
    });
    await settle(p, 3000);
  }
  const vq1 = await p.evaluate(() => {
    const t = document.body.textContent ?? "";
    return {
      approvedShown: [...document.querySelectorAll("article")].some((a) => a.textContent?.includes("APPROVED")),
      rejectReasonShown: t.includes("Rejected: Not aligned"),
    };
  });
  console.log("verification after actions:", JSON.stringify(vq1));
  await p.screenshot({ path: OUT + "verification.png" });

  await b.close();
})().catch((e) => {
  console.error("FAIL:", e.message);
  process.exit(1);
});
