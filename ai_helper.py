import json
import os
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()


def has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def generate_ai_enhancements(break_rows: List[Dict]) -> Dict[str, List[Dict]]:
    if not has_api_key() or not break_rows:
        return {"insights": [], "executive_additions": []}

    try:
        from openai import OpenAI
    except Exception:
        return {"insights": [], "executive_additions": []}

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = (
        "You are an expert Finance and Risk Product Owner assistant.\n"
        "Given reconciliation break rows, produce concise JSON with:\n"
        "1) insights: list of {recon_id, ai_root_cause, ai_recommendation, escalation_note}\n"
        "2) executive_additions: list of {section, generated_summary}\n"
        "Return valid JSON only.\n\n"
        f"Rows:\n{json.dumps(break_rows, default=str)}"
    )

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            temperature=0.2,
        )
        text = response.output_text.strip()
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            return {"insights": [], "executive_additions": []}
        return {
            "insights": parsed.get("insights", []),
            "executive_additions": parsed.get("executive_additions", []),
        }
    except Exception:
        return {"insights": [], "executive_additions": []}
