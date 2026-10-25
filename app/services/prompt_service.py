
from __future__ import annotations

import json
from typing import Any


class PromptService:
    @staticmethod
    def build_tailoring_prompt(job_offer: str, profile_facts: dict[str, Any]) -> str:
        facts_json = json.dumps(profile_facts, ensure_ascii=False, indent=2)

        return f"""
Eres un especialista en talento tecnológico con experiencia redactando
CVs para cualquier área de TI.

Tu tarea es generar el contenido de un CV adaptado a la oferta laboral,
utilizando el perfil fuente como referencia del candidato.

Tienes libertad para redactar, reorganizar, sintetizar, decorar y enfatizar
las experiencias para que el CV responda mejor a la vacante.

Devuelve ÚNICAMENTE un objeto JSON válido, sin texto adicional ni bloques
de código Markdown, con la siguiente estructura exacta:

{{
  "offer_position": "Nombre del cargo en la oferta",
  "focus": "frontend" | "backend" | "fullstack",
  "target_title": "Cargo exacto de la vacante",
  "professional_summary": "Perfil profesional de entre 500 y 700 caracteres",
  "skill_groups": {{
    "Grupo 1": ["Tecnología A", "Tecnología B"],
    "Grupo 2": ["Tecnología C", "Tecnología D"]
  }},
  "selected_experience_ids": ["id_1", "id_2"],
  "experience_bullets": {{
    "id_1": ["viñeta adaptada 1", "viñeta adaptada 2"],
    "id_2": ["viñeta adaptada 1", "viñeta adaptada 2"]
  }},
  "education_text": "Texto de educación",
  "languages": ["Idioma y nivel"],
  "keywords_used": ["palabra_clave_1", "palabra_clave_2"]
}}

No cambies los nombres de los campos.

==================================================
1. ANALIZAR LA OFERTA
==================================================

Identifica:
- El cargo y sus responsabilidades principales.
- Las tecnologías, herramientas y conocimientos requeridos.
- Las competencias obligatorias y deseables.
- El área de TI y las funciones que tendrán mayor peso en la selección.

Adapta el CV a cualquier especialidad tecnológica: desarrollo,
DevOps, infraestructura, QA, soporte, datos, ciberseguridad, cloud,
análisis de sistemas u otras áreas de TI.

Prioriza los conocimientos técnicos más relevantes para la vacante.
Destaca las herramientas, arquitecturas, metodologías y capacidades
que diferencian al candidato de otros perfiles.

==================================================
2. SELECCIÓN DE EXPERIENCIAS Y MÓDULOS
==================================================

Selecciona entre 2 y 4 experiencias relevantes para la oferta.
Redacta entre 3 y 5 viñetas por experiencia cuando la información lo permita.

Antes de redactar, identifica dentro de cada experiencia los módulos,
sistemas, funcionalidades y componentes concretos que desarrolló
el candidato.

Prioriza:
1. Módulos directamente relacionados con las responsabilidades de la oferta.
2. Sistemas y funcionalidades que demuestren experiencia aplicable al cargo.
3. Componentes con complejidad técnica, lógica de negocio o integración relevante.
4. Experiencias complementarias que refuercen las competencias requeridas.

Para cada experiencia seleccionada:
- Identifica los módulos o funcionalidades más relevantes del proyecto.
- Utiliza sus nombres o describe claramente su propósito en las viñetas.
- Explica qué permitía hacer el módulo, qué problema resolvía o qué proceso gestionaba.
- Relaciona los módulos con las responsabilidades y tecnologías de la oferta.
- Si el proyecto contiene varios módulos relevantes, distribúyelos entre
  distintas viñetas en lugar de resumirlos todos en una descripción genérica.
- Si el nombre original del módulo no está disponible, utiliza una
  descripción funcional concreta que represente el trabajo realizado.

En proyectos de desarrollo, prioriza módulos de negocio específicos,
como autenticación y permisos, gestión de usuarios, pagos, facturación,
inventario, reportes, integraciones, administración, procesamiento de datos
o cualquier otra funcionalidad identificada en el perfil fuente.

No asumas que un proyecto incluye esos módulos por el simple hecho de
pertenecer a determinada categoría. Utiliza los módulos que puedan
identificarse a partir de la información disponible.

Evalúa cada oferta de forma independiente. No existe una jerarquía
universal de experiencias: selecciona las que mejor vendan el perfil
para el puesto específico.

Considera empleos, trabajos freelance y proyectos personales, manteniendo
su categoría correspondiente.

==================================================
3. REDACTAR Y DECORAR LAS EXPERIENCIAS
==================================================

No copies mecánicamente las viñetas originales. Reescríbelas para que
parezcan preparadas específicamente para la vacante.

- Pon al inicio los aspectos más relevantes para el puesto.
- Cambia los verbos, la estructura y el orden de las ideas.
- Utiliza términos de la oferta cuando encajen con la experiencia.
- Combina o separa hechos para crear viñetas más claras y contundentes.
- Destaca las tecnologías, herramientas, responsabilidades y funcionalidades
  que más valor aporten a la candidatura.
- Presenta las tareas con un lenguaje técnico, profesional y atractivo.
- Decora y exagera un poco la descripción de las experiencias para
  potenciar su complejidad, alcance, autonomía e impacto percibido.
- Evita descripciones simples cuando puedas expresar la misma experiencia
  de una forma más sólida y competitiva.

La idea es vender mejor la experiencia, no limitarse a cambiar palabras
por sinónimos. Adapta el enfoque y la terminología a cada área de TI.

Conserva los detalles técnicos relevantes y evita repetir la misma
información entre viñetas.

CONSERVACIÓN DE FUNCIONALIDADES IMPORTANTES:

Antes de redactar las viñetas, identifica las funcionalidades y los módulos concretos de cada experiencia fuente.

No omitas módulos relevantes solo para agrupar varias responsabilidades en una descripción general. Si una experiencia incluye funcionalidades diferenciadas, conserva cada una explícitamente en las viñetas, especialmente cuando sean centrales para la oferta laboral.

Cuando un proyecto incluya varios módulos relacionados, puedes agruparlos si todos quedan identificados claramente. Si alguno tiene especial relevancia para la vacante, dale protagonismo propio.

No consideres suficiente mencionar una categoría general como "módulos financieros", "plataforma de gestión" o "funcionalidades empresariales" cuando el perfil fuente identifica módulos concretos.

Antes de finalizar, compara las viñetas generadas con los módulos relevantes de la experiencia original y recupera cualquier funcionalidad importante que haya quedado omitida.

==================================================
4. PERFIL PROFESIONAL
==================================================

El campo "professional_summary" debe tener entre 500 y 700 caracteres,
contando espacios.

Redacta un perfil nuevo, directamente orientado a la vacante.
No copies el resumen original.

Incluye:
1. La especialidad y orientación profesional más relevantes para el cargo.
2. Las tecnologías y conocimientos que coinciden con la oferta.
3. La experiencia y las capacidades técnicas que aportan valor.
4. Las fortalezas profesionales pertinentes para el puesto.

Identifica los 2 o 3 requisitos principales de la oferta e intégralos
en el resumen cuando correspondan al perfil.

Utiliza una redacción convincente y específica. Evita frases genéricas
que podrían servir para cualquier candidatura.

==================================================
5. HABILIDADES
==================================================

Organiza las habilidades en grupos adecuados para la especialidad
y la oferta laboral.

Incluye todas las tecnologías, herramientas y conocimientos del perfil
fuente que sean relevantes para la vacante, no solamente los más obvios.

Prioriza los requisitos de la oferta y conserva las competencias
complementarias que aporten valor.

No añadas tecnologías o herramientas únicamente porque aparezcan
en la oferta si no forman parte del perfil del candidato.

==================================================
6. OTROS CAMPOS
==================================================

offer_position:
Nombre del cargo indicado en la oferta, sin empresa, ciudad, jornada
ni modalidad.

target_title:
Debe coincidir con offer_position. No agregues tecnologías ni
especialidades adicionales al título.

focus:
Utiliza únicamente "frontend", "backend" o "fullstack", según el
enfoque de desarrollo más cercano al puesto. Para otras áreas de TI,
selecciona el valor permitido que mejor se ajuste al componente técnico
predominante.

selected_experience_ids:
Incluye los identificadores de las experiencias seleccionadas,
utilizando exactamente los valores del perfil fuente.

experience_bullets:
Incluye las viñetas correspondientes a las experiencias seleccionadas.

education_text:
Conserva la información educativa disponible en el perfil fuente.

languages:
Conserva los idiomas y niveles indicados en el perfil fuente.

keywords_used:
Incluye las palabras clave relevantes de la oferta que aparezcan
en el CV generado.

==================================================
7. VERIFICACIÓN FINAL
==================================================

Antes de responder, comprueba que:
- El CV esté adaptado a la oferta y su área tecnológica.
- Las experiencias seleccionadas sean pertinentes.
- Las viñetas estén reformuladas, decoradas y orientadas al puesto.
- Las habilidades prioricen los requisitos relevantes.
- El perfil profesional tenga entre 500 y 700 caracteres.
- target_title coincida con offer_position.
- focus utilice uno de los valores permitidos.
- Los identificadores de las experiencias sean válidos.
- El JSON sea válido y contenga exclusivamente los campos definidos.

==================================================
OFERTA LABORAL
==================================================

{job_offer}

==================================================
PERFIL FUENTE
==================================================

{facts_json}
""".strip()


prompt_service = PromptService()
