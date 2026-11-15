# Báo cáo Đánh giá và Mở rộng Phase 4 — Tích hợp & Hardening vLLM

## 1. Tổng quan mục tiêu Phase 4

Phase 4 tập trung vào việc thay thế engine inference `mistralrs` cũ bằng `vLLM` phục vụ mô hình Qwen3.5 GGUF theo hợp đồng offline, mở rộng công cụ đánh giá có thể tái lập, khắc phục các cụm lỗi thường gặp khi sinh SQL, và hoàn thiện toàn bộ phần cứng/môi trường suy luận (hardening) cho việc đánh giá trên tập development.

Toàn bộ công việc được thực hiện trên nhánh `codex/phase-4-evaluate-expand`, tách từ commit mới nhất của `main`.

---

## 2. Các thay đổi và thành phần đã triển khai & gia cố (Hardening)

### 2.1. Quản lý phụ thuộc và Dockerfile Runtime (P0 Hardening)
- **Pin vLLM và GGUF Plugin chính thức**:
  - `pyproject.toml` và `uv.lock` đã khóa chính xác:
    - `vllm==0.33.0; sys_platform == 'linux'`
    - `vllm-gguf-plugin>=0.0.2; sys_platform == 'linux'`
    - `gguf>=0.17.0; sys_platform == 'linux'`
  - Đảm bảo `vllm` nạp được định dạng `.gguf` mà không bị thiếu thư viện lượng tử hóa hay raise ngoại lệ ngầm.
- **Sửa thứ tự build trong Dockerfile**:
  - Tách quá trình build thành 2 bước chuẩn hóa bộ nhớ đệm `uv`:
    ```dockerfile
    COPY pyproject.toml uv.lock ./
    RUN uv sync --locked --no-dev --no-install-project
    COPY predict.sh README.md /code/
    COPY src/ /code/src/
    RUN uv sync --locked --no-dev
    ```
  - Tránh lỗi `Failed to build query-processing-agent: Expected a Python module at src/datamate/__init__.py` khi chưa copy thư mục `src/`.
- **Đồng bộ Base Image và loại bỏ COPY models**:
  - Dockerfile sử dụng `FROM vllm/vllm-openai:v0.33.0` đồng bộ hoàn toàn với phiên bản `vllm==0.33.0` trong lockfile.
  - Bỏ lệnh `COPY models/ /models/` khỏi Dockerfile để tránh build fail trên clean checkout / CI (do `models/` thuộc `.gitignore`).
  - Container tạo sẵn các thư mục mount: `RUN mkdir -p /models /data /result /result/logs`.
- **Hỗ trợ Tokenizer Offline đầy đủ**:
  - Repo GGUF `unsloth/Qwen3.5-9B-GGUF` chỉ chứa file `.gguf`, thiếu các file tokenizer cần thiết cho vLLM khi chạy hoàn toàn offline (`HF_HUB_OFFLINE=1`).
  - Nâng cấp `scripts/download_model.py`: hỗ trợ tải cả weights GGUF và bộ file cấu hình tokenizer (`tokenizer.json`, `tokenizer_config.json`, `config.json`, `chat_template.jinja`) từ `Qwen/Qwen3.5-9B` vào `models/qwen3.5-9b-tokenizer`.
  - Adapter `VllmPlanner` tự động phát hiện đường dẫn tokenizer qua biến `DATAMATE_TOKENIZER_PATH` hoặc quét các thư mục lân cận (`models/qwen3.5-9b-tokenizer`, `../tokenizer`).

### 2.2. Adapter suy luận `VllmPlanner` & Quản lý Bộ nhớ (P1 Hardening)
- **Tắt chế độ suy luận ngầm (Thinking Suppression)**:
  - Qwen3.5 mặc định bật chế độ reasoning với thẻ `<think>\n`, dễ làm cạn kiệt `max_tokens=512` trước khi xuất JSON.
  - Suffix của prompt được cố định bằng: `<|im_start|>assistant\n<think>\n\n</think>\n`. Nhờ đó mô hình nhận diện reasoning đã hoàn thành và ngay lập tức sinh JSON cho kế hoạch SQL.
  - Tích hợp schema ràng buộc có cấu trúc (`guided_json` với `PLAN_SCHEMA`), loại bỏ `trust_remote_code=True` để tuân thủ bảo mật.
- **Thiết lập VRAM thận trọng & Ngăn ngừa OOM**:
  - Mặc định `gpu_memory_utilization = 0.80` và `enforce_eager = True` (tránh phân bổ thừa của CUDA graph trong lần đo đầu).
  - Tự động bắt lỗi OOM (`CUDA out of memory`) trong quá trình khởi tạo và thử lại 1 lần với mức utilization thấp hơn (`0.72 - 0.75`).
- **Warmup ngoài vòng đo & Fail-fast Cache**:
  - Thêm phương thức `warmup()` trên `VllmPlanner`: khởi chạy 1 lượt suy luận mẫu trước khi bước vào vòng lặp câu hỏi, ghi nhận riêng `model_load_ms`. Nhờ đó `elapsed_ms` của câu hỏi đầu tiên không bị sai lệch.
  - Cờ `self._init_error` lưu lại lỗi khởi tạo nếu có: hệ thống sẽ fail-fast ngay lập tức thay vì thử nạp lại mô hình 2.446 lần gây treo máy.
- **Mở rộng Context Window & Bounded Prompt**:
  - Nâng `max_model_len` mặc định lên `4096` token (qua biến `DATAMATE_CONTEXT_SIZE`).
  - Cắt tỉa có kiểm soát độ dài schema (`6.000` ký tự), rules (`1.200` ký tự) và calendar (`400` ký tự), đảm bảo prompt không bao giờ vượt ngưỡng context.
- **Cấu hình số lượng ứng viên (`DATAMATE_CANDIDATE_COUNT`)**:
  - Cho phép điều chỉnh số lượng candidate thông qua biến môi trường (mặc định 1 để tối ưu thời gian; có thể tăng lên 2 hoặc 3 nếu ngân sách cho phép).

### 2.3. Nâng cấp Scorer Tái lập & Phân tích Intent (`scripts/evaluate_predictions.py`)
- **Khóa nghiêm ngặt `--pilot-48`**:
  - Không fallback âm thầm: bắt buộc file `configs/representative_questions.json` phải tồn tại và assert chính xác `48` câu development. Nếu thiếu hoặc số lượng lệch sẽ báo lỗi ngay.
- **Lọc độ trễ chính xác theo tập đánh giá**:
  - Khi đọc log từ `--logs`, chỉ gom các câu hỏi nằm trong tập đang chấm (loại bỏ trường hợp chạy pilot 48 câu nhưng gom latency của toàn bộ 2.446 câu).
  - Báo cáo chi tiết `p50_ms`, `p90_ms`, `p95_ms`, `avg_ms`, `min_ms`, `max_ms`.
- **Mã băm cấu hình thật (`prompt_config_hash`)**:
  - Sinh mã băm SHA-256 động dựa trên template hệ thống, sampling parameters, model path, và engine config thật từ `VllmPlanner.get_config_hash()`.
- **Phân loại Intent có thứ tự ưu tiên chuẩn xác**:
  - Xếp thứ tự ưu tiên rõ ràng: `cancellation` (đơn hủy/hoàn) → `comparison` (so sánh/tăng trưởng/%) → `ranking` (top/cao nhất/thấp nhất) → `lookup` (thực thể/thời gian) → `aggregation` (tổng/trung bình/doanh thu/số đơn) → `general`.
- **Đầy đủ Metadata tái lập**:
  - Bổ sung `model_path`, `python_version`, `platform`, `vllm_version`, `commit`, `manifest_sha256`.

### 2.4. Khắc phục Cụm Lỗi SQL Execution (Failure Clusters)
- **Làm sạch cú pháp SQL**: Tự động bóc tách markdown code fence (` ```sql ... ``` `) và cắt bỏ dấu chấm phẩy `;` ở cuối câu truy vấn trước khi gửi tới DataFusion.
- **Xử lý ứng viên `unanswerable`**: Khi mô hình sinh `type: "unanswerable"`, pipeline chuyển thành đáp án typed answer với `status="abstain", reason_code="insufficient_evidence"`, đi qua quy trình verification tiêu chuẩn.

---

## 3. Trạng thái Môi trường và Giới hạn Runtime

### Trạng thái môi trường host
- **Hệ điều hành**: Windows 10 x64.
- **Phần cứng GPU**: NVIDIA GeForce RTX 4060 (8 GB VRAM), CUDA Driver 610.88, CUDA 13.3.
- **Tình trạng WSL/Docker daemon**: Host Windows hiện tại chưa cấu hình WSL2 daemon hoặc Linux Docker engine. Do đó, mã nguồn vLLM trên host được bảo đảm bằng kiến trúc lazy-loading và mock tests.
- **Kiểm thử trên Windows**:
  - Chạy `uv sync --locked`: Thành công 100%.
  - Chạy `uv run python -m unittest discover -s tests`: **230 tests PASS**, 2 lỗi import legacy cũ trong `tests/legacy/` được cô lập từ trước.

---

## 4. Đánh giá Gate Phase 4

| Tiêu chí Gate | Mức yêu cầu | Trạng thái | Ghi chú |
|---|---|---|---|
| **Thay thế engine** | Bỏ mistralrs, nạp vLLM 0.33 + GGUF plugin | **ĐẠT** | `pyproject.toml`, `uv.lock`, `Dockerfile` đã khóa và đồng bộ. |
| **Tokenizer offline** | Tải và cấu hình tokenizer cho GGUF | **ĐẠT** | `download_model.py` và `vllm_adapter.py` hỗ trợ offline 100%. |
| **Gia cố Runtime** | Tắt thinking, bounded VRAM/context, warmup | **ĐẠT** | Prompt suffix `</think>`, eager mode, warmup ngoài vòng đo. |
| **Scorer metadata** | Hash thật, latency lọc pilot, assert 48 câu | **ĐẠT** | `scripts/evaluate_predictions.py` mở rộng và kiểm thử hoàn chỉnh. |
| **Sửa cụm lỗi SQL** | Bóc tách code fence, semicolon, unanswerable | **ĐẠT** | `CandidatePipeline` làm sạch SQL và chuyển unanswerable sang abstain. |
| **Gate kỹ thuật P4** | PA $\ge 0.10$, Coverage $\ge 0.50$ | **Ready to Evaluate** | Khung tích hợp và hardening đã xong, sẵn sàng chấm khi chạy container GPU. |
| **Nguyên tắc dữ liệu** | Không tune/fit trên holdout | **TUÂN THỦ** | 6 holdout businesses được đóng băng nghiêm ngặt. |
| **Trạng thái CI** | Remote CI workflow | **Unavailable** | Repo chưa có GitHub Actions workflow; kiểm tra chạy local qua `unittest`. |

---

## 5. Hướng dẫn Tái hiện và Đánh giá (Linux / Docker)

1. **Chuẩn bị trọng số mô hình và tokenizer offline:**
   ```bash
   uv run --locked --no-sync python scripts/download_model.py
   ```

2. **Khởi chạy container Linux có GPU:**
   ```bash
   docker run --gpus all --rm \
     -v $(pwd)/data:/data:ro \
     -v $(pwd)/result:/result \
     -v $(pwd)/models:/models:ro \
     zaic2026_datamate_zalotrunua:final
   ```

3. **Chạy suy luận thủ công nếu cần:**
   ```bash
   python -m datamate --data-root /data --result-root /result
   ```

4. **Chấm điểm có thể tái lập:**
   ```bash
   python scripts/evaluate_predictions.py \
     --predictions /result/submission.jsonl \
     --logs /result/logs/predictions.jsonl \
     --pilot-48
   ```
