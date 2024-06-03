from openai import AsyncOpenAI
from app.config import settings
import io
import os

openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

async def transcribe_voice(audio_bytes: io.BytesIO, filename: str) -> str:
    audio_bytes.name = filename
    transcription = await openai_client.audio.transcriptions.create(
        model="whisper-1",
        language="ru",
        file=audio_bytes
    )
    return transcription.text

async def get_openai_response(text: str) -> str:
    assistant = await openai_client.beta.assistants.create(
        name="GPT4 Voice",
        model="gpt-4o"
    )
    thread = await openai_client.beta.threads.create()
    message = await openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=text
    )
    run = await openai_client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    if run.status == 'completed':
        messages = await openai_client.beta.threads.messages.list(
            thread_id=thread.id
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