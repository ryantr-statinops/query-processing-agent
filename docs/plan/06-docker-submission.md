# Người 6 — Đóng gói Docker, Submission Generator và Nghiệm thu BTC

## 1. Mục tiêu và phạm vi

Tài liệu này đặc tả toàn bộ quy chuẩn kỹ thuật cho **Phase 6 / Task 6: Đóng gói Docker, sinh file kết quả (`submission.jsonl`), quản lý logs và nghiệm thu nộp bài**, tuân thủ 100% hướng dẫn chính thức từ Ban tổ chức (*Docker Submission Guide – Zalo AI Challenge 2026: DataMate*).

### Thông tin đăng ký đội thi:
* **Tên đội thi:** Zalo trừ nửa
* **Định danh Docker (lowercase identifier):** `zalotrunua`
* **Docker Image Tag:** `zaic2026_datamate_zalotrunua:final`
* **File nén nộp bài:** `zaic2026_datamate_zalotrunua.tar.gz`
* **File mã băm MD5:** `zaic2026_datamate_zalotrunua.tar.gz.md5`
* **Nền tảng mục tiêu:** `linux/amd64` (chạy trên 2 × NVIDIA RTX 5090 32GB VRAM, CUDA ≥ 12.8, Compute Capability 12.0)
* **Base Image lựa chọn:** `vllm/vllm-openai:v0.10.1.1` (Phương án A — Khuyến nghị chính thức của BTC)

---

## 2. Quy chuẩn Input / Output và Định dạng Submission

### 2.1. Cấu trúc thư mục dữ liệu đầu vào (`/data`)
Môi trường thi đấu mount thư mục dữ liệu tại `/data` với quyền **chỉ đọc (`:ro`)**:
```text
/data/
├── data/<business_id>/
│   ├── *.csv | *.xlsx | *.sqlite
│   └── README.md
├── rulebook.md          # Luật nghiệp vụ và từ điển theo kỳ
├── calendar.csv         # Lịch âm dương dùng chung
└── questions.jsonl      # Danh sách câu hỏi (id, business_id, question, as_of_date)
```

### 2.2. File kết quả nộp bài (`/result/submission.jsonl`)
File kết quả được ghi tại `/result/submission.jsonl`. Mỗi dòng là đúng một JSON object:

```json
{"id": "q_001883280e83", "type": "number", "answer": 89526400}
{"id": "q_002883280e84", "type": "percent", "answer": 12.5}
{"id": "q_003883280e85", "type": "date", "answer": "2026-08-15"}
{"id": "q_004883280e86", "type": "boolean", "answer": true}
{"id": "q_005883280e87", "type": "string", "answer": "Trà đào cam sả"}
{"id": "q_006883280e88", "type": "list", "answer": ["Sản phẩm A", "Sản phẩm B"]}
{"id": "q_007883280e89", "type": "table", "answer": {"columns": ["khach_hang", "so_tien_no"], "rows": [["Nguyễn Văn A", 1500000]]}}
{"id": "q_008883280e90", "type": "unanswerable", "reason": "Shop không có sổ kho"}
```

> [!IMPORTANT]
> **Cơ chế ghi ngay lập tức (Immediate Flush):** Hệ thống phải mở file và flush từng dòng câu trả lời ngay sau khi giải xong từng câu hỏi. Nếu container bị ngắt giữa chừng hoặc chạm mốc giới hạn 6 giờ, BTC sẽ chấm điểm trên các câu đã kịp ghi; các câu chưa ghi được tính là `abstain` (0 điểm).
>
> *(Lưu ý phát triển: Để thuận tiện cho team đối chiếu, hệ thống sẽ tự động tạo thêm bản copy/symlink `answer.jsonl` song song với `submission.jsonl` chuẩn)*.

### 2.3. Nhật ký thực thi (`/result/logs/`)
Mỗi câu hỏi bắt buộc sinh một dòng log JSON lưu trong `/result/logs/` với các trường:
* `id`: Question ID.
* `answer`: Đối tượng kết quả (chứa `type` và `answer`).
* `elapsed_ms`: Thời gian thực thi (mili-giây) từ khi nhận câu hỏi đến khi có đáp án.
* `thinking`: Chuỗi suy luận reasoning của mô hình (ví dụ trích xuất thẻ `<think>...</think>` hoặc `reasoning_content` của vLLM). Điền `null` nếu không qua mô hình.
* `code`: Đoạn SQL hoặc mã hàm Python cụ thể đã chạy thực tế.
* `output`: Dữ liệu thô trả về từ việc thực thi truy vấn.

Ví dụ bản ghi log chuẩn:
```json
{
  "id": "q_001883280e83",
  "answer": {"type": "number", "answer": 89526400},
  "elapsed_ms": 3210,
  "thinking": "Câu hỏi yêu cầu tính tổng giá trị các phiếu nhập hàng trong tháng 09/2026. Lọc SoNhapHang theo ngày >= 2026-09-01 và <= 2026-09-07.",
  "code": "SELECT SUM(ThanhTien) AS value FROM SoNhapHang WHERE NgayNhap >= '2026-09-01' AND NgayNhap <= '2026-09-07'",
  "output": 89526400
}
```

---

## 3. Cấu trúc thư mục bên trong Container (`/code/`)

Theo quy định bắt buộc tại Mục 4 của tài liệu BTC:
```text
/code/
├── predict.sh           # Entrypoint chạy không tham số
├── README.md            # Tài liệu khai báo mô hình, license, cách tiếp cận
├── requirements.txt     # Danh sách thư viện phụ thuộc
├── src/                 # Toàn bộ mã nguồn thực thi suy luận (datamate package)
├── models/              # Trọng số mô hình offline (Qwen 9B / weights)
└── training_code/       # Bắt buộc có giải trình nguồn gốc (Rule 8)
    ├── README.md        # Hướng dẫn tái hiện huấn luyện
    ├── requirements.txt # Thư viện phục vụ huấn luyện (nếu có)
    ├── train.sh         # Script huấn luyện (nếu có)
    ├── configs/         # Thiết lập huấn luyện
    ├── src/             # Mã nguồn pipeline huấn luyện
    ├── data_generation/ # Script sinh/xử lý dữ liệu
    ├── data/            # Dữ liệu train/val dùng trong quá trình thử nghiệm
    ├── logs/            # Nhật ký huấn luyện
    ├── checkpoints/     # Checkpoints kiểm chứng
    └── data_manifest.json # Bảng băm SHA-256 các dataset và URL model gốc
```

---

## 4. Dockerfile Chuẩn (Phương án A — vLLM & Blackwell Ready)

Dockerfile chuẩn hóa theo tài liệu BTC Mục 8 & 9:

```dockerfile
FROM vllm/vllm-openai:v0.10.1.1

# 1. Reset ENTRYPOINT để hỗ trợ lệnh docker run với bash và predict.sh
ENTRYPOINT []

# 2. Thiết lập môi trường offline và tối ưu NCCL cho RTX 5090 đôi
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    PIP_NO_CACHE_DIR=1 \
    NCCL_P2P_DISABLE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# 3. Cài đặt các thư viện bổ sung cho runtime (Polars, DataFusion, openpyxl, ...)
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

# 4. Bản vá NCCL cho GPU Blackwell / RTX 5090 tránh lỗi treo giao tiếp 2 GPU
RUN pip install --no-cache-dir --no-deps nvidia-nccl-cu12==2.27.7

# 5. Copy trọng số mô hình offline (tách lớp riêng để cache)
COPY models/ /code/models/

# 6. Copy mã nguồn giải trình huấn luyện (theo Rule 8 BTC)
COPY training_code/ /code/training_code/

# 7. Copy mã nguồn suy luận và script entrypoint
COPY predict.sh README.md /code/
COPY src/ /code/src/

# 8. Cấp quyền thực thi cho predict.sh
RUN chmod +x /code/predict.sh

# 9. Lệnh mặc định
CMD ["bash", "/code/predict.sh"]
```

---

## 5. Đặc tả Entrypoint `predict.sh`

File `/code/predict.sh` được chạy trực tiếp từ BTC không kèm tham số:
```bash
#!/bin/bash
set -euo pipefail

# 1. Khởi tạo thư mục đầu ra bắt buộc
mkdir -p /result/logs

# 2. Thiết lập biến môi trường chạy offline
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export PYTHONUNBUFFERED=1

# 3. Kích hoạt engine suy luận DataMate
echo "[DataMate] Bắt đầu suy luận với dữ liệu tại /data..."
python3 -m datamate \
  --data-root /data \
  --result-root /result \
  --submission-path /result/submission.jsonl \
  --log-dir /result/logs \
  --alias-answer-path /result/answer.jsonl

echo "[DataMate] Hoàn tất quá trình suy luận."
```

---

## 6. Kế hoạch triển khai Sub-tasks (S01 $\rightarrow$ S05)

| Mã Task | Tên nhiệm vụ | Chi tiết thực hiện | Tiêu chí hoàn thành (Acceptance Criteria) |
|---|---|---|---|
| **S01** | Submission & Log Writer | Cài đặt `datamate.application.writer` hỗ trợ flush tức thì từng câu vào `submission.jsonl` và `logs/*.jsonl` | File output đúng JSONL, đầy đủ trường BTC, không bị mất dữ liệu khi exit đột ngột |
| **S02** | Training Code Package & Manifest | Xây dựng thư mục `/code/training_code/` và sinh file `data_manifest.json` (SHA-256 các tập dữ liệu) | Đáp ứng điều kiện kiểm tra hợp lệ Rule 8 của BTC |
| **S03** | Dockerfile & predict.sh | Soạn thảo Dockerfile vLLM chính thức và cập nhật `predict.sh` chạy không tham số | Docker build thành công không lỗi, layer weights được cache riêng biệt |
| **S04** | Kiểm thử Reproducibility & Offline Smoke Test | Chạy thử nghiệm trên container với cờ `--network none` và `--shm-size=16g` | Lặp lại 2 lần suy luận cho độ chênh lệch $\|PA_1 - PA_2\| \le 0.03$; thời gian chạy $\le$ 6h |
| **S05** | Export Archive & Checksum | Đóng gói ra file `.tar.gz` và tạo file `.md5` theo cú pháp chuẩn của BTC | File `.tar` uncompressed $\le$ 100 GB; kiểm tra `md5sum -c` trả về `OK` |

---

## 7. Lệnh Kiểm thử và Đóng gói Nghiệm thu

### Lệnh chạy kiểm thử chuẩn BTC (Local Smoke Test):
```bash
docker run --rm --gpus '"device=0,1"' --network none --shm-size=16g \
  --entrypoint bash \
  -v "$(pwd)/public_test:/data:ro" \
  -v "$(pwd)/test_output:/result" \
  zaic2026_datamate_zalotrunua:final /code/predict.sh
```

### Lệnh xuất xưởng nộp bài:
```bash
set -o pipefail
# Xuất file nén
docker save zaic2026_datamate_zalotrunua:final | gzip > zaic2026_datamate_zalotrunua.tar.gz

# Kiểm tra dung lượng uncompressed .tar
gzip -dc zaic2026_datamate_zalotrunua.tar.gz | wc -c

# Tạo file mã băm MD5
md5sum zaic2026_datamate_zalotrunua.tar.gz > zaic2026_datamate_zalotrunua.tar.gz.md5

# Tự kiểm tra lại tính toàn vẹn
md5sum -c zaic2026_datamate_zalotrunua.tar.gz.md5
```
*(Kết quả `md5sum -c` phải báo `OK` trước khi upload lên Google Drive để gửi cho BTC)*.
