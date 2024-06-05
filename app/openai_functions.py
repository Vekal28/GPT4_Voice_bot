import openai
from openai import AsyncOpenAI
from app.config import settings
from sqlalchemy.future import select
import io
import os
from app.models import *

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

message = []

async def transcribe_voice(audio_bytes: io.BytesIO, filename: str) -> str:
    audio_bytes.name = filename
    transcription = await openai_client.audio.transcriptions.create(
        model="whisper-1",
        language="ru",
        file=audio_bytes
    )
    return transcription.text

async def get_openai_response(text: str, user_id: int, user_first_name: str, user_last_name: str) -> str:
    assistant = await openai_client.beta.assistants.create(
        name= f"AI-ассистент",
        instructions="Ты AI-ассистент, помогаешье пользователю определить его ключевые ценности.",
        model="gpt-4o"
    )
    thread = await openai_client.beta.threads.create()
    async with async_session() as session:
        async with session.begin():
            # Проверка, существует ли пользователь с данным user_id
            result = await session.execute(
                select(Users).where(Users.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                # Создание нового пользователя, если он не существует
                user = Users(id=user_id, first_name=user_first_name, last_name=user_last_name, thread=thread.id)
                session.add(user)
                await session.flush()  # Обеспечивает, что пользователь будет доступен для связи
            await session.commit()
    message = await openai_client.beta.threads.messages.create(
        thread_id=user.thread,
        role="user",
        content=text
    )
    run = await openai_client.beta.threads.runs.create_and_poll(
        thread_id=user.thread,
        assistant_id=assistant.id,
    )
    if run.status == 'completed':
        messages = await openai_client.beta.threads.messages.list(
            thread_id=user.thread
        )
        messages = messages.to_dict()
        return messages['data'][0]['content'][0]['text']['value']
    else:
        print(run.status)

async def text_to_speech(text: str, output_file: str) -> bool:
    try:
        if os.path.exists(output_file):
            os.remove(output_file)
        response = await openai_client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        response.stream_to_file(output_file)
        return True
    except Exception as e:
        print(f"Ошибка text_to_speech: {e}")
        return False

async def is_valid_value(value: str) -> bool:
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": f"Проверь, является ли следующая строка корректной пользовательской ценностью (ответь True или false): '{value}'"
            }
        ]
    )
    return "true" in response.choices[0].message.content.lowercase()

async def save_value(user_id: int, value: str) -> bool:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Users).where(Users.id == user_id)
            )
            user = result.scalar_one_or_none()
            print(user.id)
            # Создание новой ценности, связанной с пользователем
            user_value = Values(user_id=user.id, value=value)
            session.add(user_value)
            await session.commit()
    return True