
const playwright = require('playwright');
(async () => {
  const browser = await playwright['chromium'].launch({
    // headless: false, slowMo: 100, // Uncomment to visualize test
  });
  const page = await browser.newPage();

  // Load "https://sync.ksdatacloud.com/station/2099123100000000/residential/overview"
  await page.goto('https://sync.ksdatacloud.com/station/2099123100000000/residential/overview');

  // Resize window to 1920 x 937
  await page.setViewportSize({ width: 1920, height: 937 });

  await browser.close();
})();
