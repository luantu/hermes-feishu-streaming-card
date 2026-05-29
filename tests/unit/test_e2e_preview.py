from __future__ import annotations

import json
import subprocess
import sys


def test_generate_e2e_preview_writes_visual_and_card_json(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "tools/generate_e2e_preview.py",
            "--output-dir",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    svg = (tmp_path / "e2e-card-preview.svg").read_text(encoding="utf-8")
    cards = json.loads((tmp_path / "e2e-card-preview.json").read_text(encoding="utf-8"))

    assert "Hermes Agent" in svg
    assert "思考中" in svg
    assert "这是流式卡片的最终回答" in svg
    assert set(cards) == {"thinking", "completed"}
    assert cards["thinking"]["schema"] == "2.0"
    assert "这是流式卡片的最终回答" in cards["completed"]["header"]["subtitle"]["content"]
