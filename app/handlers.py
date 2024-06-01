import openai
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from app.config import settings
import aiohttp
import os
import asyncio
from aiogram.types import FSInputFile

router = Router()

openai.api_key = settings.openai_api_key

async def transcribe_voice(file_path: str) -> str:
    with open(file_path, 'rb') as audio_file:
        transcription = openai.audio.transcriptions.create(model="whisper-1", language="ru", file=audio_file)
    return transcription.text

async def get_openai_response(text: str) -> str:
    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": text
            }
        ]
    )
    return completion.choices[0].message.content

async def text_to_speech(text: str, output_file: str) -> bool:
    response = openai.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    response.stream_to_file(output_file)
    return True

async def typing_dots_effect(message: Message, text: str, duration: int):
    for _ in range(3):
        for i in range(duration):
            await message.edit_text(f"{text}{'.' * ((i % 4))}")
            await asyncio.sleep(0.2)

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(text="Привет, я твой голосовой помощник.\nЗапиши мне голосовое сообщение с вопросом, и я тут же отвечу на него")

@router.message()
async def handle_voice_message(message: Message):
    if message.voice:
        sent_message = await message.answer("Сoздание ответа")
        typing_task = asyncio.create_task(typing_dots_effect(sent_message, "Создание ответа", duration=4))
        input_file = f"audio/{message.chat.id}.ogg"
        output_file = f"audio/r{message.chat.id}.ogg"
        voice = message.voice
        file_info = await message.bot.get_file(voice.file_id)
        file_path = file_info.file_path
        file_url = f"https://api.telegram.org/file/bot{settings.tg_api_token}/{file_path}"

        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status == 200:
                    with open(input_file, "wb") as f:
                        f.write(await resp.read())
        text = await transcribe_voice(input_file)
        # print(f"User: {text}")
        response_text = await get_openai_response(text)
        # print(f"GPT: {response_text}")
        res = False
        res = await text_to_speech(response_text, output_file)
        await typing_task
        if (res):
            audio = FSInputFile(output_file)
            await sent_message.edit_text(text="Ответ готов")
            await message.bot.send_voice(chat_id=message.chat.id, voice=audio)
        else:
            await sent_message.edit_text(text="К сожалению не могу ответить на ваш вопрос.\nЗадайте другой вопрос")
        os.remove(input_file)
        os.remove(output_file)
    else:
        await message.answer(text="Отправьте мне голосовое сообщение")
