import asyncio
from telegram import Bot

class NotificationsBot:
    def __init__(self, bot_token=':', chat_id=-, chat_id_debug=-) -> None:
        # self.bot_token = bot_token
        self.bot_token = bot_token
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.chat_id_debug = chat_id_debug

    async def sendMessageDebug(self, message_text):
        try:
            # если при каждом вызове не создавать новый экземпляр бота, то сообщения перестают отправляться. 
            # поэтому на данном этапе после отправки сообщения буду закрывать соединение с текущим ботом, чтобы не создавалось много экземпляров,
            # а потом создам отдельный сервис для уведомлений или попробую решить проблему тем, чтобы не передавать бота во все классы, а использовать его только в основном
            bot = Bot(token='6354808644:')
            await bot.send_message(chat_id=-, text=)
            await bot.close()
        except Exception as e:
            print('Сообщение в дебаг чат не отправлено', e)

    async def sendMessage(self, message_text):
        try:
            bot = Bot(token='6354808644:')
            await bot.send_message(chat_id=-, text=message_text)
            await bot.close()
        except Exception as e:
            print('Сообщение в дебаг чат не отправлено', e)

    # async def sendMessageDebug(self, message_text):
    #         try:
    #             await self.bot.send_message(chat_id=self.chat_id_debug, text=message_text)
    #         except Exception as e:
    #             print('Сообщение в дебаг чат не отправлено', e)