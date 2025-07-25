#Importantes para que funcione el Text-to-speech de google
import os
from google.cloud import texttospeech
#Importantes para que funcione la API de chatgpt
from openai import OpenAI
from dotenv import load_dotenv
#Importantes para modificar el audio y que se escuche mas robotico
from pydub import AudioSegment
from pydub.playback import play
#importante para hacer los nombres random
import uuid
import random
#Utilizado para reproducir los audios
import pygame
import time

pygame.mixer.init() #Inicializa el pygame para la reproduccion de los audios

# Es como la APi key del Text-to-speech de google
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-credentials.json"
client_tts = texttospeech.TextToSpeechClient()

# Inicializa clientes
load_dotenv()   #Accede a las instrucciones de R2-D2
openai_api_key = os.getenv("OPENAI_API_KEY")
client_openai = OpenAI(api_key=openai_api_key)

# Carga instrucciones personalizadas para R2-D2
with open("Instrucciones.txt", "r", encoding="utf-8") as f:
    instrucciones = f.read()

# === FUNCIONES DE EFECTOS DE AUDIO ===

def cambiar_velocidad(audio, velocidad=1.0):
    return audio.speedup(playback_speed=velocidad)

def cambiar_pitch(audio, semitonos=0):
    factor = 2 ** (semitonos / 12)
    return audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * factor)
    }).set_frame_rate(audio.frame_rate)

def agregar_eco(audio, retraso_ms=120, atenuacion_db=6):
    eco = audio - atenuacion_db
    eco = eco.fade_in(30).fade_out(30)
    return audio.overlay(eco, position=retraso_ms)

def distorsionar(audio, ganancia=10):
    audio = audio.apply_gain(ganancia)
    return audio.normalize()

#Esto es lo que debes modificar si quieres cambiar algo sobre la voz ¡No tocar las de arriba!
def aplicar_efectos(audio):
    audio = cambiar_velocidad(audio, velocidad=1.1)
    audio = cambiar_pitch(audio, semitonos=3)   #Entre mas grande mas agudo, entre mas negativo mas grabe
    audio = agregar_eco(audio, retraso_ms=50, atenuacion_db=2)  #Que tanto eco y quetanto se escucha
    audio = distorsionar(audio, ganancia=5) #que tan distorcionado se escucha
    return audio

# === FUNCIONES PRINCIPALES ===

def obtener_respuesta_gpt(prompt):
    response = client_openai.responses.create(
        model="gpt-4o", #Se puede cambiar pero es la mejor que encontre
        tools=[{"type": "web_search_preview"}], # Para permitirle buscar en la red
        instructions=instrucciones, #Le da las instrucciones para su correcto funcionamiento
        input=prompt,
    )
    return response.output_text

def texto_a_voz_google(texto, archivo_salida):
    synthesis_input = texttospeech.SynthesisInput(text=texto)   #Le llega lo que dira, que en este caso es la respuesta de chat

    voice = texttospeech.VoiceSelectionParams(
        language_code="es-ES",  #Pone el idioma en español
        name="es-US-Standard-B",    # Puedes cambiar la voz si quieres
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )
    response = client_tts.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    with open(archivo_salida, "wb") as out:
        out.write(response.audio_content)
    return archivo_salida

#Entra a la carpeta de sonidos y elije un archivo aleatorio (hay que tener cuidado porque algunso sonidos no son de R2-D2)
def obtener_nombre_sonido():
    carpeta = "R2 Sounds and music"
    sonidos = [f for f in os.listdir(carpeta) if f.endswith(".mp3")]
    if not sonidos:
        raise FileNotFoundError("No se encontraron archivos .mp3 en la carpeta.")
    return os.path.join(carpeta, random.choice(sonidos))

#Divide la instruccion e incorpora los sonidos en medio
def reproducir_voz_r2d2_con_pitidos(texto):
    # Divide el texto por "/"
    fragmentos = [fr.strip() for fr in texto.split("/") if fr.strip()]

    audios_modificados = []

    for i, fragmento in enumerate(fragmentos):
        # Paso 1: Generar audio con voz de Google TTS
        archivo_temp = f"temp_{uuid.uuid4()}.wav"
        texto_a_voz_google(fragmento, archivo_temp)

        # Paso 2: Leer el archivo generado
        audio = AudioSegment.from_wav(archivo_temp)

        # Paso 3: Aplicar efectos (pitido, filtros, etc.)
        audio_modificado = aplicar_efectos(audio)
        audios_modificados.append(audio_modificado)

        # Paso 4: Agregar sonido R2-D2 solo entre fragmentos
        if i < len(fragmentos) - 1:
            sonido_r2d2 = AudioSegment.from_file(obtener_nombre_sonido())
            audios_modificados.append(sonido_r2d2)

        # Limpieza
        os.remove(archivo_temp)

    # Concatenar todos los audios en uno solo
    audio_final = sum(audios_modificados)
    archivo_final = f"voz_final_r2d2_{uuid.uuid4()}.wav"
    audio_final.export(archivo_final, format="wav")

     # Reproducir con pygame
    pygame.mixer.music.load(archivo_final)
    pygame.mixer.music.play()

    # Esperar a que termine
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

# === MAIN ===

def main():
    print("Habla con R2-D2 (escribe 'salir' para terminar)")
    while True:
        try:
            entrada = input("Tú: ")
            if entrada.lower() in ["salir", "exit", "quit"]:
                print("Adiós!")
                break

            respuesta = obtener_respuesta_gpt(entrada)
            print("R2-D2:", respuesta)

            reproducir_voz_r2d2_con_pitidos(respuesta)
        except Exception as e:
            print(f"¡Ups! Algo falló en el sistema galáctico: {e}")


if __name__ == "__main__":
    main()

