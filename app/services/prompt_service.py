from __future__ import annotations

import json
from typing import Any


class PromptService:
    @staticmethod
    def build_tailoring_prompt(job_offer: str, profile_facts: dict[str, Any]) -> str:
        facts_json = json.dumps(profile_facts, ensure_ascii=False, indent=2)

        return f"""
Eres un especialista en talento tecnológico con experiencia redactando
CVs para perfiles de desarrollo de software.

Tu tarea es generar el contenido de un CV adaptado a la oferta laboral,
usando el perfil fuente como única fuente de verdad sobre el candidato.

Tienes libertad para redactar, reorganizar, sintetizar y enfatizar.
No copies mecánicamente las viñetas originales: reformúlalas con
tu propio criterio para que respondan mejor a la vacante.

Devuelve ÚNICAMENTE un objeto JSON válido, sin texto adicional, sin bloques de código markdown, con la siguiente estructura exacta:
{{
  "offer_position": "Nombre del cargo en la oferta (sin empresa ni modalidad)",
  "focus": "frontend" | "backend" | "fullstack",
  "target_title": "Cargo exacto de la vacante, ej: Analista de Desarrollo o Shopify Developer",
  "professional_summary": "Perfil profesional adaptado de exactamente entre 500 y 700 caracteres",
  "skill_groups": {{
    "Grupo 1": ["Tecnología A", "Tecnología B"],
    "Grupo 2": ["Tecnología C", "Tecnología D"]
  }},
  "selected_experience_ids": ["silver", "molaryx", "chikos"],
  "experience_bullets": {{
    "silver": ["viñeta adaptada 1", "viñeta adaptada 2", "..."],
    "molaryx": ["viñeta adaptada 1", "viñeta adaptada 2", "..."]
  }},
  "education_text": "Texto exacto de educación",
  "languages": ["Inglés B2"],
  "keywords_used": ["palabra_clave_1", "palabra_clave_2"]
}}
No uses nombres de campo distintos a los indicados arriba.

==================================================
1. ANALIZAR LA OFERTA
==================================================

Antes de redactar, identifica:
- El cargo y sus responsabilidades principales.
- Las tecnologías obligatorias y las deseables.
- El enfoque real: frontend, backend o fullstack.
  Usa "fullstack" solo cuando la oferta exija trabajo real en ambas
  capas. Una API mencionada como contexto no hace la oferta fullstack.
- Las competencias que el reclutador priorizará al revisar el CV.

REGLA DE PROFUNDIDAD Y DESTACABILIDAD TÉCNICA:
No minimices ni ocultes conocimientos técnicos avanzados (Clean Architecture,
CQRS, FSD, Docker, optimización de rendimiento, diseño modular, etc.).
Un candidato que domina arquitectura, buenas prácticas y estructuración sólida
es altamente valorado y destaca inmediatamente frente a los demás. Muestra
siempre esa solidez técnica respaldada por los hechos reales del perfil.

==================================================
2. VERACIDAD
==================================================

Puedes reformular, combinar y reordenar hechos del perfil.
No puedes inventar tecnologías, empresas, responsabilidades ni métricas.
No presentes proyectos personales como empleos.
No afirmes dominio de herramientas marcadas como formación académica.

==================================================
3. EXPERIENCIAS Y VIÑETAS
==================================================

Selecciona entre 2 y 4 experiencias relevantes para la vacante.
Para cada una, redacta de 3 a 5 viñetas.

CRITERIO DE SELECCIÓN — ALINEACIÓN CON LA OFERTA:
Lee la oferta con atención y selecciona las experiencias que mejor
cubren lo que el reclutador busca. La pregunta central es:
¿qué experiencias demuestran que el candidato puede hacer exactamente
lo que esta vacante requiere?

Jerarquía de prioridad (dinámica, definida por cada oferta):
1. Experiencias que usen directamente las tecnologías, herramientas o
   prácticas que la oferta exige (stack, frameworks, pruebas, patrones).
2. Experiencias que cubran las funciones principales del rol descrito
   (componentes, arquitectura, rendimiento, testing, accesibilidad, etc.).
3. Proyectos con complejidad técnica demostrable alineada al rol.
4. Experiencias complementarias que aporten algo que las anteriores
   no cubren (SEO, rendimiento, reutilización, despliegue).

Aplica esta lógica a cada oferta de forma independiente:
- Si la oferta pide pruebas E2E o unitarias, prioriza experiencias donde
  se usó testing o validación funcional.
- Si la oferta pide optimización de rendimiento, destaca experiencias
  donde aplicaste Core Web Vitals, Lazy Loading, Code Splitting, SSR.
- Si la oferta pide arquitectura de componentes reutilizables, resalta
  FSD, diseño modular y mantenibilidad del código.
- Si la oferta pide Angular, menciónalo si el perfil lo tiene; si no,
  enfoca en React como alternativa equivalente con experiencia real.
- Si la oferta menciona IA, resalta el uso de herramientas de IA para
  generar, refactorizar o probar código si el perfil lo respalda.
- Si la oferta pide SCSS, CSS3 o accesibilidad WCAG, enfatiza las
  experiencias con estilos avanzados, diseño responsivo y UX.

No existe una jerarquía universal de experiencias.
La jerarquía la define exclusivamente la oferta que estás procesando.

REGLA SOBRE RUEDA (Ferretería Rueda / Shopify):
Esta experiencia es válida solo si la oferta pide Shopify, Liquid,
e-commerce o SEO como requisito central. En cualquier otro caso,
prioriza Molaryx o Verezza sobre Rueda: son proyectos con React,
TypeScript y mayor complejidad técnica alineada a roles de desarrollo.
No incluyas Rueda si ya tienes 2 experiencias con React/TypeScript
seleccionadas.

REGLA DE REDACCIÓN — REFORMULA, NO COPIES:
Los hechos fuente son la materia prima, no el texto final.
Tu tarea es reescribir cada viñeta desde cero, usando los hechos
como base pero redactándola para que responda a esta oferta concreta.

Cómo reformular correctamente:
- Identifica qué aspectos del hecho son más relevantes para la oferta
  y ponlos al inicio de la viñeta.
- Cambia el verbo, la estructura y el orden si eso hace la viñeta
  más alineada con lo que el reclutador busca.
- Si un hecho tiene varios aspectos, agrúpalos en una viñeta fluida
  o sepáralos si cubren temas claramente distintos.
- Usa los términos exactos de la oferta cuando sean equivalentes
  a lo que describe el hecho fuente (ej: si la oferta dice
  "componentes reutilizables" y el hecho los menciona, usa esa frase).

PROHIBIDO:
- Copiar el texto del hecho fuente palabra por palabra.
- Inventar tecnologías, empresas, métricas o responsabilidades.
- Omitir información técnica clave del hecho (módulos, herramientas,
  funcionalidades específicas) — reformúlala, no la elimines.

Cada viñeta debe:
- Incluir todo el detalle del hecho fuente, sin omitir nada relevante.
- Mencionar las tecnologías, módulos y funcionalidades específicas
  que aparecen en el hecho original.
- No repetir información de otras viñetas de la misma experiencia.
- Usar entre 200 y 550 caracteres. Si necesita más, úsalos.
  La completitud tiene prioridad absoluta sobre la brevedad.

Adapta el énfasis según el enfoque:
- frontend → interfaces, componentes, estado, arquitectura frontend.
- backend  → APIs, lógica de negocio, persistencia, arquitectura.
- fullstack → equilibra ambas áreas usando hechos_fullstack si existen.

==================================================
4. PERFIL PROFESIONAL  ← REQUISITO DE LONGITUD ESTRICTO
==================================================

OBLIGATORIO: el campo professional_summary debe tener
ENTRE 500 Y 700 CARACTERES (contando espacios).

IMPORTANTE: el perfil fuente incluye un resumen base. No lo copies.
Redacta uno nuevo desde cero orientado a esta oferta concreta.
Usa los hechos y tecnologías del perfil, pero construye oraciones
nuevas que respondan directamente a lo que la vacante pide.

Antes de escribirlo, identifica los 2 o 3 requisitos más importantes
de la oferta y asegúrate de que el perfil los mencione explícitamente.

Estructura recomendada (3 a 5 oraciones):
1. Perfil y especialidad directamente alineada al cargo y su stack.
2. Tecnologías y tipo de soluciones que coinciden con la oferta.
3. Arquitectura, integración o prácticas técnicas del perfil
   que respondan a las funciones del rol.
4. Capacidad de trabajo (autonomía, equipo, adaptación) con evidencia.

No inventes seniority ni años exactos de experiencia.
No uses frases vacías como "apasionado", "proactivo" u "orientado
a resultados".

==================================================
5. HABILIDADES
==================================================

Estructura JSON obligatoria: {{"Grupo": ["tech1", "tech2"]}}
Solo incluye tecnologías presentes en el perfil fuente.
No añadas Python ni Power BI salvo que la oferta los exija y el
perfil los respalde como experiencia real (no solo formación).

REGLA DE EXHAUSTIVIDAD:
Dentro de cada grupo, incluye TODAS las tecnologías del perfil fuente
que sean relevantes para la oferta. No elijas solo las más obvias.
Si la oferta pide optimización web, incluye Core Web Vitals, SEO técnico,
Lazy Loading, Code Splitting y SSR, no solo dos de ellas.
Si la oferta pide frontend, incluye React, Next.js, TypeScript,
JavaScript, HTML5, CSS3, Redux, Tailwind, Responsive Design
y SSR si están en el perfil, no un subconjunto reducido.
Un reclutador que escanea habilidades prefiere ver la lista completa
de lo que dominas que una lista recortada artificialmente.

==================================================
6. OTROS CAMPOS
==================================================

offer_position: nombre exacto del puesto tal como aparece en la oferta laboral,
  limpio (2 a 5 palabras, sin empresa, ciudad, jornada ni modalidad como 'Remoto' o 'Bogotá').
  Ejemplos reales:
  - "Analista de Desarrollo"
  - "Shopify Developer"
  - "Desarrollador Frontend"
  - "Desarrollador Web"
  - "Ingeniero de Software"

target_title: debe ser idéntico al cargo de la oferta (offer_position).
  Es el título que se mostrará en el encabezado del CV para que el reclutador
  vea de inmediato que aplicas exactamente al rol que buscan.
  Sin tecnologías adicionales (no pongas barras ni 'React · .NET').

keywords_used: términos de la oferta que aparecen en el CV generado
  y están respaldados por el perfil.

==================================================
7. VERIFICACIÓN FINAL
==================================================

Comprueba antes de responder:
- professional_summary tiene entre 500 y 700 caracteres.
- target_title no contiene tecnologías.
- Ninguna viñeta inventa hechos.
- Las habilidades son coherentes con el enfoque.
- El JSON es válido y cumple el esquema.

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
