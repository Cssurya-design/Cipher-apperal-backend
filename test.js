const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));

  console.log("Navigating to single product page...");
  await page.goto('http://127.0.0.1:8000/sproduct/', { waitUntil: 'networkidle' });

  console.log("Adding to cart...");
  await page.evaluate(() => {
    // Inject a dummy product in localStorage since page loads it
    localStorage.setItem('currentProduct', JSON.stringify({img: '/static/f1.jpg', name: 'Test Shirt', price: '₹78.00'}));
  });
  await page.reload({ waitUntil: 'networkidle' });

  await page.click('#add-to-cart-btn');
  await page.waitForTimeout(500);

  console.log("Navigating to cart page...");
  await page.goto('http://127.0.0.1:8000/cart/', { waitUntil: 'networkidle' });

  const cartItemsCount = await page.evaluate(() => document.querySelectorAll('#cart-body tr').length);
  console.log("Cart items count:", cartItemsCount);

  console.log("Clicking remove...");
  await page.evaluate(() => {
    const removeBtn = document.querySelector('#cart-body a');
    if (removeBtn) removeBtn.click();
  });
  await page.waitForTimeout(500);

  const newCartItemsCount = await page.evaluate(() => document.querySelectorAll('#cart-body tr').length);
  console.log("New Cart items count:", newCartItemsCount);

  await browser.close();
})();
