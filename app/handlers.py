import openai
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, Voice
from app.config import settings
import aiohttp

# Инициализация роутера
router = Router()

# Установка API ключа для OpenAI
openai.api_key = settings.openai_api_key


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(text="Привет, я твой голосовой помощник.\nЗапиши мне голосовое сообщение с вопросом, и я тут же отвечу на него")


async def transcribe_voice(file_path: str) -> str:
    audio_file = open(file_path, "rb")
    response = openai.Audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return response["text"]


async def get_openai_response(text: str) -> str:
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": text
            }
        ]
    )
    return response.choices[0].message['content']


async def text_to_speech(text: str) -> str:
    response = await openai.Audio.create(
        text=text,
        voice="text-to-speech-voice",
        model="text-to-speech"
    )
    return response["url"]


@router.message()
async def handle_voice_message(message: Message):
    voice = message.voice
    file_info = await message.bot.get_file(voice.file_id)
    file_path = file_info.file_path
    file_url = f"https://api.telegram.org/file/bot{settings.tg_api_token}/{file_path}"
    print(file_url)

    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                with open("voice.ogg", "wb") as f:
                    f.write(await resp.read())

    text = await transcribe_voice("voice.ogg")
    response_text = await get_openai_response(text)
    audio_url = await text_to_speech(response_text)
    await message.answer_voice(audio_url)