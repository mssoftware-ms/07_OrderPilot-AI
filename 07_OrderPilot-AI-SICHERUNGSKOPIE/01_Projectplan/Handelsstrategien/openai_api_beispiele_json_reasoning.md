# OpenAI API – Python-Beispiele (JSON Input/Output + Reasoning an/aus)

Stand: Januar 2026. Beispiele für **Responses API** (empfohlen) und optional **Chat Completions**.  
Alle Snippets sind so geschrieben, dass du **Request-JSON** und **Response-JSON** direkt sehen kannst.

---

## 0) Installation & Key

### Windows (PowerShell)
```powershell
setx OPENAI_API_KEY "DEIN_API_KEY"
```

### Python
```bash
pip install -U openai requests
```

---

## 1) Hilfsfunktionen (robust: Text aus Response extrahieren + JSON dump)

Je nach SDK-Version existiert `response.output_text`. Zur Sicherheit kannst du immer robust aus `response.output` extrahieren.

```python
import json
from typing import Any

def to_json(obj: Any) -> str:
    """SDK-Objekt -> JSON (pretty)."""
    if hasattr(obj, "model_dump_json"):
        return obj.model_dump_json(indent=2)
    if hasattr(obj, "model_dump"):
        return json.dumps(obj.model_dump(), ensure_ascii=False, indent=2)
    if hasattr(obj, "dict"):
        return json.dumps(obj.dict(), ensure_ascii=False, indent=2)
    return json.dumps(obj, ensure_ascii=False, indent=2)

def extract_output_text(response: Any) -> str:
    """
    Aggregiert Text aus Response.output (Responses API).
    Funktioniert auch dann, wenn output_text nicht verfügbar ist.
    """
    # SDK-Shortcut (falls vorhanden)
    if hasattr(response, "output_text"):
        try:
            return response.output_text or ""
        except Exception:
            pass

    out = []
    output_items = getattr(response, "output", None) or []
    for item in output_items:
        # "message" Items enthalten typischerweise content-Blöcke
        if getattr(item, "type", None) == "message":
            content = getattr(item, "content", None) or []
            for block in content:
                # Textblock
                if getattr(block, "type", None) in ("output_text", "text"):
                    text = getattr(block, "text", None)
                    if isinstance(text, str):
                        out.append(text)
                    elif hasattr(text, "value"):  # manche SDKs kapseln Text
                        out.append(getattr(text, "value"))
    return "\n".join([t for t in out if t])
```

---

## 2) Responses API – Reasoning **AUS** (`reasoning.effort="none"`) + JSON rein/raus

```python
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

request_payload = {
    "model": "gpt-5.2",
    "input": "Gib mir 3 prägnante Stichpunkte, warum man Unit-Tests schreibt.",
    "reasoning": {"effort": "none"},        # Reasoning AUS (niedrigste Stufe / minimalste Reasoning-Tokens)
    "temperature": 0.2,                     # Sampling (modellabhängig)
    "text": {"verbosity": "low"},           # optional
    "max_output_tokens": 200,
}

print("=== JSON REQUEST ===")
print(json.dumps(request_payload, ensure_ascii=False, indent=2))

response = client.responses.create(**request_payload)

print("\n=== JSON RESPONSE (voll) ===")
print(to_json(response))

print("\n=== output_text (extrahiert) ===")
print(extract_output_text(response))

print("\n=== Usage (Token) ===")
raw = response.model_dump() if hasattr(response, "model_dump") else {}
print(json.dumps(raw.get("usage", {}), ensure_ascii=False, indent=2))
```

**Hinweis:** Bei Reasoning-Modellen können **Reasoning-Tokens** anfallen und sind **als Output-Tokens abgerechnet**, auch wenn sie nicht im Klartext ausgegeben werden. Du siehst sie in `usage.output_tokens_details.reasoning_tokens`.

---

## 3) Responses API – Reasoning **AN** (`reasoning.effort="high"` oder `"xhigh"`) + Reasoning-Tokens prüfen

```python
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

request_payload = {
    "model": "gpt-5.2",
    "input": "Entwirf eine robuste Ordnerstruktur für ein Python-Desktopprojekt (Qt), inkl. kurzer Begründung.",
    "reasoning": {"effort": "high"},     # AN: none|minimal|low|medium|high|xhigh
    "text": {"verbosity": "medium"},
    "max_output_tokens": 700,
}

response = client.responses.create(**request_payload)

print("=== JSON RESPONSE (voll) ===")
print(to_json(response))

raw = response.model_dump() if hasattr(response, "model_dump") else {}
usage = raw.get("usage", {})
print("\n=== usage.output_tokens_details (Reasoning sichtbar) ===")
print(json.dumps(usage.get("output_tokens_details", {}), ensure_ascii=False, indent=2))

print("\n=== output_text ===")
print(extract_output_text(response))
```

---

## 4) Responses API – Multi-Turn / Conversation State mit `previous_response_id`

```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Turn 1
r1 = client.responses.create(
    model="gpt-5.2",
    input=[
        {"role": "system", "content": "Du bist ein präziser Softwarearchitekt."},
        {"role": "user", "content": "Ich baue eine Win11 Python-Qt Trading-App. Nenne mir 5 Architekturprinzipien."},
    ],
    reasoning={"effort": "medium"},
    store=True,  # optional: stateful
)

# Turn 2 (verkettet)
r2 = client.responses.create(
    model="gpt-5.2",
    previous_response_id=r1.id,
    input="Setze daraus eine kurze Checkliste (max 8 Punkte).",
    reasoning={"effort": "none"},
)

print("Turn1:", extract_output_text(r1))
print("Turn2:", extract_output_text(r2))
```

---

## 5) Responses API – Strukturiertes JSON per JSON Schema (`text.format`)

```python
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

schema = {
    "type": "object",
    "properties": {
        "entscheidung": {"type": "string", "enum": ["approve", "reject", "needs_more_info"]},
        "gruende": {"type": "array", "items": {"type": "string"}},
        "naechste_schritte": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["entscheidung", "gruende", "naechste_schritte"],
    "additionalProperties": False
}

request_payload = {
    "model": "gpt-4.1",
    "input": [
        {"role": "system", "content": "Antworte strikt im JSON Schema."},
        {"role": "user", "content": "Soll ich für eine lokale Desktop-App eher SQLite oder PostgreSQL nutzen? Später evtl. Multi-User."}
    ],
    "text": {
        "format": {
            "type": "json_schema",
            "name": "db_decision",
            "schema": schema,
            "strict": True
        }
    },
    "max_output_tokens": 350
}

response = client.responses.create(**request_payload)

# output_text ist dann JSON (als String)
json_text = extract_output_text(response)
print("=== JSON (output_text) ===")
print(json_text)

parsed = json.loads(json_text)
print("\n=== Parsed dict ===")
print(parsed)
```

---

## 6) Raw HTTP (ohne SDK) – `POST /v1/responses` mit `requests`

```python
import os
import json
import requests

api_key = os.environ["OPENAI_API_KEY"]

payload = {
    "model": "gpt-5.2",
    "input": "Schreibe eine sehr kurze Erklärung (max 2 Sätze) zu Dependency Injection.",
    "reasoning": {"effort": "none"},
    "text": {"verbosity": "low"},
    "max_output_tokens": 120
}

print("=== JSON REQUEST ===")
print(json.dumps(payload, ensure_ascii=False, indent=2))

resp = requests.post(
    "https://api.openai.com/v1/responses",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    data=json.dumps(payload),
    timeout=60,
)

resp.raise_for_status()
data = resp.json()

print("\n=== JSON RESPONSE (gekürzt) ===")
print(json.dumps(
    {
        "id": data.get("id"),
        "model": data.get("model"),
        "status": data.get("status"),
        "reasoning": data.get("reasoning"),
        "usage": data.get("usage"),
        "output_first_item": (data.get("output") or [])[:1],
    },
    ensure_ascii=False,
    indent=2
))
```

---

## 7) Optional: Chat Completions – Reasoning-Effort + JSON Mode (`response_format`)

```python
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

request_payload = {
    "model": "gpt-5.2",
    "messages": [
        {"role": "system", "content": "Du bist ein präziser Assistent."},
        {"role": "user", "content": "Gib ein JSON mit Keys: name, vorteil, nachteil (alle Strings)."}
    ],
    "reasoning_effort": "none",           # none|minimal|low|medium|high|xhigh
    "response_format": {"type": "json_object"},
    "temperature": 0.2,
}

print("=== JSON REQUEST ===")
print(json.dumps(request_payload, ensure_ascii=False, indent=2))

resp = client.chat.completions.create(**request_payload)

content = resp.choices[0].message.content
print("\n=== message.content (JSON) ===")
print(content)

parsed = json.loads(content)
print("\n=== parsed dict ===")
print(parsed)
```

---

## 8) Praxis-Tipps (kurz, aber wichtig)

- **Reasoning effort** steuert Kosten/Qualität/Latenz. Bei komplexen Aufgaben: `medium` oder `high`. Für UI-nahe Antworten: oft `none`/`minimal`.
- **`max_output_tokens`** begrenzt Output *inkl. Reasoning-Tokens*. Wenn zu klein, kann der Request „incomplete“ enden, selbst ohne sichtbare Ausgabe.
- Für **“garantiertes JSON”**: nutze **Structured Outputs** (`text.format` mit JSON Schema) statt „Bitte antworte als JSON“.
- Für Multi-Turn: **`previous_response_id`** (oder `store=True`) nutzen, statt Kontext selbst „zusammenzukleben“.
