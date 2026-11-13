# Kiểm tra bàn giao Data Catalog

Tài liệu chốt phạm vi review của Người 1; đọc cùng [báo cáo handoff](data-catalog-handoff.md), [schema catalog](data-schema-catalog.md) và [acceptance criteria](plan/01-data-catalog.md). Đây là sản phẩm sẵn sàng **bàn giao để review**, chưa phải xác nhận hoàn tất toàn bộ D01–D05/P1.

## Đối chiếu acceptance criteria

| Tiêu chí của Người 1 | Bằng chứng | Kết luận |
|---|---|---|
| 1. Đủ 30/30 business, file/sheet/table khớp gói local hoặc có finding giải thích | 162 file, 30 README, 302 sheet Excel + 20 CSV business + 17 bảng SQLite = 339 nguồn; đối chiếu inventory từng business; khác biệt tên file Unicode/README có finding và mapping riêng | Đạt kiểm kê local; checksum gói chính thức chưa xác minh |
| 2. Nguồn của câu mẫu có header, grain, khóa nối đã xác minh | 339 header/schema được đọc trực tiếp; 335 grain verified, 4 needs_review; source map có 60 record, 22 ready, 28 ready with caveats, 10 needs_review | Chưa đạt vô điều kiện; không nâng trạng thái bốn bảng hỗn hợp |
| 3. Row count/date coverage tái lập, báo malformed/unparsed dates, null keys, duplicates, fan-out | source_quality.csv, date_review.json, findings.jsonl, validated_join_unions; toàn bộ 16.594 serial NgayBan của biz_111 được giải quyết bằng audit | Đạt kiểm tra kỹ thuật và báo cáo số đếm; policy filter/status/unit còn cần review. Raw row count không phải số giao dịch đã chuẩn hóa |
| 4. README conflicts và chưa rõ ghi riêng | schema catalog, findings.jsonl, grain_review, missing_evidence trong source contracts | Đã công khai khác biệt và giả định; chưa thay quyết định của lead |
| 5. Nguồn không đổi, Người 2 xác nhận dùng được cho trace | fingerprint 162 file; source refs/cột/join của 60 câu; catalog_validation.json | Fingerprint đạt; xác nhận Người 2/lead còn chờ |

D01 đã có kiểm kê. D02 đã review nhưng còn bốn nguồn mở. D03 đã có profiling/audit và cảnh báo, chưa duyệt mọi policy nghiệp vụ. D04 có 366 cặp nguồn và 109 quan hệ sau union partitions: 101 verified, 3 yêu cầu dedup dòng trong đơn, 5 có raw unmatched. D05 có gói tài liệu/source map để review, chưa nghiệm thu.

## Blocker phải giữ khi bàn giao

| Nguồn | Dòng mang nhãn tổng | Quyết định cần review |
|---|---:|---|
| biz_107/SoBanHang.xlsx#Sheet1 | 526 | Xác minh filter dòng giao dịch trước khi cộng tiền |
| biz_110/danh_sach_hoa_don.csv | 429 | Không coi 429 dòng null Mã bill là 429 đơn thiếu ID; không fill ID vào dòng tổng |
| biz_130/So_chi_tiet_ban_hang_1.xlsx#Sheet1 | 347 | Phân biệt tổng ngày/tháng và dòng hàng |
| biz_130/So_chi_tiet_ban_hang_2.xlsx#Sheet1 | 247 | Như trên; kiểm tra cả hai phần file |

Tổng **1.549** dòng; không xóa hoặc sửa nguồn. Sáu source contracts liên quan các bảng này cần review; bốn contract khác thiếu loại bằng chứng cần thiết (tồn kho, lịch sử thu tiền/công nợ, nhận xét nhân viên, địa chỉ khách). Không tự biến các blocker thành đáp án `unanswerable`.

Người 2 review đường dẫn/cột/grain/join và caveat của từng câu trong `question_source_map.json`. Lead/Người 5 review filter dòng tổng, dedup trong cùng đơn, alias trạng thái/đơn vị và policy serial CSV chỉ cho export đã audit. Ba join phân bổ lô ở biz_119/biz_123/biz_124 có fan-out raw; không SUM tổng đơn sau nối dòng hàng/thu tiền. Chi tiết số trước/sau nằm trong handoff và catalog.

## Kiểm tra cuối và tái lập

Kết quả thực tế của lượt kiểm tra cuối được lưu tại:

- `artifacts/data_prep/catalog_validation.json`: JSON strict, CSV schema, 30/339 coverage, source refs/header, fingerprint và kiểm tra Git.
- `artifacts/data_prep/catalog_tests.log`: toàn bộ unit/synthetic tests riêng Data Catalog.
- `artifacts/data_prep/handoff_repro_result.json`: so sánh sáu deliverable trước/sau replay; chỉ bỏ timestamp `review_provenance.generated_utc` khi so sánh catalog.

Kết quả đã chạy trên checkout này:

| Kiểm tra | Kết quả thực tế |
|---|---|
| Unit/synthetic tests riêng Data Catalog | 21/21 đạt, gồm regression CLI trên console cp1252 với tên file Unicode |
| JSON strict và CSV schema | Đạt; không duplicate JSON keys, CSV có 11.466 record thống kê |
| Coverage/source references | Đạt 30 business, 339 nguồn; đọc trực tiếp đủ 339 header/schema |
| Fingerprint | 162 file nguồn trước/sau khớp |
| Replay | 6/6 phép so sánh khớp; năm file phụ trợ giống byte, catalog giống nội dung ngoài timestamp được nêu |
| Tài liệu public-test | Nội dung giữ nguyên |
| git diff --check | Đạt |
| Bộ test chung của dự án | Không có kết quả pass; blocker scaffold vẫn tồn tại |

Không tuyên bố bộ test chung đạt: `src/datamate/__init__.py` vẫn thiếu. Không sửa scaffold hoặc môi trường thuộc Người 4.

Các lệnh đã dùng trên checkout hiện tại, với `uv` và `.venv/Scripts/python.exe` sẵn có:

```powershell
cd D:\Code\query-processing-agent
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'
if (!(Test-Path artifacts/data_prep/data_catalog.initial.json)) {
    throw 'Thiếu baseline raw; cần build trước khi chạy incremental review.'
}
uv run --no-project --python .venv/Scripts/python.exe python scripts/review_data_catalog.py --write-docs
uv run --no-project --python .venv/Scripts/python.exe python scripts/validate_data_catalog.py --write-report
git diff --check
```

Validator tự chạy toàn bộ tests theo pattern `*catalog*.py`. Có thể chạy riêng để đọc log trực tiếp:

```powershell
uv run --no-project --python .venv/Scripts/python.exe python -m unittest discover -s tests -p '*catalog*.py' -v
```

Nếu chưa có artifact raw ban đầu, chạy `scripts/build_data_catalog.py --write-docs` bằng cùng cách gọi uv trước bước review. **Không** dùng một catalog đã review làm baseline raw mới. Replay hiện tại dùng `data_catalog.initial.json` bất biến và dừng khi fingerprint nguồn không khớp.

Trên máy khác, catalog có `source_root` tuyệt đối nên không bảo đảm chạy trực tiếp từ bản copy. Để review, có thể đọc artifact nhận được ở một thư mục riêng. Để tái tạo, dùng checkout/thư mục artifact mới, train chính thức có sẵn trên máy đó, rồi chạy build → review → validation để ghi source_root đúng. Không sửa artifact đã đối chiếu SHA-256 hoặc đổi tên dữ liệu nguồn chỉ để khớp đường dẫn của máy này.

## Git: tracked, untracked và ignored

Repo HEAD lúc kiểm tra: `53e8b076799ac20d8e50723a1d493c8c9ac35108`. Đây chưa phải revision chứa toàn bộ sản phẩm bàn giao.

| File/nhóm | Trạng thái |
|---|---|
| docs/data-schema-catalog.md | Đã tracked; đang modified |
| docs/data-catalog-handoff.md | Untracked, không ignored |
| docs/data-catalog-delivery.md | Untracked, không ignored |
| scripts/build_data_catalog.py | Untracked, không ignored; có từ lượt trước |
| scripts/review_data_catalog.py | Untracked, không ignored |
| scripts/validate_data_catalog.py | Untracked, không ignored |
| tests/test_data_catalog.py | Untracked, không ignored; có từ lượt trước |
| tests/test_catalog_review.py | Untracked, không ignored |
| artifacts/data_prep/* | Ignored bởi `.gitignore:6`, quy tắc `/artifacts/*`; chưa tracked |
| train/* | Ignored bởi `.gitignore:3`, quy tắc `/train/`; không đưa vào gói bàn giao |

`??` không có nghĩa là ignored. `git diff` thông thường không chứa nội dung các file untracked; chỉ gửi patch tracked hiện tại sẽ thiếu scripts/tests/handoff. Chưa commit, push hay tạo PR, nên nhóm chưa thể lấy đủ sản phẩm này bằng checkout remote.

## Chia sẻ riêng artifact

Đề xuất dùng thư mục Drive/SharePoint hoặc nơi lưu trữ nội bộ đã giới hạn thành viên nhóm; gửi link và SHA-256 của gói trong kênh nhóm. Đây là đề xuất, chưa tạo ZIP hoặc upload/gửi link.

Gói artifact dùng allowlist, không nén toàn bộ repository hoặc train:

- data_catalog.json
- data_catalog.initial.json — cần cho incremental replay, chỉ chứa catalog/statistics/fingerprints, không phải train gốc
- source_quality.csv
- question_source_map.json
- date_review.json
- findings.jsonl
- unmatched_name_review.json
- catalog_validation.json
- catalog_tests.log
- handoff_repro_result.json

Không kèm train/, answers.jsonl, questions.jsonl, workbook/CSV/SQLite nguồn, models/, cache hoặc log debug không cần thiết. Không dùng `git add -f`, Git LFS hoặc GitHub Release để vượt quy tắc không commit artifacts.

Có thể tạo ZIP từ **đúng allowlist** ở trên, đối chiếu danh sách thành viên ZIP rồi tính `Get-FileHash -Algorithm SHA256`. Người nhận kiểm tra SHA-256 trước khi giải nén vào thư mục artifact tham khảo. Baseline phải đi cùng các artifact nếu muốn replay incremental trên cùng cấu trúc máy.

Vì scripts/docs/tests vẫn untracked và chưa push, cần gửi thêm **gói mã nguồn Data Catalog riêng**, giữ cấu trúc đường dẫn của tám file không ignored trong bảng Git. Ghi kèm HEAD nền và checksum các file gửi. Mỗi người tự chuẩn bị train từ nguồn chính thức; không chuyển train thông qua gói này. Sau khi được yêu cầu riêng mới thực hiện commit/push hoặc chia sẻ lên dịch vụ ngoài.

## Tin nhắn đề xuất gửi nhóm

> Data Catalog đã sẵn sàng bàn giao để review: đủ 30 business, 339 nguồn, 339 header/schema đã đối chiếu. Grain: 335 verified, 4 needs_review; đã xử lý 16.594 ngày serial ở biz_111, còn 0 unresolved trong cột NgayBan.
>
> Có catalog JSON, quality CSV, source map cho 60 câu, schema catalog và báo cáo handoff. Source contracts: 22 ready, 28 ready with caveats, 10 cần review. Điểm cần chốt là 1.549 dòng nhãn tổng ở biz_107/biz_110/biz_130, dedup/fan-out và policy alias/status/unit. Nhờ Người 2 review khả năng truy vết; lead/Người 5 duyệt các policy và acceptance.
>
> Validation và tests riêng đạt theo log đính kèm; fingerprint train không đổi. Test chung vẫn bị blocker thiếu package datamate. Artifact sẽ chia sẻ riêng theo allowlist, không đưa train lên GitHub. Chưa commit/push/PR; chưa coi D05/P1 đã nghiệm thu.
