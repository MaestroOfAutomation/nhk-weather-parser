"""
NHK Japan Weather Parser

Entry point script for the application.
"""
import asyncio
import sys

from loguru import logger

from nhk_weather.core.models import CityWeather
from nhk_weather.services.ai import deepseek_client
from nhk_weather.services.browser import browser_scraper
from nhk_weather.services.telegram import telegram_client


class WeatherReporter:
    """
    Main class for orchestrating the weather reporting workflow.
    
    Coordinates browser scraping, AI summary generation, and Telegram posting.
    """
    
    def __init__(self) -> None:
        """Initialize the weather reporter."""
        self._ai_client = deepseek_client
        self._browser = browser_scraper
        self._telegram = telegram_client
    
    async def _categorize_weather(self, alt: str) -> str:
        """
        Categorize weather condition based on alt text.
        
        :param alt: Weather condition alt text.
        :return: Categorized weather condition.
        """
        if "雷" in alt:
            return "гроза"
        if "雪" in alt:
            return "снег"
        if "晴れ時々くもり" in alt:
            return "солнечно, временами облачно"
        if "くもり時々雨" in alt:
            return "облачно, временами дождь"
        if "雨時々やむ" in alt:
            return "дождь с прояснениями"
        if "雨" in alt:
            return "дождь"
        if "晴" in alt:
            return "солнечно"
        if "くも" in alt or "曇" in alt:
            return "облачно"
        return alt

    async def _prepare_weather_data(self, weather_data: list[CityWeather]) -> list[dict[str, str]]:
        """
        Prepare weather data for summary generation.
        
        :param weather_data: List of CityWeather objects.
        :return: List of dictionaries with processed weather data.
        """
        return [
            {
                "jp": record.jp,
                "ru": record.ru,
                "max_c": record.max_c,
                "alt": record.alt,
                "condition": await self._categorize_weather(record.alt)
            }
            for record in weather_data
        ]
    
    async def run(self) -> bool:
        """
        Run the complete weather reporting workflow.
        
        :return: True if successful, False otherwise.
        """
        try:
            weather_data, screenshot = await self._browser.process(
                self._ai_client.translate
            )
            
            if not weather_data:
                logger.error("No weather data found")
                return False
            
            processed_data = await self._prepare_weather_data(weather_data)

            initial_summary = await self._ai_client.build_weather_summary(processed_data)
            logger.info(f"Generated initial summary: {initial_summary}")
            
            summary = await self._ai_client.rephrase_weather_summary(initial_summary)
            logger.success(f"Rephrased summary: {summary}")
            
            result = await self._telegram.send_weather_report(summary, screenshot)
            
            return result
        except Exception as e:
            logger.exception(f"Error in weather reporting workflow: {e}")
            return False
        finally:
            await self._telegram.close()


async def main() -> None:
    """
    Main entry point for the application.
    """
    reporter = WeatherReporter()
    success = await reporter.run()
    
    if success:
        logger.success("Weather report successfully sent to Telegram")
    else:
        logger.error("Failed to send weather report")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())