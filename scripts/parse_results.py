#!/usr/bin/env python3
"""
parse_results.py - Parse SWE-bench evaluation output and notify via NTFY
"""

import os
import sys
import json
import glob
import urllib.request
from pathlib import Path

def find_result_file():
    patterns = [
        "*.json",
        "*/*.json",
        "*/*/*.json",
        "evaluation_results/*.json",
        "logs/*/*.json"
    ]
    candidates = []
    for pat in patterns:
        for f in glob.glob(pat, recursive=True):
            p = Path(f)
            if p.name in ["package.json", "tsconfig.json", "requirements.json"]:
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    # Check for SWE-bench result keys
                    if any(k in data for k in ["resolved", "unresolved", "error", "total_instances", "resolved_instances"]):
                        candidates.append((p, data))
            except Exception:
                pass
    return candidates[0] if candidates else (None, None)

def send_ntfy(topic, message, title=None, priority="default", tags=None):
    if not topic:
        return
    url = f"https://ntfy.sh/{topic}"
    headers = {}
    if title:
        headers["Title"] = title.encode("utf-8")
    if priority:
        headers["Priority"] = priority
    if tags:
        headers["Tags"] = tags

    try:
        req = urllib.request.Request(url, data=message.encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[NTFY] Sent: {resp.status}")
    except Exception as e:
        print(f"[NTFY Error] {e}", file=sys.stderr)

def main():
    ntfy_topic = os.environ.get("NTFY_TOPIC", "gulmezcetiner-tasiyici-9f3a7c21")
    model_name = os.environ.get("MODEL_NAME", "gulmezcetiner-0.1-pro-27b")
    run_id = os.environ.get("RUN_ID", "swebench_run")
    step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")

    res_file, data = find_result_file()

    if not data:
        print("[WARN] No standard SWE-bench result JSON found. Checking directories...")
        summary_md = f"### ⚠️ SWE-bench Değerlendirme Tamamlandı (Sonuç Dosyası Ayrıştırılamadı)\n- Run ID: `{run_id}`\n- Model: `{model_name}`\n"
        if step_summary_path:
            with open(step_summary_path, "a", encoding="utf-8") as f:
                f.write(summary_md)
        send_ntfy(ntfy_topic, f"SWE-bench değerlendirme bitti fakat sonuç JSON bulunamadı. Run: {run_id}", title="SWE-bench Uyarı", tags="warning")
        return

    print(f"[INFO] Found evaluation results in: {res_file}")

    resolved = data.get("resolved", [])
    unresolved = data.get("unresolved", [])
    error = data.get("error", [])

    total = len(resolved) + len(unresolved) + len(error)
    if total == 0 and "total_instances" in data:
        total = data.get("total_instances", 0)
        res_count = data.get("resolved_instances", 0)
        unres_count = data.get("unresolved_instances", 0)
        err_count = data.get("error_instances", 0)
    else:
        res_count = len(resolved)
        unres_count = len(unresolved)
        err_count = len(error)

    rate = (res_count / total * 100.0) if total > 0 else 0.0

    print("=" * 60)
    print(f"SWE-bench Evaluation Results for {model_name}")
    print(f"Total Instances:      {total}")
    print(f"Resolved (Passed):    {res_count} ({rate:.1f}%)")
    print(f"Unresolved (Failed):  {unres_count}")
    print(f"Errors:               {err_count}")
    print("=" * 60)

    # Prepare Markdown Summary
    summary_md = f"""## 📊 SWE-bench Değerlendirme Raporu

**Model:** `{model_name}`  
**Run ID:** `{run_id}`  
**Sonuç Dosyası:** `{res_file}`  

| Metrik | Değer |
|---|---|
| **Toplam Görev** | **{total}** |
| **Çözülen (Pass)** | **{res_count}** ({rate:.1f}%) |
| **Çözülemeyen (Fail)** | {unres_count} |
| **Ortam / Hata** | {err_count} |

### 🎯 Detaylar
"""
    if resolved:
        summary_md += "\n**✅ Çözülen Görevler:**\n"
        for iid in resolved:
            summary_md += f"- `{iid}`\n"

    if unresolved:
        summary_md += "\n**❌ Çözülemeyen Görevler:**\n"
        for iid in unresolved:
            summary_md += f"- `{iid}`\n"

    if error:
        summary_md += "\n**⚠️ Hata Alınan Görevler:**\n"
        for iid in error:
            summary_md += f"- `{iid}`\n"

    if step_summary_path:
        with open(step_summary_path, "a", encoding="utf-8") as f:
            f.write(summary_md)

    # Prepare NTFY Message
    status_emoji = "🎉" if res_count > 0 else "ℹ️"
    ntfy_title = f"{status_emoji} SWE-bench: %{rate:.1f} Başarı ({res_count}/{total})"
    ntfy_body = f"Model: {model_name}\nToplam: {total} | Çözülen: {res_count} (%{rate:.1f})\nFail: {unres_count} | Hata: {err_count}\nRun: {run_id}"

    send_ntfy(ntfy_topic, ntfy_body, title=ntfy_title, tags="tada" if res_count > 0 else "chart")

if __name__ == "__main__":
    main()
