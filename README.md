# 🚀 SWE-bench Değerlendirme Sahası (Docker & GitHub Actions)

Bu repo, **Gülmez & Çetiner (0.1-Pro / 0.2)** modellerinin SWE-bench (Verified & Lite) ölçümlerini resmi Docker container ortamında çalıştırmak için kurulmuş hibrit değerlendirme platformudur.

---

## 🏗️ Hibrit Bulut Pipeline Mimarisi

Kaggle standart GPU ortamı eski C derleyicilerini ve kütüphanelerini barındırmadığı için, model yama üretimi ile test ortamı birbirinden ayrılmıştır:

```
[ Kaggle GPU / TPU ] (27B / 72B Model Çıkarımı)
       │
       ▼  (predictions.jsonl üretilir ve GitHub'a aktarılır)
[ GitHub Repository: swebench-eval ]
       │
       ▼  (Otomatik GitHub Actions tetiklenir)
[ GitHub Actions Runner ] (Ubuntu + Tam Yetkili Docker Ortamı)
       │
       ▼  (Resmi SWE-bench test harness çalıştırılır: swebench.harness.run_evaluation)
[ Sonuç & Skor Kartı ] ──► NTFY ile Telefona Anlık Bildirim! 📱
```

---

## ⚡ Kullanım Yöntemleri

### 1. GitHub Web Arayüzünden Manuel Çalıştırma (Workflow Dispatch)
1. **Actions** sekmesine gidin.
2. **SWE-bench Docker Evaluation** workflow'unu seçin.
3. **Run workflow** butonuna tıklayın:
   - `predictions_file`: `predictions/predictions_b96.jsonl` (veya istediğiniz dosya)
   - `dataset_name`: `SWE-bench/SWE-bench_Verified`
   - `max_workers`: `2` (Runner limitine göre)

### 2. Kaggle veya Harici Betikten Otomatik Tetikleme (Repository Dispatch)
GitHub Personal Access Token (PAT) ile Kaggle'dan doğrudan API çağrısı yapılabilir:

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/glassesglitchstudio-lab/swebench-eval/dispatches \
  -d '{
    "event_type": "eval_predictions",
    "client_payload": {
      "run_id": "kaggle_b96_v25",
      "dataset_name": "princeton-nlp/SWE-bench_Verified",
      "predictions_b64": "'$(base64 -w 0 predictions.jsonl)'"
    }
  }'
```

### 3. Git Push ile Otomatik Değerlendirme
`predictions/` dizinine yeni bir `.jsonl` dosyası pushlandığında workflow kendiliğinden tetiklenir.

---

## 📱 NTFY Bildirimleri
Tüm başlatma, ilerleme ve değerlendirme sonuçları NTFY kanalına (`https://ntfy.sh/gulmezcetiner-tasiyici-9f3a7c21`) otomatik iletilir.
