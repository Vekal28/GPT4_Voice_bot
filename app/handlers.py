from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import FSInputFile
from app.openai_functions import *


router = Router()

user_context = {}

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        text="Привет, я твой голосовой помощник.\nЗапиши мне голосовое сообщение с вопросом, и я тут же отвечу на него.\nТакже я могу помочь определить ваши ключевые ценности.")

@router.message()
async def handle_voice_message(message: Message):
    m = 10
    if not message.voice:
        sent_message = await message.answer("Создание ответа")

        audio_bytes: io.BytesIO = await message.bot.download(message.voice)

        text = await transcribe_voice(audio_bytes, filename="audio.ogg")
        text = message.text
        assistant_message = await get_openai_response(text, message.from_user.id, message.from_user.first_name, message.from_user.last_name)
        print(assistant_message)
        await message.answer(assistant_message)
        if await is_valid_value(text):
            await save_value(message.from_user.id, text)
            await sent_message.edit_text(f"Ценность '{text}' успешно сохранена.")
        else:
            await message.answer(get_openai_response("Ценоомть не прошла валидаю, помоги её опрделить. Продолжи диалог"), message.from_user.id, message.from_user.first_name, message.from_user.last_name)
    else:
        await message.answer(text=f"Отправьте голосовое сообщение")
