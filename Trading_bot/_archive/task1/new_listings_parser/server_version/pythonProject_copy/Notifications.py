import asyncio
from telegram import Bot

token = '6354808644:AAEA9pvVZj6YqvXKCyyyF9ay0q4mdXqXfxE'
# chatId = -1001995965101  # мой тестовый чат
chatId = -1002096660763 # наш основной чат


# TODO. Общий комментарий по всем файлам. Лучше для каждой отельной структуры (парсер, бот для уведолмений и тд)
# писать свой класс, будем более читабельно и легче будет прописывать взаимодействие между ними.
async def send_telegram_message(message_text):
    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=chatId, text=message_text)
    except Exception as e:
        print('Сообщение не отправлено', e)

async def send_telegram_message_debug(message_text):
    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=-1001995965101, text=message_text)
    except Exception as e:
        print('Сообщение не отправлено', e)


if __name__ == '__main__':
    asyncio.run(send_telegram_message('тестовое сообщение'))
