const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");

function loadPuppeteer() {
  try {
    return require("puppeteer");
  } catch (error) {
    throw new Error(
      "Puppeteer is not installed. Run `npm install` in the backend directory."
    );
  }
}

async function main() {
  const [, , modeArg, sourceArg, outputArg] = process.argv;
  const sourceType = modeArg === "--url" || modeArg === "--file" ? modeArg.slice(2) : "file";
  const inputArg = sourceType === "file" && modeArg !== "--file" ? modeArg : sourceArg;
  const outputPathArg = sourceType === "file" && modeArg !== "--file" ? sourceArg : outputArg;

  if (!inputArg || !outputPathArg) {
    throw new Error(
      "Usage: node html_to_pdf_puppeteer.js [--file <input.html> | --url <url>] <output.pdf>"
    );
  }

  if (!["file", "url"].includes(sourceType)) {
    throw new Error("Source type must be --file or --url.");
  }

  const outputPath = path.resolve(outputPathArg);
  let pageUrl = inputArg;

  if (sourceType === "file") {
    const inputPath = path.resolve(inputArg);
    if (!fs.existsSync(inputPath)) {
      throw new Error(`Input HTML file not found: ${inputPath}`);
    }
    pageUrl = pathToFileURL(inputPath).href;
  }

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });

  const puppeteer = loadPuppeteer();
  const launchOptions = {
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  };

  if (process.env.PUPPETEER_EXECUTABLE_PATH) {
    launchOptions.executablePath = process.env.PUPPETEER_EXECUTABLE_PATH;
  }

  const browser = await puppeteer.launch(launchOptions);
  try {
    const page = await browser.newPage();
    page.setDefaultNavigationTimeout(120000);
    page.setDefaultTimeout(120000);

    await page.setViewport({ width: 1280, height: 900, deviceScaleFactor: 1 });
    await page.goto(pageUrl, {
      waitUntil: sourceType === "url" ? ["load", "networkidle2"] : "load",
      timeout: 120000,
    });

    await page.evaluate(() => {
      if (document.fonts && document.fonts.ready) {
        return document.fonts.ready;
      }
      return Promise.resolve();
    });
    await page.pdf({
      path: outputPath,
      format: "A4",
      printBackground: true,
      preferCSSPageSize: true,
      margin: {
        top: "12mm",
        right: "12mm",
        bottom: "12mm",
        left: "12mm",
      },
    });
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error && error.message ? error.message : error);
  process.exit(1);
});
