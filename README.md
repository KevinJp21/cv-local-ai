# CV Local AI

Plataforma local y privada para adaptar dinámicamente un currículum (CV) a cualquier oferta laboral y generar un PDF profesional optimizado para sistemas ATS, utilizando modelos de lenguaje mediante Ollama y renderizado tipográfico con ReportLab.

---

## Modelo recomendado

Para un rendimiento óptimo en velocidad y calidad de redacción, se recomienda configurar en el archivo `.env`:

```env
OLLAMA_MODEL=gemma4:31b-cloud
```

> **Nota técnica sobre este modelo:**
> Ofrece tiempos de respuesta de entre 4 y 5 segundos por currículum, comprensión precisa de directivas de arquitectura de software y capacidad operativa continua para flujos intensivos de postulación.

**Alternativas locales compatibles:**
- `qwen2.5:14b` (Excelente seguimiento de instrucciones y redacción técnica en GPU/local)
- `llama3.1:8b` (Ligero, adecuado para equipos con menor disponibilidad de VRAM)

---

## Arquitectura del proyecto

El proyecto implementa una arquitectura en capas (Clean Architecture), desacoplando la configuración, los contratos de datos, la persistencia y la lógica de negocio:

```text
cv_local_ai/
│
├── app/
│   ├── core/                  # Configuración global y variables por defecto (config.py)
│   ├── schemas/               # Contratos y validación de datos con Pydantic (cv.py)
│   ├── repositories/          # Acceso y lectura de datos fuente (profile_repository.py)
│   ├── services/              # Casos de uso y lógica de negocio
│   │   ├── prompt_service.py   # Reglas dinámicas y construcción de prompts ATS
│   │   ├── ollama_service.py   # Cliente Ollama, streaming y extractor JSON resiliente
│   │   └── cv_service.py       # Orquestador del flujo y generación de PDF
│   ├── api/                   # Capa de presentación / Endpoints FastAPI (routes.py)
│   ├── templates/             # Interfaz web con Jinja2 (index.html)
│   ├── static/                # Estilos CSS
│   ├── pdf_builder.py         # Motor de dibujo de PDF con ReportLab
│   └── main.py                # Punto de entrada de la aplicación FastAPI
│
├── data/                      # Perfil fuente del candidato (cv_base.json)
├── outputs/                   # Directorio donde se guardan los PDFs generados
├── .env                       # Variables de entorno locales
└── requirements.txt           # Dependencias del proyecto
```

---

## Inicio rápido

### 1. Requisitos
- **Python 3.11+**
- **Ollama** instalado y en ejecución en el entorno local (`http://localhost:11434`).

### 2. Instalación de dependencias

```bash
# Crear entorno virtual
python -m venv .venv

# Activar entorno (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activar entorno (Linux/macOS)
# source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración y ejecución

El repositorio incluye el archivo `.env` configurado por defecto para trabajar en entorno local. Si se requiere modificar el modelo, basta con actualizar el valor de `OLLAMA_MODEL` en `.env`:

```env
OLLAMA_MODEL=gemma4:31b-cloud
```

Iniciar el servidor de desarrollo:

```bash
uvicorn app.main:app --reload
```

Acceder a través del navegador en: **http://127.0.0.1:8000**

---

## Personalizar el perfil base

La información del candidato reside en:

`data/cv_base.json` *(Plantilla de referencia disponible en `data/cv_base.example.json`)*.

### Extracción automática a cv_base.json

Para estructurar un currículum existente sin necesidad de editar el archivo JSON manualmente, se puede utilizar el siguiente prompt en ChatGPT, Claude o cualquier modelo de preferencia:

<details>
<summary><b>Ver prompt de extracción</b></summary>

```text
Actúa como un extractor de datos profesional para perfiles tecnológicos. 
A continuación te proporciono el texto de mi currículum actual. Tu tarea es extraer y estructurar toda mi información en un único objeto JSON válido que cumpla exactamente la siguiente estructura (guárdalo como cv_base.json):

{
  "name": "Nombre y Apellidos",
  "email": "correo@ejemplo.com",
  "phone": "+57 300 000 0000",
  "portfolio": "https://tu-web.dev (o dejar en blanco si no tienes)",
  "linkedin": "https://linkedin.com/in/tu-perfil",
  "location": "Ciudad, País",
  "availability": "Remota, híbrida, presencial.",
  "education": "Título Profesional o Técnico\\nInstitución Educativa\\nAño de finalización o estado.",
  "languages": ["Español (Nativo)", "Inglés B2"],
  "target_title_frontend": "Tu título o cargo principal (ej: Desarrollador Frontend)",
  "target_title_fullstack": "Tu título fullstack (ej: Desarrollador Full Stack)",
  "summary_frontend": "Un resumen profesional de 3 a 5 líneas enfocado en tus fortalezas de desarrollo web/frontend.",
  "summary_fullstack": "Un resumen profesional de 3 a 5 líneas enfocado en tu capacidad general o fullstack.",
  "skills_frontend": {
    "Frontend": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3"],
    "Arquitectura & Calidad": ["Componentes reutilizables", "Responsive Design"],
    "Optimización": ["Core Web Vitals", "SEO técnico"],
    "Herramientas": ["Git", "Docker", "APIs REST"],
    "Metodologías": ["Scrum", "Desarrollo ágil"]
  },
  "skills": {
    "Frontend": ["React", "TypeScript", "JavaScript"],
    "Backend": ["APIs REST", "Node.js o Python o C# si aplica"],
    "Bases de datos": ["PostgreSQL", "MySQL", "SQL"],
    "DevOps & Herramientas": ["Git", "Docker", "Linux"],
    "Metodologías": ["Scrum", "Desarrollo ágil"]
  },
  "experience": [
    {
      "id": "identificador_unico_en_minusculas",
      "section": "profesional | freelance | proyectos",
      "title": "Nombre del cargo",
      "title_fullstack": "Nombre del cargo alternativo (opcional)",
      "company": "Nombre Empresa o Proyecto – Modalidad (ej: Empresa S.A.S. o Proyecto personal)",
      "dates": "Mes Año – Mes Año",
      "type": "Experiencia profesional | Experiencia freelance | Proyecto personal",
      "technologies": ["Tecnología1", "Tecnología2", "Tecnología3"],
      "bullets": [
        "Responsabilidad o logro técnico detallado destacando tecnologías y resultados.",
        "Otra responsabilidad o logro relevante."
      ],
      "bullets_fullstack": [
        "Versión alternativa con énfasis en backend/persistencia si aplica (opcional)"
      ]
    }
  ]
}

Reglas importantes:
1. No inventes tecnologías, fechas ni empresas que no aparezcan en mi texto.
2. Cada viñeta ('bullets') debe ser completa y detallada, mencionando herramientas y módulos específicos.
3. Devuelve ÚNICAMENTE el bloque JSON válido, sin introducciones ni comentarios.

AQUÍ ESTÁ EL TEXTO DE MI CV:
[Pega aquí el texto completo de tu currículum actual]
```
</details>

Una vez generado, guárdalo en `data/cv_base.json` para que el sistema procese y adapte el perfil a las ofertas laborales requeridas.

---

## Características principales

- **Alineación dinámica con ATS:** Identifica los requisitos principales de la vacante (frontend, backend, fullstack, e-commerce, APIs, bases de datos) y prioriza las tecnologías y logros con mayor afinidad.
- **Sincronización de título y archivo:** El encabezado del currículum y el nombre del archivo PDF generado adoptan automáticamente la denominación del puesto objetivo (ejemplo: `CV_TuNombre_ShopifyDeveloper.pdf` o `CV_TuNombre_AnalistaDeDesarrollo.pdf`).
- **Resiliencia de formato:** Parser capaz de sanear bloques markdown y normalizar esquemas para garantizar compatibilidad entre diversos modelos LLM.
- **Privacidad integral:** La información profesional y las descripciones de las vacantes se procesan en el entorno local sin transmitir datos a servicios externos.
