"""
Browser module for web scraping and screenshot capture.
"""
import asyncio
import re
from typing import Dict, List, Any, Tuple

from playwright.async_api import async_playwright, ViewportSize
from loguru import logger

from nhk_weather.config.config import config
from nhk_weather.core.models import CityWeather

# JavaScript for scraping weather data
WEATHER_SCRAPE_JS = """
() => Array.from(document.querySelectorAll('.weather-forecast-plate')).map(n => ({
    name: n.querySelector('.weather-forecast-name')?.textContent.trim() || '',
    alt:  n.querySelector('.weather-telop-icon img')?.alt || '',
    max:  n.querySelector('.max-temp')?.textContent.trim() || ''
}))
"""

# JavaScript for replacing city names
REPLACE_CITY_NAMES_JS = """
(dict) => {
  const apply = () => {
    document.querySelectorAll('.weather-forecast-name').forEach(el => {
      const jp = (el.dataset.jpName || el.textContent).trim();
      el.dataset.jpName = jp;
      const ru = dict[jp];
      if (ru && el.textContent.trim() !== ru) {
        el.textContent = ru;
      }
    });
  };
  apply();
  
  const cont = document.querySelector('.theWeatherForecastWeeklyMap_mapContainer');
  if (cont && !cont.__ruObserver) {
    const obs = new MutationObserver(() => apply());
    obs.observe(cont, {childList:true, subtree:true, characterData:true});
    cont.__ruObserver = obs;
  }
  
  const names = Array.from(document.querySelectorAll('.weather-forecast-name')).map(e=>e.textContent.trim());
  return names;
}
"""

# CSS styles for the weather map
WEATHER_MAP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap');
.weather-forecast-name{
  font-family: 'Inter', 'Roboto', 'Arial', sans-serif !important;
  font-weight: 600 !important;
  letter-spacing: 0 !important;
  text-shadow: 0 0 2px #fff;
}
.weather-forecast-name{
  font-size: 12px !important;
  line-height: 1.1 !important;
}
"""


class BrowserScraper:
    """
    Browser scraper for NHK weather website.
    
    Handles browser automation, data extraction, and screenshot capture.
    """
    
    def __init__(self) -> None:
        """Initialize the browser scraper."""
        self._url: str = config.nhk_url
        self._map_selector: str = config.nhk_map_selector
        self._cyrillic_re = re.compile(r"[А-ЯЁа-яё]")
    
    async def scrape_weather_data(self, page: Any) -> List[Dict[str, str]]:
        """
        Scrape weather data from the page.
        
        :param page: Browser page object.
        :return: List of dictionaries with weather data.
        """
        return await page.evaluate(WEATHER_SCRAPE_JS)
    
    async def replace_city_names(self, page: Any, mapping: Dict[str, str]) -> bool:
        """
        Replace Japanese city names with Russian translations in the DOM.
        
        :param page: Browser page object.
        :param mapping: Dictionary mapping Japanese names to Russian translations.
        :return: True if at least one Cyrillic name is present.
        """
        names = await page.evaluate(REPLACE_CITY_NAMES_JS, mapping)
        ok = any(self._cyrillic_re.search(n) for n in names)
        
        if not ok:
            for i in range(3):
                await asyncio.sleep(0.3)
                names = await page.evaluate(
                    "() => Array.from(document.querySelectorAll('.weather-forecast-name')).map(e=>e.textContent.trim())"
                )
                if any(self._cyrillic_re.search(n) for n in names):
                    ok = True
                    break
        
        return ok
    
    async def apply_styles(self, page: Any) -> None:
        """
        Apply custom CSS styles to the page.
        
        :param page: Browser page object.
        """
        await page.add_style_tag(content=WEATHER_MAP_CSS)
    
    async def capture_screenshot(self, page: Any) -> bytes:
        """
        Capture a screenshot of the weather map.
        
        :param page: Browser page object.
        :return: Screenshot as bytes.
        """
        screenshot_bytes = await page.locator(self._map_selector).screenshot()
        logger.info("Screenshot captured successfully")
        return screenshot_bytes
    
    async def process(self, translate_func: Any) -> Tuple[List[CityWeather], bytes]:
        """
        Process the NHK weather page.
        
        :param translate_func: Function to translate Japanese to Russian.
        :return: Tuple of (weather data list, screenshot bytes).
        """
        logger.info("Opening browser")
        async with async_playwright() as playwright:
            browser = await playwright.firefox.launch(headless=True)
            context = await browser.new_context(
                viewport=ViewportSize(width=1600, height=1200)
            )
            page = await context.new_page()
            
            await page.goto(self._url)
            await page.wait_for_selector(self._map_selector, timeout=30_000)
            
            await asyncio.sleep(10)
            
            raw_data = await self.scrape_weather_data(page)
            logger.info(f"Found {len(raw_data)} weather tiles")
            if not raw_data:
                raise RuntimeError('No weather tiles found')
            
            jp_names = [r["name"] for r in raw_data if r["name"]]
            mapping = await translate_func(jp_names)
            logger.debug(f"Translation mapping: {mapping}")
            
            logger.info("Replacing names in DOM...")
            dom_ok = await self.replace_city_names(page, mapping)
            logger.info(f"DOM Cyrillic status: {dom_ok}")
            
            await self.apply_styles(page)
            
            screenshot = await self.capture_screenshot(page)
            await browser.close()
        
        weather_data = [
            CityWeather(
                jp=r["name"],
                ru=mapping.get(r["name"], r["name"]),
                max_c=r["max"] if r["max"] != "-" else "",
                alt=r["alt"]
            )
            for r in raw_data if r["name"]
        ]
        
        return weather_data, screenshot


browser_scraper = BrowserScraper()