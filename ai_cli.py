import requests
import time
import getpass
from google import genai
from google.genai import types

# --- 1. FUNCIÓN DE LOGIN ---
def login_usuario():
    print("--- 🔑 Login de Administrador/Votante ---")
    email = input("Email: ")
    password = getpass.getpass("Contraseña: ")
    url_login = "http://127.0.0.1:8000/api/auth/login/"
    try:
        response = requests.post(url_login, json={"email": email, "password": password})
        if response.status_code == 200:
            print("✅ Autenticación exitosa.")
            return response.json().get('token')
        print(f"❌ Error: {response.json().get('error')}")
    except Exception as e:
        print(f"⚠️ Error de conexión: {e}")
    return None

# --- 2. HERRAMIENTAS PARA LA IA ---
def consultar_votos():
    """Consulta los votos registrados en la base de datos de Django."""
    print("\n[SISTEMA] 🔍 Consultando API de Django (GET)...")
    url = "http://127.0.0.1:8000/api/votos/"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(url, headers=headers)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def registrar_voto(candidato: str, mesa_id: str = "MESA-05", comentario: str = "Voto emitido con seguridad"):
    """Registra un nuevo voto. Usamos 'candidato' como el valor para 'candidato_id'."""
    print(f"\n[SISTEMA] 🚀 Registrando voto para {candidato} en la {mesa_id}...")
    url = "http://127.0.0.1:8000/api/votos/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"candidato_id": candidato, "mesa_id": mesa_id, "comentario": comentario}
    try:
        res = requests.post(url, json=payload, headers=headers)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def actualizar_voto(voto_id: str, candidato: str, comentario: str = "Voto editado"):
    """Actualiza un voto existente usando su ID."""
    print(f"\n[SISTEMA] 📝 Actualizando voto ID {voto_id}...")
    url = f"http://127.0.0.1:8000/api/votos/{voto_id}/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"candidato_id": candidato, "comentario": comentario}
    try:
        res = requests.put(url, json=payload, headers=headers)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def eliminar_voto(voto_id: str):
    """Elimina un voto por su ID."""
    print(f"\n[SISTEMA] 🗑️ Eliminando voto ID {voto_id}...")
    url = f"http://127.0.0.1:8000/api/votos/{voto_id}/"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.delete(url, headers=headers)
        if res.status_code == 204: return {"status": "Borrado exitoso"}
        return res.json()
    except Exception as e:
        return {"error": str(e)}

# Mapeo manual
funciones_crud = {
    "consultar_votos": consultar_votos,
    "registrar_voto": registrar_voto,
    "actualizar_voto": actualizar_voto,
    "eliminar_voto": eliminar_voto
}

# --- 3. CONFIGURACIÓN IA ---

API_KEY = "aqui_va_api_key" 
client = genai.Client(api_key=API_KEY)
modelo_id = "gemini-2.0-flash" 

# --- 4. FLUJO PRINCIPAL ---
token = login_usuario()

if token:
    print("\n🤖 IA: ¡Hola! Soy tu asistente de ADSO. ¿Qué deseas consultar hoy?")
    
    while True:
        user_input = input("\nTú: ")
        if user_input.lower() in ['salir', 'exit', 'bye']: break

        # Prompt optimizado para que la IA entienda que DEBE usar las herramientas
        prompt = (
            f"Eres un asistente de gestión de votos. \n"
            f"Si el usuario quiere ver los votos, usa 'consultar_votos'.\n"
            f"Si el usuario quiere votar, usa 'registrar_voto'.\n"
            f"Si quiere cambiar algo, usa 'actualizar_voto'.\n"
            f"Si quiere borrar algo, usa 'eliminar_voto'.\n"
            f"Pregunta: {user_input}"
        )

        try:
            # Llamada a Gemini con las herramientas
            response = client.models.generate_content(
                model=modelo_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[consultar_votos, registrar_voto, actualizar_voto, eliminar_voto]
                )
            )

            # Lógica para procesar la respuesta
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        func_name = part.function_call.name
                        args = part.function_call.args
                        
                        # Ejecutamos la función de Python
                        resultado = funciones_crud[func_name](**args)
                        
                        # Devolvemos el resultado a Gemini para la respuesta final
                        response_final = client.models.generate_content(
                            model=modelo_id,
                            contents=[
                                types.Content(role="user", parts=[types.Part.from_text(prompt)]),
                                response.candidates[0].content,
                                types.Content(role="tool", parts=[
                                    types.Part.from_function_response(
                                        name=func_name, 
                                        response={"result": resultado}
                                    )
                                ])
                            ]
                        )
                        print(f"🤖 IA: {response_final.text}")
                    elif part.text:
                        print(f"🤖 IA: {part.text}")
            else:
                print("🤖 IA: No estoy seguro de cómo ayudarte con eso.")

        except Exception as e:
            if "503" in str(e):
                print("⚠️ IA: Servidor ocupado, reintentando en breve...")
            else:
                print(f"⚠️ Ups! Algo pasó: {e}")