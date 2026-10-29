/** Browser contracts for the public homepage; uses the existing pinned media runtime. */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const { chromium } = require("playwright-core");
const { createServer } = require("node:http");
const { readFile } = require("node:fs/promises");
const { join, resolve } = require("node:path");
const { mkdir } = require("node:fs/promises");

/** Ensures discovery, persistence, all palettes, and responsive layouts work under a Pages prefix. */
test("Homepage browsing and every theme work on GitHub project Pages", async () => {
  const directory = resolve(__dirname, "../../dist");
  const prefix = process.env.SITE_PATH || "/nice-skills/";
  const server = createServer(async (request, response) => {
    const name = (request.url.startsWith(prefix) ? request.url.slice(prefix.length) : "not-found") || "index.html";
    if (!/^(index.html|app.js|styles.css|themes.css|favicon.svg)$/.test(name)) {
      response.writeHead(404).end();
      return;
    }
    try {
      const types = { css: "text/css", js: "text/javascript", svg: "image/svg+xml", html: "text/html" };
      response.setHeader("Content-Type", types[name.split(".").pop()]);
      response.end(await readFile(join(directory, name)));
    } catch {
      response.writeHead(404).end();
    }
  });
  await new Promise((ready) => server.listen(0, "127.0.0.1", ready));
  let browser;
  try {
    browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
    const url = `http://127.0.0.1:${server.address().port}${prefix}`;
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("response", (response) => {
      if (response.status() >= 400) errors.push(response.url());
    });
    await page.goto(url);
    await page.getByLabel("Your theme").waitFor({ state: "visible" });
    const catalog = await readFile(resolve(__dirname, "../../skills/README.md"), "utf8");
    const skillCount = catalog.split("\n").filter((line) => line.startsWith("| [")).length;
    assert.equal(await page.locator(".skill:visible").count(), skillCount);
    const panelWidth = await page.locator(".palette").evaluate((element) => element.getBoundingClientRect().width);
    const introWidth = await page.locator(".intro").evaluate((element) => element.getBoundingClientRect().width);
    assert.ok(panelWidth >= introWidth - 1, "Theme panel should occupy at least half the hero width");
    const themes = await page.locator("#theme option").evaluateAll((options) => options.map((option) => option.value));
    assert.equal(themes.length, 51);
    for (const slug of themes) {
      await page.getByLabel("Your theme").selectOption(slug);
      assert.equal(await page.locator("html").getAttribute("data-palette"), slug);
      const styles = await page.evaluate(() => {
        const root = getComputedStyle(document.documentElement);
        return {
          primary: root.getPropertyValue("--mca-primary").trim(),
          swatch: document.getElementById("primary-hex").textContent,
          background: getComputedStyle(document.body).backgroundColor,
        };
      });
      assert.equal(styles.primary, styles.swatch);
      assert.notEqual(styles.background, "rgba(0, 0, 0, 0)");
    }
    await page.getByLabel("Your theme").selectOption(themes[0]);
    await page.getByRole("button", { name: "Previous theme", exact: true }).click();
    assert.equal(await page.getByLabel("Your theme").inputValue(), themes.at(-1));
    await page.getByRole("button", { name: "Next theme", exact: true }).click();
    assert.equal(await page.getByLabel("Your theme").inputValue(), themes[0]);
    await page.getByRole("button", { name: "Next theme", exact: true }).focus();
    await page.keyboard.press("Space");
    assert.equal(await page.getByLabel("Your theme").inputValue(), themes[1]);
    await page.getByRole("button", { name: "Previous theme", exact: true }).focus();
    await page.keyboard.press("Enter");
    assert.equal(await page.getByLabel("Your theme").inputValue(), themes[0]);
    for (let attempt = 0; attempt < 3; attempt += 1) {
      const previous = await page.getByLabel("Your theme").inputValue();
      await page.getByRole("button", { name: "Random theme", exact: true }).click();
      const current = await page.getByLabel("Your theme").inputValue();
      assert.notEqual(current, previous);
      assert.ok(themes.includes(current));
      assert.equal(await page.locator("html").getAttribute("data-palette"), current);
      await page.reload();
      assert.equal(await page.getByLabel("Your theme").inputValue(), current);
    }
    await page.getByLabel("Your theme").selectOption(themes[0]);
    await page.reload();
    assert.equal(await page.getByLabel("Your theme").inputValue(), themes[0]);
    await page.getByLabel("Your theme").selectOption("lavender");
    await page.getByLabel("Find a skill").fill("PDF");
    assert.equal(await page.locator(".skill:visible").count(), 2);
    await page.getByLabel("Browse by focus").selectOption("Documents & data");
    assert.equal(await page.locator(".skill:visible").count(), 1);
    await page.getByLabel("Find a skill").fill("no-such-skill");
    assert.equal(await page.locator("#empty").isVisible(), true);
    await page.getByRole("button", { name: "Show all skills" }).click();
    assert.equal(await page.locator(".skill:visible").count(), skillCount);
    await page.locator(".skill summary").first().click();
    assert.equal(await page.locator(".skill details").first().getAttribute("open"), "");
    await page.locator(".skill summary").first().click();
    await page.evaluate(() => localStorage.setItem("nice-skills-theme", "invalid-theme"));
    await page.reload();
    assert.equal(await page.getByLabel("Your theme").inputValue(), "lavender");
    const screenshots = process.env.SITE_SCREENSHOTS;
    if (screenshots) await mkdir(screenshots, { recursive: true });
    for (const width of [1440, 768, 390, 320]) {
      await page.setViewportSize({ width, height: 1000 });
      await page.emulateMedia({ reducedMotion: "reduce" });
      assert.equal(
        await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
        true,
        `Overflow at ${width}: ${await page.evaluate(() =>
          [...document.querySelectorAll("body *")]
            .filter((el) => el.getBoundingClientRect().right > innerWidth)
            .map((el) => el.className)
            .join(", "),
        )}`,
      );
      if (screenshots) {
        await page.locator(".hero").screenshot({ path: join(screenshots, `${width}-hero.png`) });
        await page.screenshot({ path: join(screenshots, `${width}.png`), fullPage: true });
      }
    }
    await page.goto(url);
    await page.keyboard.press("Tab");
    assert.equal(await page.evaluate(() => document.activeElement.textContent), "Skip to skills");
    assert.deepEqual(errors, []);
    await page.close();
    const noScript = await browser.newContext({ javaScriptEnabled: false });
    const fallback = await noScript.newPage();
    await fallback.goto(url);
    assert.equal(await fallback.locator(".skill:visible").count(), skillCount);
    assert.equal(await fallback.getByRole("link", { name: "Find your next skill" }).isVisible(), true);
    await noScript.close();
    const restricted = await browser.newContext();
    await restricted.addInitScript(() =>
      Object.defineProperty(window, "localStorage", {
        get() {
          throw new Error("Storage blocked");
        },
      }),
    );
    const restrictedPage = await restricted.newPage();
    await restrictedPage.goto(url);
    await restrictedPage.getByLabel("Your theme").selectOption(themes[0]);
    assert.equal(await restrictedPage.locator("html").getAttribute("data-palette"), themes[0]);
    await restrictedPage.getByRole("button", { name: "Next theme", exact: true }).click();
    assert.equal(await restrictedPage.getByLabel("Your theme").inputValue(), themes[1]);
    await restricted.close();
  } finally {
    if (browser) await browser.close();
    await new Promise((done) => server.close(done));
  }
});
