"""
Telegram module for sending messages and images to Telegram channels.
"""
from typing import Optional

from aiogram import Bot
from aiogram.types import BufferedInputFile
from loguru import logger

from nhk_weather.config.config import config


class TelegramClient:
    """
    Client for sending messages and images to Telegram.
    
    Uses aiogram to interact with the Telegram Bot API.
    """
    
    def __init__(self) -> None:
        """
        Initialize the Telegram client.
        
        :raises ValueError: If the bot token is not set.
        """
        self._bot_token: str = config.telegram_bot_token
        self._chat_id: str = config.telegram_chat_id
        self._bot: Optional[Bot] = None
        
        if not self._bot_token:
            raise ValueError("Telegram bot token is not set")
        
        if not self._chat_id:
            raise ValueError("Telegram chat ID is not set")
    
    async def _get_bot(self) -> Bot:
        """
        Get or create the Bot instance.
        
        :return: Aiogram Bot instance.
        """
        if self._bot is None:
            self._bot = Bot(token=self._bot_token)
        return self._bot
    
    async def send_message(self, text: str, chat_id: Optional[str] = None) -> bool:
        """
        Send a text message to a Telegram chat.
        
        :param text: Message text to send.
        :param chat_id: Chat ID to send the message to. If None, uses the default chat ID.
        :return: True if the message was sent successfully, False otherwise.
        """
        if not text:
            logger.warning("Empty message text, not sending")
            return False
        
        chat_id = chat_id or self._chat_id
        
        try:
            bot = await self._get_bot()
            await bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"Message sent to chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
    
    async def send_photo(self, 
                         photo_bytes: bytes, 
                         caption: Optional[str] = None, 
                         chat_id: Optional[str] = None) -> bool:
        """
        Send a photo to a Telegram chat.
        
        :param photo_bytes: Photo bytes to send.
        :param caption: Optional caption for the photo.
        :param chat_id: Chat ID to send the photo to. If None, uses the default chat ID.
        :return: True if the photo was sent successfully, False otherwise.
        """
        if not photo_bytes:
            logger.warning("Empty photo bytes, not sending")
            return False
        
        chat_id = chat_id or self._chat_id
        
        try:
            bot = await self._get_bot()
            input_file = BufferedInputFile(photo_bytes, filename="weather_map.png")
            await bot.send_photo(chat_id=chat_id, photo=input_file, caption=caption)
            logger.info(f"Photo sent to chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send photo: {str(e)}")
            return False
    
    async def send_weather_report(self, summary: str, photo_bytes: bytes) -> bool:
        """
        Send a complete weather report with text and image.
        
        :param summary: Weather summary text.
        :param photo_bytes: Weather map screenshot bytes.
        :return: True if both the message and photo were sent successfully, False otherwise.
        """
        try:
            result = await self.send_photo(photo_bytes=photo_bytes, caption=summary)
            
            if not result and summary:
                logger.info("Caption might be too long, sending as separate message")
                await self.send_photo(photo_bytes=photo_bytes)
                await self.send_message(text=summary)
                result = True
            
            return result
        except Exception as e:
            logger.error(f"Failed to send weather report: {str(e)}")
            return False
    
    async def close(self) -> None:
        """
        Close the bot session.
        """
        if self._bot:
            await self._bot.session.close()
            self._bot = None


telegram_client = TelegramClient()