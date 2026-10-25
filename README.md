# CV Local AI — prototipo inicial

Aplicación web local para adaptar un CV a una oferta y generar un PDF usando Ollama.

## Requisitos
- Python 3.11 o superior
- Ollama instalado y ejecutándose
- Modelo local descargado

## 1. Descargar un modelo
En una terminal:
```bash
ollama pull qwen3:8b
```
Si el modelo resulta lento o consume demasiada memoria:
```bash
ollama pull qwen3:4b
```

## 2. Preparar el proyecto
Windows PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Ejecutar
Desde la raíz del proyecto:
```bash
uvicorn app.main:app --reload
```
Abre http://127.0.0.1:8000

Para cambiar el modelo, define la variable `OLLAMA_MODEL` antes de iniciar el servidor.
PowerShell:
```powershell
$env:OLLAMA_MODEL="qwen3:4b"
uvicorn app.main:app --reload
```

## 4. Personalizar tu perfil
Edita `data/cv_base.json`. Mantén los datos verificables, las fechas reales y la distinción entre empleo profesional, freelance y proyecto personal.

## Límites conocidos de esta versión
- Es un prototipo: el modelo puede redactar alguna viñeta de forma imprecisa. Revisa el PDF antes de usarlo.
- El esquema restringe el formato de salida, pero no garantiza por sí solo que cada frase sea verdadera.
- El generador usa una plantilla de PDF de una columna y texto seleccionable para favorecer la lectura ATS.
- Los PDF generados quedan en `outputs/`.
- La aplicación no se debe exponer a internet; úsala en `localhost`.
- La versión inicial no extrae ofertas desde enlaces web, no envía postulaciones y no mantiene una base de datos de solicitudes.
