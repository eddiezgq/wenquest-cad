// Acceptance check of the live WenQuest CAD help pages (course plan section 13, item 1).
// Runs on a GitHub runner (this session cannot reach the sites). For each page and for a desktop and a
// phone viewport: page errors, counts of lessons / videos / quizzes / interactive blocks, every quiz answered,
// interactive blocks drawn, search, phone overflow, screenshots of each lesson; every video, subtitle and
// poster fetched (first byte only). Writes out/report.json and prints a summary; exit 1 on any failure.
import pw from "playwright";
const { chromium, devices } = pw;
import fs from "node:fs";

const PAGES = process.argv.slice(2);
const EXPECT = { sections: 23, videos: 50, quizzes: 65, anims: 7 };
fs.mkdirSync("out/shots", { recursive: true });
const report = [];
let failures = 0;
const fail = (where, msg) => { failures++; report.push({ where, fail: msg }); console.log(`FAIL ${where}: ${msg}`); };

const browser = await chromium.launch();
for (const url of PAGES) {
  const tag = url.replace(/^https:\/\/|\/static\/help\/wqcad|\/index\.html$/g, "").replace(/[^a-z0-9]+/gi, "_");
  for (const [vp, opts] of [["desktop", { viewport: { width: 1366, height: 900 } }], ["phone", devices["iPhone 13"]]]) {
    const where = `${tag} ${vp}`;
    const ctx = await browser.newContext(opts);
    const page = await ctx.newPage();
    const errs = [];
    page.on("pageerror", e => errs.push(String(e)));
    page.on("console", m => { if (m.type() === "error") errs.push(m.text()); });
    const resp = await page.goto(url, { waitUntil: "networkidle", timeout: 120000 });
    if (!resp || resp.status() >= 400) { fail(where, `page status ${resp && resp.status()}`); await ctx.close(); continue; }
    await page.waitForTimeout(1500);

    const counts = await page.evaluate(() => ({
      sections: document.querySelectorAll("section").length,
      videos: document.querySelectorAll("figure.vid video").length,
      quizzes: document.querySelectorAll(".quiz").length,
      anims: document.querySelectorAll(".anim").length,
    }));
    for (const k of Object.keys(EXPECT)) if (counts[k] !== EXPECT[k]) fail(where, `${k} ${counts[k]} (expected ${EXPECT[k]})`);

    // interactive blocks: something drawn with a real size
    const anims = await page.evaluate(() => [...document.querySelectorAll(".anim")].map(a => {
      const r = a.getBoundingClientRect();
      return { id: a.dataset.anim, kids: a.querySelectorAll("svg, canvas, button, input").length, w: Math.round(r.width), h: Math.round(r.height) };
    }));
    for (const a of anims) if (!a.kids || a.w < 100 || a.h < 60) fail(where, `anim ${a.id} not drawn (${JSON.stringify(a)})`);

    // quizzes: answer each with the right option; the explanation must show and say correct
    const quiz = await page.evaluate(() => {
      const bad = [];
      document.querySelectorAll(".quiz").forEach((qz, i) => {
        const b = qz.querySelector(`button[data-k="${qz.dataset.ok}"]`);
        if (!b) { bad.push(`${i}: no option ${qz.dataset.ok}`); return; }
        b.click();
        const w = qz.querySelector(".why");
        if (w.hidden || !/^✓/.test(w.textContent)) bad.push(`${i}: ${w.textContent.slice(0, 40)}`);
      });
      return bad;
    });
    for (const q of quiz) fail(where, `quiz ${q}`);

    // search
    const hits = await page.evaluate(() => {
      const f = document.querySelector("input.find");
      f.value = document.documentElement.lang === "en" ? "sketch" : "草图";
      f.dispatchEvent(new Event("input"));
      const shown = [...document.querySelectorAll("nav a")].filter(a => a.offsetParent !== null || getComputedStyle(a).display !== "none").length;
      f.value = ""; f.dispatchEvent(new Event("input"));
      return shown;
    });
    if (!hits) fail(where, "search shows nothing");

    // phone: nothing wider than the screen
    if (vp === "phone") {
      const wide = await page.evaluate(() => {
        const W = document.documentElement.clientWidth, out = [];
        if (document.documentElement.scrollWidth > W + 1) out.push(`page ${document.documentElement.scrollWidth} > ${W}`);
        document.querySelectorAll("main *").forEach(el => {
          const r = el.getBoundingClientRect();
          if (r.right > W + 2 && getComputedStyle(el).position !== "fixed" && !el.closest("pre, .tbl, table, .scroll")) {
            const s = el.closest("section"); out.push(`${s ? s.id : "?"} <${el.tagName.toLowerCase()} class="${el.className}"> right ${Math.round(r.right)}`);
          }
        });
        return out.slice(0, 30);
      });
      for (const w of wide) fail(where, `wider than phone: ${w}`);
    }

    // screenshots: top of each lesson
    const ids = await page.evaluate(() => [...document.querySelectorAll("section")].map(s => s.id));
    for (const id of ids) {
      await page.evaluate(i => { document.documentElement.style.scrollBehavior = "auto"; document.getElementById(i).scrollIntoView({ behavior: "instant" }); }, id);
      await page.waitForTimeout(400);
      await page.screenshot({ path: `out/shots/${tag}_${vp}_${id}.png` });
    }

    // media: every video, subtitle and poster (first byte only) — once per page, on desktop
    if (vp === "desktop") {
      const media = await page.evaluate(() => [...new Set([...document.querySelectorAll("figure.vid video, figure.vid source, figure.vid track")]
        .map(e => e.poster ? new URL(e.getAttribute("poster"), location.href).href : (e.src || null)).filter(Boolean)
        .concat([...document.querySelectorAll("figure.vid video")].map(v => new URL(v.getAttribute("poster"), location.href).href)))]);
      let ok = 0;
      for (const m of media) {
        try {
          const r = await ctx.request.get(m, { headers: { Range: "bytes=0-0" }, timeout: 60000 });
          if (r.status() === 200 || r.status() === 206) ok++; else fail(where, `media ${r.status()} ${m}`);
        } catch (e) { fail(where, `media error ${m}: ${e.message.split("\n")[0]}`); }
      }
      report.push({ where, media: media.length, media_ok: ok });
      console.log(`${where}: media ${ok}/${media.length} ok`);
    }
    for (const e of errs) fail(where, `console: ${e.slice(0, 200)}`);
    report.push({ where, counts, anims });
    console.log(`${where}: ${JSON.stringify(counts)}`);
    await ctx.close();
  }
}
await browser.close();
fs.writeFileSync("out/report.json", JSON.stringify(report, null, 1));
console.log(failures ? `${failures} failure(s)` : "all checks passed");
process.exit(failures ? 1 : 0);
