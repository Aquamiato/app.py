import pyaudio
import wave
import openai
import os
import asyncio
import edge_tts
from pygame import mixer

# API Anahtarını buraya tanımla
os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY"
openai.api_key = os.getenv("OPENAI_API_KEY")

# Ses Ayarları
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "live_input.wav"
RESPONSE_AUDIO_FILE = "response.mp3"

SYSTEM_PROMPT = (
    "Sen kullanıcının kulağındaki anlık sağduyu asistanısın. "
    "Ortamdaki konuşmaları dinle ve kullanıcıya o an nasıl davranması, "
    "nasıl konuşması gerektiği hakkında en fazla 1-2 cümlelik, çok kısa, "
    "net ve stratejik yönlendirmeler fısılda. Giriş cümleleri kurma, direkt taktiği söyle."
)

def record_audio(duration=5):
    """Kulaklık mikrofonundan 5 saniyelik bağlam sesi yakalar"""
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("🧠 Kulaklık dinlemede (Bağlam yakalanıyor)...")
    frames = []

    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def analyze_and_get_advice():
    """Sesi yazıya döker ve yapay zekadan anlık tavsiye alır"""
    print("⚡ Yapay zeka durumu analiz ediyor...")
    
    # 1. Sesi Yazıya Dök (Whisper API)
    with open(WAVE_OUTPUT_FILENAME, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    
    user_context = transcript["text"]
    print(f"🎤 Ortamda Duyulan: '{user_context}'")

    if not user_context.strip():
        return None

    # 2. LLM'den Tavsiye Al
    response = openai.ChatCompletion.create(
        model="gpt-4o", # En hızlı ve zeki model
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Ortamda şu an bu konuşuluyor/yaşanıyor: {user_context}. Ne yapmalıyım?"}
        ],
        max_tokens=60
    )
    
    advice = response.choices[0].message['content']
    print(f"🤖 Kulaklıktan Verilen Tavsiye: {advice}")
    return advice

async def text_to_speech_and_play(text):
    """Tavsiyeyi doğal bir Türkçe sesle kulaklığa okur"""
    # 'tr-TR-AhmetNeural' veya 'tr-TR-EmelNeural' çok başarılı doğal seslerdir
    communicate = edge_tts.Communicate(text, "tr-TR-AhmetNeural")
    await communicate.save(RESPONSE_AUDIO_FILE)
    
    # Sesi oynat
    mixer.init()
    mixer.music.load(RESPONSE_AUDIO_FILE)
    mixer.music.play()
    while mixer.music.get_busy():
        await asyncio.sleep(0.1)
    mixer.quit()

async def main():
    while True:
        # 1. Kulaklığı 5 saniye boyunca dinle
        record_audio(duration=5)
        
        # 2. Durumu analiz et ve strateji belirle
        advice = analyze_and_get_advice()
        
        # 3. Eğer ortamda bir konuşma/aksiyon varsa kulaklığa fısılda
        if advice:
            await text_to_speech_and_play(advice)
        
        await asyncio.sleep(1) # Kısa bir mola ve tekrar dinleme

if __name__ == "__main__":
    asyncio.run(main())
