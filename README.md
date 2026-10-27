# CV Local AI

Plataforma local-first y privada para adaptar dinámicamente un currículum (CV) a **ofertas laborales del área de TI** y generar un PDF profesional optimizado para sistemas ATS, utilizando modelos de lenguaje mediante Ollama (local o cloud) y renderizado tipográfico con ReportLab. Actualmente está enfocada en perfiles tecnológicos; todavía no cubre ofertas de otras industrias ni un uso global.

---

## Modelo recomendado

Para un rendimiento óptimo en velocidad y calidad de redacción, se recomienda configurar en el archivo `.env`:

```env
OLLAMA_MODEL=gemma4:31b-cloud
```

> **Nota técnica sobre este modelo:**
> Ofrece tiempos de respuesta de entre 4 y 5 segundos por currículum, comprensión precisa de directivas de arquitectura de software y capacidad operativa continua para flujos intensivos de postulación.
>
> El sufijo `-cloud` está pensado para ejecutarse a través de un **Ollama local**. Si vas a consumir directamente la API de Ollama Cloud, usa el nombre del modelo **sin** `-cloud` y configura `OLLAMA_BASE_URL=https://ollama.com`.

**Alternativas locales compatibles:**

- `qwen2.5:14b` (Excelente seguimiento de instrucciones y redacción técnica en GPU/local)
- `llama3.1:8b` (Ligero, adecuado para equipos con menor disponibilidad de VRAM)

---



## Configuración de Ollama: local o cloud

El archivo `.env` controla la conexión con Ollama:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:31b-cloud
OLLAMA_API_KEY=
OLLAMA_TEMPERATURE=0.4
OLLAMA_NUM_CTX=12000
```



### Opción A · Ollama local (por defecto)

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:31b-cloud
OLLAMA_API_KEY=
OLLAMA_TEMPERATURE=0.4
OLLAMA_NUM_CTX=12000
```

- Requiere tener Ollama instalado y ejecutándose en tu equipo.
- `OLLAMA_API_KEY` se deja vacío.
- El sufijo `-cloud` **solo funciona en local**: le indica al servidor local de Ollama que ejecute el modelo en la nube utilizando la sesión de Ollama.



### Opción B · Ollama Cloud / API directa

```env
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_MODEL=gemma4:31b
OLLAMA_API_KEY=tu_api_key_de_ollama
OLLAMA_TEMPERATURE=0.4
OLLAMA_NUM_CTX=12000
```

- Solo debes agregar tu API key en `OLLAMA_API_KEY` dentro de `.env`.
- Configura el modelo **sin** el sufijo `-cloud` (`gemma4:31b`, no `gemma4:31b-cloud`).
- Apunta `OLLAMA_BASE_URL` a `https://ollama.com`.
- El endpoint directo de Ollama Cloud **no reconoce** el sufijo `-cloud`; ese sufijo únicamente es válido cuando se usa el Ollama local.
- `OLLAMA_API_KEY` es opcional: si está vacío, la aplicación funciona en modo local sin autenticación.

> Después de cambiar cualquier valor en `.env`, reinicia el servidor de uvicorn para que se apliquen los nuevos parámetros.

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
├── data/                      # Perfil fuente (cv_base.json) y plantilla (cv_base.example.json)
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

> Para usar Ollama Cloud o la API directa, revisa la sección [Configuración de Ollama: local o cloud](#configuración-de-ollama-local-o-cloud).

Iniciar el servidor de desarrollo:

```bash
uvicorn app.main:app --reload
```

Acceder a través del navegador en: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---



## Personalizar el perfil base

La información del candidato reside en `data/cv_base.json`.

La plantilla de referencia con datos ficticios está en `data/cv_base.example.json`. Cópiala, reemplaza los valores y guárdala como `data/cv_base.json`.

### Extracción automática a cv_base.json

Para estructurar un currículum existente sin necesidad de editar el archivo JSON manualmente, se puede utilizar el siguiente prompt en ChatGPT, Claude o cualquier modelo de preferencia:

**Haz clic aquí para desplegar y copiar el prompt de extracción**

La estructura del prompt coincide con `data/cv_base.example.json`: mismos nombres de claves, mismos grupos de habilidades y los campos opcionales de fullstack.

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
  "education": "Título Profesional o Técnico\nInstitución Educativa\nAño de finalización o estado.",
  "languages": ["Español (Nativo)", "Inglés B2"],
  "target_title_frontend": "Tu título o cargo principal (ej: Desarrollador Frontend)",
  "target_title_fullstack": "Tu título fullstack (ej: Desarrollador Full Stack)",
  "summary_frontend": "Un resumen profesional de 3 a 5 líneas enfocado en tus fortalezas de desarrollo web/frontend.",
  "summary_fullstack": "Un resumen profesional de 3 a 5 líneas enfocado en tu capacidad general o fullstack.",
  "skills_frontend": {
    "Frontend": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3"],
    "Arquitectura Frontend": ["Componentes reutilizables", "Diseño responsive", "Accesibilidad"],
    "E-commerce": ["Shopify", "Liquid", "Stripe"],
    "APIs e integración": ["REST", "GraphQL"],
    "Herramientas de desarrollo": ["Git", "Docker", "Vite"],
    "Optimización web": ["Core Web Vitals", "SEO técnico"],
    "Metodologías": ["Scrum", "Desarrollo ágil"]
  },
  "skills": {
    "Frontend": ["React", "TypeScript", "JavaScript"],
    "Backend": ["Python", "FastAPI", "Node.js", "APIs REST"],
    "Bases de datos": ["PostgreSQL", "MySQL", "SQL"],
    "Arquitectura": ["Clean Architecture", "MVC", "Diseño de APIs"],
    "DevOps e infraestructura": ["Git", "Docker", "Linux", "CI/CD"],
    "E-commerce": ["Shopify", "Liquid", "Stripe"],
    "Optimización web": ["Core Web Vitals", "SEO técnico"],
    "Otros": ["Scrum", "Documentación técnica"]
  },
  "experience": [
    {
      "id": "identificador_unico_en_minusculas",
      "section": "profesional | freelance | proyectos",
      "title": "Nombre del cargo",
      "company": "Nombre Empresa o Proyecto – Modalidad",
      "dates": "Mes Año – Mes Año",
      "type": "Experiencia profesional | Experiencia freelance | Proyecto personal",
      "technologies": ["Tecnología1", "Tecnología2", "Tecnología3"],
      "bullets": [
        "Responsabilidad o logro técnico detallado destacando tecnologías y resultados.",
        "Otra responsabilidad o logro relevante."
      ]
    },
    {
      "id": "identificador_unico_en_minusculas_2",
      "section": "proyectos",
      "title": "Nombre del cargo",
      "title_fullstack": "Nombre del cargo alternativo (opcional)",
      "company": "Nombre del proyecto – Modalidad",
      "dates": "Mes Año – Mes Año",
      "type": "Proyecto personal",
      "technologies": ["Tecnología1", "Tecnología2", "Tecnología3"],
      "bullets": [
        "Responsabilidad o logro técnico detallado.",
        "Otra responsabilidad o logro relevante."
      ],
      "bullets_fullstack": [
        "Versión alternativa con énfasis en backend/persistencia si aplica (opcional)"
      ]
    }
  ]
}

Reglas importantes:
1. Respeta exactamente los nombres, la anidación y los tipos de las claves de la estructura.
2. No agregues campos que no aparezcan en la estructura.
3. Usa `title_fullstack` y `bullets_fullstack` solo cuando exista una versión fullstack; si no aplican, omítelos.
4. No inventes tecnologías, fechas ni empresas que no aparezcan en mi texto.
5. Cada viñeta ('bullets') debe ser completa y detallada, mencionando herramientas y módulos específicos.
6. Devuelve ÚNICAMENTE el bloque JSON válido, sin introducciones ni comentarios.

AQUÍ ESTÁ EL TEXTO DE MI CV:
[Pega aquí el texto completo de tu currículum actual]
```



Una vez generado, guárdalo en `data/cv_base.json` para que el sistema procese y adapte el perfil a las ofertas laborales requeridas.

---



## Personalización de ubicación dinámica

El sistema cuenta con un mecanismo en `app/services/cv_service.py` (`resolve_location`) que detecta automáticamente si la vacante pertenece a una ciudad específica para adaptar la ubicación y disponibilidad del CV sin requerir cambios manuales en el archivo JSON:

- **Detección local:** Si la oferta menciona Barranquilla o Atlántico, establece automáticamente `Barranquilla, Colombia` con disponibilidad presencial/híbrida.
- **Detección capital:** Si la oferta menciona Bogotá, establece `Bogotá, Colombia` con disponibilidad remota/híbrida.
- **Ofertas remotas o generales:** Utiliza la ubicación por defecto definida en tu `cv_base.json` junto con disponibilidad de reubicación nacional.



### ¿Cómo adaptar las ciudades a tu caso personal?

Si resides en otra región o país (por ejemplo: Medellín / Bogotá, o Madrid / Barcelona), puedes personalizar las reglas editando la función `resolve_location` en `app/services/cv_service.py`:

```python
@staticmethod
def resolve_location(job_offer: str, profile: dict[str, Any]) -> tuple[str, str]:
    offer_lower = job_offer.lower()
    
    # Define tus ciudades objetivo según las palabras clave de la oferta
    if any(kw in offer_lower for kw in ("medellin", "medellín", "antioquia")):
        return "Medellín, Colombia", "Presencial, híbrida, remota."
        
    if any(kw in offer_lower for kw in ("bogota", "bogotá")):
        return "Bogotá, Colombia", "Remota, híbrida, presencial."
        
    # Ubicación base del perfil
    return (
        profile.get("location", "Tu Ciudad, País"),
        profile.get("availability", "Remota, híbrida, presencial.")
    )
```

---



## Características principales

- **Alineación dinámica con ATS:** Identifica los requisitos principales de la vacante (frontend, backend, fullstack, e-commerce, APIs, bases de datos) y prioriza las tecnologías y logros con mayor afinidad.
- **Sincronización de título y archivo:** El encabezado del currículum y el nombre del archivo PDF generado adoptan automáticamente la denominación del puesto objetivo (ejemplo: `CV_TuNombre_ShopifyDeveloper.pdf` o `CV_TuNombre_AnalistaDeDesarrollo.pdf`).
- **Resiliencia de formato:** Parser capaz de sanear bloques markdown y normalizar esquemas para garantizar compatibilidad entre diversos modelos LLM.
- **Privacidad por defecto:** en modo Ollama local, la información profesional y las descripciones de las vacantes se procesan en tu equipo sin transmitirse a servicios externos. Si habilitas Ollama Cloud/API directa, los datos se envían al proveedor del modelo según sus políticas.

---



## Contribuciones

Las contribuciones son bienvenidas: mejoras al prompt, nuevos modelos compatibles, correcciones de bugs, mejoras de interfaz, documentación o pruebas. El proyecto está enfocado en **ofertas laborales del área de TI**; todavía no cubre otras industrias ni un uso global.

### Cómo contribuir

1. Haz un fork del repositorio.
2. Crea una rama descriptiva:
  ```bash
   git checkout -b feat/nombre-de-la-mejora
   # o
   git checkout -b fix/nombre-del-bug
  ```
3. Prepara el entorno:
  ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # Windows
   # source .venv/bin/activate    # Linux/macOS
   pip install -r requirements.txt
  ```
4. Copia `.env.example` a `.env` y configura Ollama local o cloud.
5. Realiza el cambio y prueba el flujo completo generando al menos un CV.
6. Haz commit con un mensaje claro:
  ```bash
   git commit -m "feat: mejora la extracción del cargo de la oferta"
   git commit -m "fix: corrige la validación de habilidades vacías"
  ```
7. Sube la rama y abre un Pull Request explicando:
  - Qué problema resuelve.
  - Cómo lo probaste.
  - Modelo de Ollama utilizado (local o cloud).
  - Capturas o logs si aplica.



### Recomendaciones

- Mantén los cambios enfocados; evita mezclar refactors grandes con correcciones pequeñas.
- Respeta la estructura existente: `api/`, `services/`, `schemas/`, `repositories/`.
- Si agregas una variable de entorno, documéntala en `README.md` y `.env.example`.
- Si modificas el prompt o el esquema, pruébalo con más de un modelo cuando sea posible.
- No subas tu `.env`, API keys, datos personales de `data/cv_base.json` ni PDFs generados en `outputs/`.
- Para cambios grandes o nuevas funcionalidades, abre primero un issue para discutir el enfoque.



### Reportar un problema

Incluye:

- Pasos para reproducirlo.
- Modelo y configuración usada (`OLLAMA_MODEL`, local o cloud; **nunca** compartas tu API key).
- Mensaje de error o fragmento relevante de la consola.
- Versión de Python y sistema operativo.

