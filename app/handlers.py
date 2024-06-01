import openai
from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.types import ContentType

router = Router()
@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(text="Привет, я твой голосовой помощник.\nЗапиши мне голосовое сообщение с вопросом, и я тут же отвечу на него")

async def transcribe_voice(file_path: str) -> str:
    response = await openai.Audio.transcribe("whisper-1", file_path)
    return response["text"]

async def get_openai_response(text: str) -> str:
    response = await openai.ChatCompletion.create(
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
    voice = await message.voice.get_file()

    file_path = f"https://api.telegram.org/file/bot%7Bsettings.telegram_api_token%7D/%7Bvoice.file_path%7D"
    text = await transcribe_voice(file_path)
    response_text = await get_openai_response(text)
    audio_url = await text_to_speech(response_text)
    await message.reply_voice(audio_url)

