const puppeteer = require("puppeteer-core");
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const OUT = "C:\\Users\\sushr\\ai_tutor\\evidence\\frontend-003\\";

(async () => {
  const b = await puppeteer.launch({
    executablePath: EDGE,
    headless: "new",
    args: ["--disable-gpu"],
    defaultViewport: { width: 1600, height: 1000 },
  });
  const p = await b.newPage();
  const gets = [];
  p.on("request", (r) => {
    if (r.method() === "GET" && /\/teacher\//.test(r.url())) gets.push(r.url().replace(/^https?:\/\/[^/]+/, ""));
  });
  p.on("response", async (r) => {
    if (/\/teacher\//.test(r.url()) && r.status() >= 400) console.log("HTTP", r.status(), r.url().slice(-70));
  });

  // teacher door: /login must route role=teacher to /teacher
  await p.goto("http://localhost:5173/login", { waitUntil: "networkidle2" });
  await p.type('input[type="email"]', "ravi@example.edu");
  await p.type('input[type="password"]', "demo1234");
  await p.click('button[type="submit"]');
  await p.waitForFunction(() => location.pathname === "/teacher", { timeout: 45000 });
  console.log("teacher door: /login ->", await p.evaluate(() => location.pathname));

  // heatmap: real data or a real empty state, never the geometry mock
  await p.waitForFunction(
    () => document.body.textContent.includes("Identified Mental Models"),
    { timeout: 30000 },
  );
  await new Promise((r) => setTimeout(r, 3500));
  const heat = await p.evaluate(() => {
    const t = document.body.textContent ?? "";
    return {
      teacherName: t.includes("Ravi Menon"),
      noGeometryMock: !t.includes("division as always shrinking") && !t.includes("Dr. Sarah Ascent"),
      rowCount: [...document.querySelectorAll("article, h4")].filter((x) =>
        (x.textContent ?? "").match(/Chooses GET|URL|Django|path|model|form|template|http/i),
      ).length,
      hasEmptyState: t.includes("Nothing confirmed yet"),
      classSize: (t.match(/Class size: \d+/) || [])[0],
    };
  });
  console.log("heatmap:", JSON.stringify(heat));
  await p.screenshot({ path: OUT + "teacher-heatmap.png" });

  // sidebar -> uncertainty flags
  await p.evaluate(() => {
    [...document.querySelectorAll("a[data-path]")].find((a) => a.dataset.path === "uncertainty-flags")?.click();
  });
  await p.waitForFunction(() => document.body.textContent.includes("Uncertainty Flags"), { timeout: 15000 });
  await new Promise((r) => setTimeout(r, 2500));
  const flags = await p.evaluate(() => ({
    openCount: (document.body.textContent.match(/Open \((\d+)\)/) || [])[1],
    hasRealQuestion: [...document.querySelectorAll("article h3")].length,
    emptyOk: document.body.textContent.includes("No open flags"),
  }));
  console.log("flags:", JSON.stringify(flags));
  await p.screenshot({ path: OUT + "teacher-flags.png" });

  // sidebar -> gap map
  await p.evaluate(() => {
    [...document.querySelectorAll("a[data-path]")].find((a) => a.dataset.path === "gap-map")?.click();
  });
  await p.waitForFunction(() => document.body.textContent.includes("Prerequisite Gap Map"), { timeout: 15000 });
  await new Promise((r) => setTimeout(r, 2500));
  const gaps = await p.evaluate(() => ({
    concepts: [...document.querySelectorAll("article h3")].map((x) => (x.textContent ?? "").slice(0, 40)).slice(0, 5),
    fromCourse: (document.body.textContent.match(/From [A-Z][^•]{3,30}/g) || []).slice(0, 3),
  }));
  console.log("gap-map:", JSON.stringify(gaps));
  await p.screenshot({ path: OUT + "teacher-gapmap.png" });

  // sidebar -> reteach
  await p.evaluate(() => {
    [...document.querySelectorAll("a[data-path]")].find((a) => a.dataset.path === "suggested-reteach")?.click();
  });
  await p.waitForFunction(() => document.body.textContent.includes("Suggested Reteach"), { timeout: 15000 });
  await new Promise((r) => setTimeout(r, 2500));
  const reteach = await p.evaluate(() => {
    const t = document.body.textContent ?? "";
    return {
      drafts: (t.match(/Drafts awaiting approval \((\d+)\)/) || [])[1],
      assigned: (t.match(/Assigned to the class \((\d+)\)/) || [])[1],
      draftButton: !![...document.querySelectorAll("button")].find((x) =>
        (x.textContent ?? "").includes("Draft top 3"),
      ),
    };
  });
  console.log("reteach:", JSON.stringify(reteach));
  await p.screenshot({ path: OUT + "teacher-reteach.png" });

  console.log("teacher GETs:", JSON.stringify([...new Set(gets)]));
  await b.close();
})().catch((e) => {
  console.error("FAIL:", e.message);
  process.exit(1);
});
