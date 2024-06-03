from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import FSInputFile
from app.openai_functions import *

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        text="Привет, я твой голосовой помощник.\nЗапиши мне голосовое сообщение с вопросом, и я тут же отвечу на него")


@router.message()
async def handle_voice_message(message: Message):
    if message.voice:
        sent_message = await message.answer("Создание ответа")

        audio_bytes: io.BytesIO = await message.bot.download(message.voice)

        text = await transcribe_voice(audio_bytes, filename="audio.ogg")
        #print(f"User: {text}")
        response_text = await get_openai_response(text)
        #print(f"Chat: {response_text}")

        audio_file = f"audio/{message.chat.id}.ogg"

        if await text_to_speech(response_text, audio_file):
            audio = FSInputFile(audio_file)
            await sent_message.edit_text(text="Ответ готов")
            await message.bot.send_voice(chat_id=message.chat.id, voice=audio)
        else:
            await sent_message.edit_text(text="К сожалению не могу ответить на ваш вопрос.\nЗадайте другой вопрос")

        os.remove(audio_file)
    else:
        await message.answer(text="Отправьте мне голосовое сообщение")