"""
Referencia de frameworks de copywriting/storytelling, parseada desde
references/CoppieGPT (https://github.com/WynterJones/CoppieGPT, 231 frameworks).

Uso:
    from frameworks import get, recommend_for_pillar, all_frameworks

    get("BAB")                    -> {"name": "BAB", "structure": "Before, After, Bridge"}
    recommend_for_pillar("caso")  -> lista de frameworks recomendados con motivo
"""
import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "references" / "frameworks.json"

_data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
SOURCE = _data["source"]
_by_name = {f["name"].upper(): f for f in _data["frameworks"]}


def all_frameworks():
    return _data["frameworks"]


def get(name: str):
    return _by_name.get(name.upper())


# Frameworks probados para cada pilar de contenido de DatosGT (ver content-strategy/programa_contenido.md).
# No es una lista completa de los 231 -- es la selección curada que ya validamos que aplica bien
# a analitica de datos / educacion / casos de negocio, con el motivo de por que funciona para cada pilar.
RECOMMENDATIONS = {
    "A_habilidad_concreta": [
        ("WWHW", "Why, What, How, What If -- ideal para tutoriales: primero el motivo, luego el paso a paso."),
        ("PPF", "Problem, Promise, Future -- funciona para 'antes de aprender X, sentias esto...'"),
    ],
    "B_datos_negocio": [
        ("PAS", "Problem, Agitate, Solution -- el dueño de negocio ya siente el dolor (perdida de margen); agitarlo con el numero real antes de dar la solucion."),
        ("DIP", "Data, Insight, Proof -- literal para contenido de analitica: dato duro, que revela, prueba."),
    ],
    "C_casos_resultados": [
        ("BAB", "Before, After, Bridge -- el framework que ya usamos en 'El error de Q42,000'. Ideal para casos de cliente."),
        ("3-Act Structure", "Setup, Confrontation, Resolution -- estructura narrativa clasica para contar un caso completo."),
        ("STAR", "Situation, Task, Action, Result -- alternativa mas corta para casos que caben en menos slides."),
        ("S.T.O.R.Y. Selling System", "Situation, Transformation, Obstacles, Results, You -- cierra dirigiendose directo al lector ('y tu?')."),
    ],
    "D_actualidad": [
        ("SCQA", "Situation, Complication, Question, Answer -- bueno para reaccionar a un evento/tendencia con un angulo de datos."),
    ],
    "promocional": [
        ("PASTOR", "Problem, Amplify, Solution, Testimonials, Offer, Response -- para posts de venta directa en Fase 3."),
        ("The Irresistible Offer Framework", "Uso puntual para el lanzamiento de una capacitacion."),
    ],
}


def recommend_for_pillar(pillar: str):
    key = pillar if pillar in RECOMMENDATIONS else None
    if not key:
        raise KeyError(f"Pilar '{pillar}' no reconocido. Opciones: {list(RECOMMENDATIONS)}")
    out = []
    for name, why in RECOMMENDATIONS[key]:
        fw = get(name) or {"name": name, "structure": "(framework compuesto, ver README de CoppieGPT)"}
        out.append({**fw, "why": why})
    return out


if __name__ == "__main__":
    print(f"{len(all_frameworks())} frameworks cargados desde {SOURCE}\n")
    for pillar in RECOMMENDATIONS:
        print(f"== {pillar} ==")
        for f in recommend_for_pillar(pillar):
            print(f"  {f['name']}: {f['structure']}\n    -> {f['why']}")
        print()
