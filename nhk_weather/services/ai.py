"""
AI module for interacting with DeepSeek API.
"""
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, TypedDict

import aiohttp
from loguru import logger

from nhk_weather.config.config import config

TRANSLATE_SYSTEM_PROMPT = (
    "Верни ТОЛЬКО валидный JSON {jp: ru}. "
    "ru — это русское название города (кириллица). "
    "Если нет общепринятого названия — транслитерируй на русский по звучанию. "
    "НЕ оставляй японские иероглифы в значениях."
)

WEATHER_SUMMARY_SYSTEM_PROMPT_TEMPLATE = (
    "Ты — лаконичный русскоязычный метео-редактор. "
    "Сегодняшняя дата: {date}. "
    "Используй ТОЛЬКО факты из переданного JSON. Ничего не выдумывай: никаких температур, городов или явлений, которых нет в данных. "
    "Сделай 1–2 предложения.\n\n"
    "Обязательно:\n"
    "• КРИТИЧЕСКИ ВАЖНО: ВСЕГДА указывай температуру в градусах Цельсия (например, +37°C) для упоминаемых городов. Поле max_c содержит эту информацию.\n"
    "• Упомяни текущую дату в контексте прогноза погоды.\n"
    "• Упомяни погоду в Токио, если он есть в списке.\n"
    "• Упомяни один южный город из списка и Саппоро (определи по общеизвестной географии названий).\n"
    "• Отметь заметные явления (дождь, гроза, снег и т.п.), если они есть.\n"
    "• Не перечисляй все города подряд, только ключевые.\n"
    "• Добавляй уместные эмодзи (например, 🌧️ для дождя, ☀️ для солнца, 🌩️ для грозы), но не перебарщивай (1-2 эмодзи на весь текст).\n"
    "• Используй тире (—) для выделения важных частей сообщения.\n"
    "• Каждый раз формулируй прогноз по-разному, избегай шаблонных фраз.\n"
    "• Если температура не указана, то не пиши ничего про температуру.\n"
    "Пример формата: \"Сегодня по всей Японии — жара: в Токио и Осаке до +37°C, душно и солнечно. 🌧️ В Саппоро — грозы и дожди, на юге местами возможны кратковременные осадки.\"\n"
    "Формат ответа: чистый текст, без списков и кавычек."
)

WEATHER_SUMMARY_USER_PROMPT = "Данные по городам (макс. температура в °C и описание погоды в alt):\n"

WEATHER_REPHRASE_SYSTEM_PROMPT = (
    "Ты — опытный русскоязычный редактор метеосводок. "
    "Перефразируй предоставленный текст прогноза погоды, чтобы он звучал более естественно и профессионально на русском языке. "
    "ВАЖНО: Используй МАКСИМУМ 2 ПРЕДЛОЖЕНИЯ для всего прогноза. "
    "Сохрани все ключевые фактические данные (города, температуры, погодные условия, эмодзи), но сделай текст лаконичным. "
    "Используй более разнообразные и точные выражения для описания погодных явлений. "
    "Пример хорошего стиля (2 предложения): \"28 июля в Токио — солнечно ☀️, а на юге в Нахе — облачно с переходом в дождь 🌧️. В Саппоро — переменная облачность с кратковременными дождями.\""
)

CITY_TRANSLATIONS: Dict[str, str] = {
    "東京": "Токио",
    "長野": "Нагано",
    "新潟": "Ниигата",
    "小笠原": "Огасавара",
    "大阪": "Осака",
    "名古屋": "Нагоя",
    "金沢": "Канадзава",
    "広島": "Хиросима",
    "松江": "Мацуэ",
    "福岡": "Фукуока",
    "鹿児島": "Кагосима",
    "那覇": "Наха",
    "仙台": "Сэндай",
    "秋田": "Акита",
    "札幌": "Саппоро",
    "釧路": "Кусиро",
    "高知": "Коти",
}


class MessageDict(TypedDict):
    """Type definition for a message in the DeepSeek API."""
    role: str
    content: str


class WeatherRecord(TypedDict):
    """Type definition for a weather record."""
    jp: str
    ru: str
    max_c: str
    alt: str
    condition: str


class DeepSeekClient:
    """
    Client for interacting with DeepSeek API.
    
    Handles API requests and response processing for text generation.
    """

    def __init__(self) -> None:
        """Initialize the DeepSeek client."""
        self._api_key: str = config.deepseek_api_key
        self._api_url: str = config.deepseek_api_url
        self._model: str = config.deepseek_model
        self._cyrillic_re = re.compile(r"[А-ЯЁа-яё]")

    async def chat(self, messages: List[MessageDict], temperature: float = 0.2) -> str:
        """
        Send a chat request to DeepSeek API.
        
        :param messages: List of message objects with role and content.
        :param temperature: Temperature parameter for text generation.
        :return: Generated text response.
        :raises ValueError: If the API key is not set.
        :raises RuntimeError: If the API request fails.
        """
        if not self._api_key:
            raise ValueError("DeepSeek API key is not set")

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                        self._api_url,
                        headers=headers,
                        json=payload,
                        timeout=60
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise RuntimeError(f"DeepSeek API error: {response.status} - {error_text}")

                    data = await response.json()
                    return data["choices"][0]["message"]["content"].strip()
            except aiohttp.ClientError as e:
                raise RuntimeError(f"DeepSeek API request failed: {str(e)}")

    async def translate(self, jp_terms: List[str], max_retries: int = 2) -> Dict[str, str]:
        """
        Translate Japanese terms to Russian using DeepSeek.
        
        :param jp_terms: List of Japanese terms to translate.
        :param max_retries: Maximum number of retry attempts.
        :return: Dictionary mapping Japanese terms to Russian translations.
        """
        to_do = [t for t in jp_terms if t and t not in CITY_TRANSLATIONS]
        if not to_do:
            return {t: CITY_TRANSLATIONS.get(t, t) for t in jp_terms}

        attempt = 0
        missing = to_do[:]
        result: Dict[str, str] = {}

        while missing and attempt <= max_retries:
            attempt += 1
            logger.info(f"DeepSeek translate attempt {attempt}, {len(missing)} terms")

            system: MessageDict = {
                "role": "system",
                "content": TRANSLATE_SYSTEM_PROMPT
            }
            user: MessageDict = {"role": "user", "content": json.dumps(missing, ensure_ascii=False)}

            resp = await self.chat([system, user], temperature=0.0)

            start, end = resp.find("{"), resp.rfind("}")
            if start >= 0 and end > start:
                try:
                    data = json.loads(resp[start:end + 1])

                    good, bad = {}, []
                    for jp, ru in data.items():
                        if ru and self._cyrillic_re.search(ru):
                            good[jp] = ru.strip()
                        else:
                            bad.append(jp)

                    result.update(good)
                    missing = bad
                    logger.debug(f"good={len(good)}, bad={len(bad)}")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON from response: {resp}")
            else:
                logger.error(f"No JSON found in response: {resp}")

        CITY_TRANSLATIONS.update(result)

        for jp in missing:
            result[jp] = jp

        return {t: CITY_TRANSLATIONS.get(t, t) for t in jp_terms}

    async def build_weather_summary(self, records: List[WeatherRecord]) -> str:
        """
        Generate a weather summary based on the provided records.
        
        :param records: List of weather records with city and condition information.
        :return: Generated weather summary text.
        """
        payload = [
            {
                "city_ru": r["ru"],
                "city_jp": r["jp"],
                "max_c": r["max_c"],
                "condition_alt": r["alt"]
            }
            for r in records
        ]
        
        # Debug log to check temperature data
        logger.debug(f"Weather payload for AI: {json.dumps(payload, ensure_ascii=False)}")

        # Use UTC+9 timezone (Japan Standard Time)
        jst = timezone(timedelta(hours=9))
        current_date = datetime.now(jst).strftime("%Y-%m-%d")

        system: MessageDict = {
            "role": "system",
            "content": WEATHER_SUMMARY_SYSTEM_PROMPT_TEMPLATE.format(date=current_date)
        }

        user: MessageDict = {
            "role": "user",
            "content": WEATHER_SUMMARY_USER_PROMPT + json.dumps(payload, ensure_ascii=False, indent=2)
        }

        return await self.chat([system, user], temperature=0.7)

    async def rephrase_weather_summary(self, summary: str) -> str:
        """
        Rephrase a weather summary to make it sound more natural in Russian.
        
        :param summary: Original weather summary text.
        :return: Rephrased weather summary text.
        """
        if not summary:
            logger.warning("Empty summary text, not rephrasing")
            return summary
            
        logger.info("Rephrasing weather summary")
        
        system: MessageDict = {
            "role": "system",
            "content": WEATHER_REPHRASE_SYSTEM_PROMPT
        }
        
        user: MessageDict = {
            "role": "user",
            "content": summary
        }
        
        rephrased = await self.chat([system, user], temperature=0.5)
        logger.info("Summary rephrased successfully")
        
        return rephrased


deepseek_client = DeepSeekClient()
