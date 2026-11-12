# Kế hoạch rebuild DataMate — trang điều phối

## Mục tiêu

Xây DataMate thành **agentic RAG kết hợp truy vấn dữ liệu có kiểm soát**: lấy schema, README/rulebook, entity evidence và dữ liệu liên quan; model lập kế hoạch; công cụ thực hiện phép tính; verifier kiểm tra provenance/bằng chứng; hệ thống trả typed answer hoặc từ chối có lý do.

Trong giai đoạn hiện tại, nhóm hoàn tất data catalog và trace câu mẫu trước khi khóa model, retrieval strategy hoặc runtime. Loader chỉ đọc nguồn; kết quả phải truy vết được; inference chạy offline. Dùng train labels cho phát triển. Public test chỉ hỗ trợ kiểm tra cấu trúc, không dùng labels/scores để chọn thiết kế.

## Phân công team

| Người | Nhóm việc | Chủ sở hữu tài liệu |
|---|---|---|
| 1 | Data catalog và chất lượng 30 train business | [01-data-catalog.md](01-data-catalog.md) |
| 2 | Trace 60 câu từ input đến đáp án hoặc blocker | [02-question-tracing.md](02-question-tracing.md) |
| 3 | Agentic RAG, tool boundary và inference contract | [03-agentic-rag-inference.md](03-agentic-rag-inference.md) |
| 4 | Môi trường, loader, baseline và runtime | [04-baseline-runtime.md](04-baseline-runtime.md) |
| 5 — Lead | Đánh giá, review, tích hợp và bàn giao | [05-evaluation-integration.md](05-evaluation-integration.md) |

## Checklist lead trước kickoff

| ID | Chuẩn bị | Hoàn tất khi |
|---|---|---|
| L01 | Ghi trạng thái repo và giới hạn hiện tại | Mọi người biết catalog là bản quét ban đầu; solver cũ đã xóa; scripts/tests cũ có thể import package đã xóa nên chưa là baseline chạy được. |
| L02 | Chốt phạm vi dữ liệu | Dùng 30 train businesses, 60 câu mẫu và manifest đã kiểm tra; public test chỉ kiểm tra cấu trúc. |
| L03 | Ghi mức độ tiếp xúc holdout | 12/60 câu thuộc holdout và labels đã xuất hiện trong sample JSON; báo cáo chúng là exploratory, không độc lập. |
| L04 | Chốt mẫu bàn giao | Catalog, trace, issue, execution record và evaluation report có trường dùng chung/provenance. |
| L05 | Chuẩn bị 3 ví dụ theo định dạng | Một catalog entry và trace nhỏ cho CSV `biz_101`, Excel `biz_102`, SQLite `biz_123`; thống nhất cùng Người 1/2, không thay họ làm hết. |
| L06 | Chốt owner/reviewer/integration | Mỗi deliverable có chủ, reviewer, artifact location, test command và cách báo blocker. |

L01–L04 và L06 xong trước kickoff; L05 được review trong buổi bắt đầu. Nếu môi trường không cài/chạy được, giao Người 4 task preflight và ghi blocker/stack trace trước khi phần việc khác phụ thuộc vào đó.

## Thứ tự và gates

| Phase | Công việc và song song | Gate để chuyển bước |
|---|---|---|
| P0 — Lead prep | Hoàn checklist L01–L06; Người 4 có thể preflight môi trường | Phạm vi, ownership, mẫu record và blocker đã rõ |
| P1 — Data discovery | Người 1 xác minh 30 business; Người 2 truy trace 60 câu; Người 3 soạn khung contract; Người 4 kiểm tra môi trường/synthetic path; Người 5 review scorer và findings | Catalog 30/30 có trạng thái; 60 trace có source/calculation hoặc blocker; sai lệch có nguyên nhân; nguồn không đổi |
| P2 — Inference design | Người 3 so sánh retrieval/plan/tool contracts trên trace; Người 1/2 xác nhận grounding; Người 4 xác nhận khả thi; Người 5 chốt tiêu chí chấm | Contract v0 có ví dụ success/failure/insufficient evidence, được team review và version hóa |
| P3 — Baseline runtime | Người 4 tích hợp theo contract; Người 3 hỗ trợ; Người 1/2 đối chiếu nguồn; Người 5 chấm ở cuối phase | Một lát cắt end-to-end chạy được; answer/log contract hợp lệ; lỗi tái hiện được |
| P4 — Evaluate/expand | Cả nhóm sửa lỗi theo báo cáo; Người 5 quản lý tích hợp; mở rộng intent/business theo kết quả | Scorer tái lập, split đúng, acceptance đạt, giới hạn còn lại được ghi |
| P5 — Freeze/handoff | Kiểm tra offline/Docker, lệnh chạy và tài liệu; chạy holdout sau code/config freeze theo protocol | Gói tuân thủ submission contract và kết quả được báo kèm giới hạn holdout đã tiếp xúc |

**Kiểm thử:** theo lựa chọn của lead, kiểm thử tập trung cuối mỗi phase. Trong phase, mỗi task ghi scenario và expected result. Tài liệu-only phase dùng review chéo và `git diff --check`; code phase dùng unit/integration phù hợp, cuối phase chạy acceptance. Repo hiện không có CI workflow; không báo CI pass khi chưa có pipeline.

**Holdout:** manifest hiện có 24 development và 6 holdout business. Bộ mẫu 60 câu gồm 48 development và 12 holdout. Nhóm vẫn truy vết đủ 60 theo quyết định của lead; các câu holdout là exploratory và không được dùng để tune model/prompt/threshold hoặc báo cáo đánh giá độc lập. Giữ manifest, phân nhóm và caveat trong mọi báo cáo.

## Quy tắc tích hợp

- Mỗi người sở hữu file giao việc tương ứng và đầu ra của họ; lead giữ `rebuild.md`, templates/decision log và quyền pass/fail gate.
- Catalog là nguồn tên/schema; trace chỉ tham chiếu catalog; inference contract chỉ tham chiếu field/source refs đã xác minh; runtime cùng contract version; evaluation ghi version/commit/manifest.
- Artifact chi tiết và experiment outputs ở `artifacts/` local; không commit train/public-test data, model weights hoặc raw transaction rows.
- Mỗi task là một thay đổi reviewable. Stage explicit paths, xem staged diff và chạy `git diff --cached --check` trước commit. Đợt tài liệu này chia ba commit: data catalog/trace; inference/runtime; evaluation/hub.
- Làm trên `main`, giữ các commit local trong lúc soát chéo, push một lần sau khi cả bộ tài liệu và kiểm tra cuối đạt.

## Trạng thái và đầu vào hiện có

- `configs/representative_questions.json`: 60 câu, hai câu mỗi business; gồm 12 holdout exploratory.
- `docs/data-inventory.md` và `docs/data-schema-catalog.md`: thống kê và schema scan sơ bộ; header workbook/row counts/date coverage cần xác minh theo task Người 1.
- `configs/splits/seed_2026.json`: manifest business-level làm source of truth; không thay bằng split theo câu.
- Source solver cũ đã được dọn khỏi `src/`; README, rules, data, setup/download scripts và manifest được giữ lại. Kiểm tra/tests cũ cần được preflight sau khi package scaffold mới có.
- Chưa chốt model, vector index, prompt, inference schema, tool loop hay kiến trúc runtime. Những quyết định này thuộc P2 và cần dựa trên P1.
