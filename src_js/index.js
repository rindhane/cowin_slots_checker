const {chromium, firefox}=require('playwright');

(async () => {
    const browser =  await chromium.launch({headless:false, slowMo:50});
    const page = await browser.newPage();
    await page.goto('https://www.cowin.gov.in/home',);
    await page.click('text="Enter your PIN"').catch(error=>{console.log(error)});
    await page.fill('444601');
    //await page.screenshot({path:'status.png'})
    await browser.close();
})();