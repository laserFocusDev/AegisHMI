import json
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = API_DIR.parent

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from generator import generate_and_validate  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
TREND_SPEC = REPO_ROOT / "contracts" / "fixtures" / "spec.golden.trend.json"


def test_generator_includes_structured_operator_intent():
    captured = {}

    def fake_llm(system_prompt, user_prompt):
        captured["user_prompt"] = user_prompt

        with open(TREND_SPEC, "r") as f:
            return json.load(f)

    spec, error = generate_and_validate(
        "Show me the temperature trend",
        "plant.utilities.chiller1",
        "medium",
        llm_fn=fake_llm,
    )

    assert error is None
    assert spec is not None

    prompt = captured["user_prompt"]

    assert "Structured operator intent:" in prompt
    assert "- intent: trend" in prompt
    assert "- focus: temperature, trend" in prompt
    assert "- urgency: normal" in prompt