# Báo cáo Đánh giá và Mở rộng Phase 4 — Tích hợp vLLM

## 1. Tổng quan mục tiêu Phase 4

Phase 4 tập trung vào việc thay thế engine inference `mistralrs` cũ bằng `vLLM` phục vụ mô hình Qwen3.5 GGUF theo hợp đồng offline, mở rộng công cụ đánh giá có thể tái lập, khắc phục các cụm lỗi thường gặp khi sinh SQL, và chuẩn bị cho việc đánh giá trên tập development.

Toàn bộ công việc được thực hiện trên nhánh `codex/phase-4-evaluate-expand`, tách từ commit mới nhất của `main`.

---

## 2. Các thay đổi và thành phần đã triển khai

### Commit 1: `build(runtime): replace mistralrs with vllm`
- **Loại bỏ `mistralrs`**: Gỡ bỏ hoàn toàn dependency `mistralrs` và các cấu hình CUDA riêng khỏi `pyproject.toml`.
- **Thêm `vLLM` cho Linux**: Khai báo `vllm>=0.6.0; sys_platform == 'linux'` để hỗ trợ container Linux / WSL2 mà không phá vỡ môi trường phát triển / test trên Windows. Cập nhật và khóa `uv.lock`.
- **Cập nhật Dockerfile**: Chuyển sang base image chính thức `vllm/vllm-openai:v0.10.1.1`, cấu hình đường dẫn model mặc định `/models/qwen3.5-9b-q4/Qwen3.5-9B-Q4_K_M.gguf`.
- **Cập nhật tài liệu AGENTS.md**: Bổ sung hướng dẫn runtime vLLM, quy định offline inference, ngân sách GPU memory 3 GiB.

### Commit 2: `feat(generation): wire offline vllm planner`
- **Tạo adapter `VllmPlanner`**: Triển khai trong `src/datamate/generation/vllm_adapter.py`.
  - Hỗ trợ lazy loading `vllm` (`from vllm import LLM, SamplingParams`), cho phép unit test chạy thông suốt trên môi trường Windows mà không crash.
  - Greedy decoding (`temperature=0.0`, `max_tokens=512`) đảm bảo tính xác định (deterministic).
  - Prompt có cấu trúc rõ ràng: cung cấp question, business schema, business calendar, rules và yêu cầu sinh JSON duy nhất.
- **Tích hợp vào Pipeline và Runner**:
  - `src/datamate/application/runner.py` đọc cấu hình `DATAMATE_MODEL_PATH` và khởi tạo `VllmPlanner`.
  - `src/datamate/generation/__init__.py` xuất `VllmPlanner`.
  - Bộ unit test `tests/unit/generation/test_vllm_adapter.py` gồm 5 test cases kiểm thử prompt, lazy load, mock generation, và tích hợp với candidate pipeline.

### Commit 3: `feat(evaluation): record reproducible model scores`
- **Nâng cấp `scripts/evaluate_predictions.py`**:
  - Hỗ trợ cờ `--pilot-48`: lọc nhanh 48 câu development trong danh sách 60 câu representative để đo kiểm trước khi chạy toàn bộ 2.446 câu development.
  - Metadata tái lập mở rộng: lưu trữ `model_path`, `model_hash`, `vllm_version`, `prompt_hash`, `manifest_hash`, `git_commit`, `python_version`.
  - Thống kê độ trễ (latency summary): tính toán `mean_ms`, `p50_ms`, `p90_ms`, `max_ms` từ log chi tiết qua cờ `--logs`.
  - Phân tích chi tiết theo intent (`by_intent`): tự động phân loại intent (`aggregation`, `filtering`, `ranking`, `comparison`, `unanswerable`, `lookup`) để phát hiện cụm lỗi.
- **Kiểm thử scorer**: Bổ sung regression tests trong `tests/unit/evaluation/test_evaluation_cli.py`.

### Commit 4: `fix(agent): address development failure clusters`
- **Khắc phục cụm lỗi Markdown SQL code blocks**:
  - Khi model sinh SQL bọc trong ` ```sql ... ``` `, `CandidatePipeline._parse_plan` tự động bóc tách và trích xuất câu SQL nguyên bản.
- **Khắc phục cụm lỗi trailing semicolon**:
  - Tự động cắt bỏ dấu `;` ở cuối câu truy vấn trước khi chuyển cho DataFusion execution engine, tránh cú pháp lỗi.
- **Xử lý ứng viên `unanswerable` an toàn**:
  - Khi model phát hiện schema thiếu trường dữ liệu hoặc không đủ bằng chứng và sinh kế hoạch dạng `type: "unanswerable"`, pipeline xây dựng candidate typed answer `{"type": "unanswerable", "answer": None}`.
  - Verifier gắn trạng thái `abstain` với lý do `insufficient_evidence`, tránh ném ngoại lệ vô căn cứ.
- **Bổ sung Unit Tests**: 2 test cases mới trong `tests/unit/data/test_application_candidates.py` xác minh việc bóc tách markdown SQL và xử lý unanswerable candidate.

---

## 3. Trạng thái Môi trường và Giới hạn Runtime

### Trạng thái môi trường host
- **Hệ điều hành**: Windows 10 x64.
- **Phần cứng GPU**: NVIDIA GeForce RTX 4060 (8 GB VRAM), CUDA Driver 610.88, CUDA 13.3.
- **Tình trạng WSL/Docker daemon**: Host hiện tại chưa cài đặt hoàn chỉnh WSL2 hoặc Docker daemon. Vì vậy, việc chạy vLLM engine thật (yêu cầu nhân Linux) không thể thực hiện trực tiếp trên native Windows host này mà phải chạy trong container Linux Docker hoặc môi trường WSL2 của máy chủ đích/máy chấm.
- **Lazy loading & Mocking**: Nhờ thiết kế lazy loading trong `VllmPlanner`, toàn bộ mã nguồn trên Windows hoàn toàn độc lập với binary vLLM. Các bài test logic, pipeline, runner, candidate parsing và SQL cleaning đều chạy thành công trên Windows.

### Kết quả kiểm thử (Unit & Regression Tests)
- Chạy toàn bộ test suite (`uv run python -m unittest discover -s tests`):
  - **230 test cases PASS**.
  - **2 lỗi import legacy cũ** (`tests/legacy/test_business_sources.py` và `tests/legacy/test_deterministic.py`) do các module solver cũ đã xóa theo chủ đích từ Phase 3. Hai lỗi này được giữ nguyên cách ly, không gây ảnh hưởng đến production runtime.
  - Không có bất kỳ lỗi test mới nào phát sinh.

---

## 4. Đánh giá Gate Phase 4

| Tiêu chí Gate | Mức yêu cầu | Trạng thái | Ghi chú |
|---|---|---|---|
| **Thay thế engine** | Bỏ mistralrs, nạp vLLM Linux-only | **ĐẠT** | `pyproject.toml`, `uv.lock`, `Dockerfile` đã cập nhật. |
| **Adapter & Runner** | Bounded offline loop, lazy loading | **ĐẠT** | `VllmPlanner` đã nối vào `runner.py`, greedy decoding. |
| **Scorer metadata** | Hash, latency, pilot-48, intent | **ĐẠT** | `scripts/evaluate_predictions.py` mở rộng đầy đủ. |
| **Sửa cụm lỗi** | Markdown SQL, semicolon, unanswerable | **ĐẠT** | `CandidatePipeline` làm sạch SQL và chuyển unanswerable sang abstain an toàn. |
| **Gate kỹ thuật P4** | PA $\ge 0.10$, Coverage $\ge 0.50$ | **Sẵn sàng đo kiểm** | Sẵn sàng chạy trên container Linux có model weights. |
| **Nguyên tắc dữ liệu** | Không tune/fit trên holdout | **TUÂN THỦ** | Tập holdout (6 businesses / 12 câu representative) được đóng băng nghiêm ngặt. |
| **Trạng thái CI** | Remote CI workflow | **Unavailable** | Repo chưa có GitHub Actions workflow; kiểm tra chạy local qua `unittest`. |

---

## 5. Hướng dẫn Tái hiện và Đánh giá (Linux / Docker)

1. **Khởi chạy container Linux có GPU:**
   ```bash
   docker run --gpus all --rm -v $(pwd)/data:/data -v $(pwd)/result:/result -v $(pwd)/models:/models <image_name>
   ```

2. **Chạy inference trên tập development:**
   ```bash
   DATAMATE_MODEL_PATH=/models/qwen3.5-9b-q4/Qwen3.5-9B-Q4_K_M.gguf python -m datamate --data-dir /data --output-dir /result
   ```

3. **Chấm điểm reproducible:**
   ```bash
   python scripts/evaluate_predictions.py --predictions /result/submission.jsonl --logs /result/logs/predictions.jsonl --pilot-48
   ```
