"""Validate catalog artifacts, physical source references and unchanged hashes."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import re

SPEC = importlib.util.spec_from_file_location("catalog_review", Path(__file__).with_name("review_data_catalog.py"))
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)
base, ROOT = review.base, review.ROOT
QUALITY_COLUMNS = ["business_id", "source_ref", "column", "metric", "value", "denominator", "status"]


def validate(output):
    catalog = review.load_json(output / "data_catalog.json")
    businesses = catalog["businesses"]
    ids = [b["business_id"] for b in businesses]
    assert len(ids) == len(set(ids)) == 30 and set(ids) == {f"biz_{i}" for i in range(101, 131)}
    tables = {t["source_ref"]: t for b in businesses for t in b["tables"]}
    assert len(tables) == sum(len(b["tables"]) for b in businesses) == 339
    train = Path(catalog["source_root"])
    before = base.snapshot(train)
    assert before == catalog["source_fingerprints"], "Source fingerprints differ from initial catalog"
    assert len(before) == 162
    assert catalog["archive_checksum"].startswith("not_verified")
    header_checks = 0
    for business in businesses:
        files = defaultdict(list)
        assert (train / business["readme"]).is_file()
        for table in business["tables"]:
            suffix = "#" + table["sheet_or_table"] if table["sheet_or_table"] else ""
            assert table["source_ref"] == business["business_id"] + "/" + table["file"] + suffix
            path = (train / "data" / business["business_id"] / table["file"]).resolve()
            assert path.is_file() and path.is_relative_to((train / "data" / business["business_id"]).resolve())
            files[table["file"]].append(table)
            assert len({c["name"] for c in table["columns"]}) == len(table["columns"])
            assert table["grain_status"] != "verified" or table.get("grain_review") or table.get("grain_evidence")
            for col in table["columns"]:
                assert 0 <= col["blank_or_null"] <= table["data_rows"]
                if "date_profile" in col:
                    p = col["date_profile"]
                    assert p["parsed"] + p["invalid"] + col["blank_or_null"] == table["data_rows"]
            for key in table["reviewed_keys"].values():
                assert set(key["columns"]).issubset({c["name"] for c in table["columns"]})
                assert 0 <= key["distinct"] <= table["data_rows"] - key["null_rows"]
        for filename, grouped in files.items():
            targets = {t["sheet_or_table"]: t for t in grouped}
            observed = set()
            for sheet, rows, sql_columns in base.source_tables(train / "data" / business["business_id"] / filename):
                assert sheet in targets
                table = targets[sheet]
                columns = [c["name"] for c in table["columns"]]
                if sql_columns is not None:
                    assert columns == sql_columns
                else:
                    actual = next(row for physical, row in rows if physical == table["header_row_1based"])
                    assert list(map(str, actual)) == columns, table["source_ref"]
                observed.add(sheet)
                header_checks += 1
            assert observed == set(targets)
        for edge in business["validated_join_edges"]:
            assert edge["left"] in tables and edge["right"] in tables
            left, right = tables[edge["left"]], tables[edge["right"]]
            assert set(edge["left_columns"]).issubset({c["name"] for c in left["columns"]})
            assert set(edge["right_columns"]).issubset({c["name"] for c in right["columns"]})
            assert edge["left_matched_rows"] + edge["left_unmatched_non_null_rows"] + edge["left_null_rows"] == edge["left_rows"]
            assert edge["right_matched_rows"] + edge["right_unmatched_non_null_rows"] + edge["right_null_rows"] == edge["right_rows"]
            assert edge["left_join_rows"] == edge["inner_join_rows"] + edge["left_rows"] - edge["left_matched_rows"]
        for edge in business["validated_join_unions"]:
            assert set(edge["left_sources"] + edge["right_sources"]).issubset(tables)
            assert edge["left_rows"] == sum(tables[r]["data_rows"] for r in edge["left_sources"])
            assert edge["right_rows"] == sum(tables[r]["data_rows"] for r in edge["right_sources"])
            assert edge["left_matched_rows"] + edge["left_unmatched_non_null_rows"] + edge["left_null_rows"] == edge["left_rows"]
            assert edge["right_matched_rows"] + edge["right_unmatched_non_null_rows"] + edge["right_null_rows"] == edge["right_rows"]
            assert edge["left_join_rows"] == edge["inner_join_rows"] + edge["left_rows"] - edge["left_matched_rows"]
    seen_metrics, quality_refs = set(), set()
    with (output / "source_quality.csv").open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == QUALITY_COLUMNS
        for row in reader:
            assert set(row) == set(QUALITY_COLUMNS) and None not in row and all(v is not None for v in row.values())
            assert row["source_ref"] in tables
            table = tables[row["source_ref"]]
            assert row["business_id"] == row["source_ref"].split("/", 1)[0]
            key = tuple(row[n] for n in ("business_id", "source_ref", "column", "metric"))
            assert key not in seen_metrics, key
            seen_metrics.add(key)
            quality_refs.add(row["source_ref"])
            assert int(row["denominator"]) >= 0
            if row["metric"] == "data_rows":
                assert int(row["value"]) == table["data_rows"]
            elif row["metric"] in ("summary_label_rows", "summary_rows_without_order_id"):
                assert int(row["value"]) == table["row_kind_review"][row["metric"]]
            elif row["metric"] == "blank_or_null":
                col = next(c for c in table["columns"] if c["name"] == row["column"])
                assert int(row["value"]) == col["blank_or_null"]
            elif row["metric"].startswith("date_"):
                col = next(c for c in table["columns"] if c["name"] == row["column"])
                value = col["date_profile"][row["metric"][5:]]
                assert row["value"] == ("" if value is None else str(value))
    assert quality_refs == set(tables)
    source_map = review.load_json(output / "question_source_map.json")
    samples = review.load_json(ROOT / "configs/representative_questions.json")["questions"]
    train_questions = {}
    with (train / "questions.jsonl").open(encoding="utf-8-sig") as stream:
        for line in stream:
            if line.strip():
                question = json.loads(line, object_pairs_hook=review.strict_pairs)
                assert question["id"] not in train_questions
                train_questions[question["id"]] = question
    assert len(source_map) == len({q["question_id"] for q in source_map}) == 60
    assert {q["question_id"] for q in source_map} == {q["id"] for q in samples}
    for question in source_map:
        sample = next(q for q in samples if q["id"] == question["question_id"])
        actual = train_questions[question["question_id"]]
        assert all(sample[k] == actual[k] for k in ("business_id", "as_of_date", "question"))
        assert sample["business_id"] == question["business_id"]
        assert sample["as_of_date"] == question["as_of_date"]
        approved_ids = {e["id"] for b in businesses for e in b["validated_join_unions"]}
        assert set(question["join_edges"]).issubset(approved_ids)
        folded_question = review.base.fold(sample["question"])
        asks_product_group = "nhom" in folded_question and "khach" not in folded_question and "than thiet" not in folded_question
        asks_ingredient = "hoat chat" in folded_question
        if asks_product_group or asks_ingredient:
            roles = {tables[ref]["logical_role"] for ref in question["source_refs"]}
            assert "products" in roles, f"{question['question_id']} missing product master source"
            product_edge = any(
                {"sales_lines", "products"}.issubset(set(e["semantic_relation"].split(" -> ")))
                for b in businesses for e in b["validated_join_unions"]
                if e["id"] in question["join_edges"]
            )
            assert product_edge, f"{question['question_id']} missing approved sales-to-product join"
        for ref, columns in question["source_columns"].items():
            assert ref in tables and set(columns).issubset({c["name"] for c in tables[ref]["columns"]})
    assert catalog["review_provenance"]["script_sha256"] == base.digest(Path(__file__).with_name("review_data_catalog.py"))
    assert catalog["review_provenance"]["base_artifact_sha256"] == base.digest(output / "data_catalog.initial.json")
    initial_public = subprocess.check_output(["git", "show", "HEAD:docs/data-schema-catalog.md"], cwd=ROOT).decode("utf-8").split("## public_test", 1)[1]
    current_doc = (ROOT / "docs/data-schema-catalog.md").read_text(encoding="utf-8")
    assert initial_public.strip() == current_doc.split("## public_test", 1)[1].strip()
    assert before == base.snapshot(train), "Source changed during validation"
    whitespace = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True)
    assert whitespace.returncode == 0, whitespace.stdout + whitespace.stderr
    test_command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "*catalog*.py", "-v"]
    test_run = subprocess.run(test_command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (output / "catalog_tests.log").write_text(test_run.stdout + test_run.stderr, encoding="utf-8")
    assert test_run.returncode == 0, test_run.stderr
    test_count = re.search(r"Ran (\d+) tests?", test_run.stderr)
    return {"status": "passed", "businesses": 30, "tables": 339, "physical_header_checks": header_checks,
            "quality_schema": QUALITY_COLUMNS, "quality_records": len(seen_metrics), "question_source_records": 60,
            "strict_json_no_duplicate_keys": True, "source_refs_reachable": True,
            "fingerprints_before_after_match": True, "source_file_count": len(before), "public_test_document_unchanged": True,
            "synthetic_tests": {"status": "passed", "count": int(test_count[1]) if test_count else None, "log": "artifacts/data_prep/catalog_tests.log"},
            "git_diff_check": "passed",
            "official_archive_checksum": "not_verified", "review_acceptance": "Person 2 / lead pending"}


def handoff(catalog, validation):
    tables = [t for b in catalog["businesses"] for t in b["tables"]]
    counts = Counter(t["grain_status"] for t in tables)
    pairs = [e for b in catalog["businesses"] for e in b["validated_join_edges"]]
    edges = [e for b in catalog["businesses"] for e in b["validated_join_unions"]]
    joins = Counter(e["status"] for e in edges)
    source_map = catalog["question_source_map"]
    original = catalog["review_provenance"]["initial_grains_needs_review"]
    git_state = subprocess.check_output(["git", "status", "--short"], cwd=ROOT).decode("utf-8").strip()
    lines = ["# Bàn giao Data Catalog D01–D05", "", "Báo cáo kỹ thuật dựa trên train local; chưa thay thế xác nhận nghiệm thu của Người 2/lead.", "",
             "## Kết quả và coverage", "", "| Hạng mục | Kết quả |", "|---|---|",
             "| D01 | Đủ 30 business, 30 README, 162 file; 339 nguồn bảng, kiểm kê tái sử dụng từ lượt trước |",
             f"| D02 | Grain verified {counts['verified']}/339 ({counts['verified']/339:.2%}); needs_review {counts['needs_review']}/339 ({counts['needs_review']/339:.2%}); đã review lại {original} nguồn mở |",
             "| D03 | Profiling raw có số đếm; date audit riêng bên dưới; alias trạng thái/đơn vị chưa phải mapping runtime được duyệt |",
             f"| D04 | {len(pairs)} cặp nguồn và {len(edges)} quan hệ sau union partitions; trạng thái union: {dict(joins)}; không dùng mọi candidate chung khóa |",
             f"| D05 | Có 60 source contracts, {dict(Counter(q['status'] for q in source_map))}; chưa phải 60 trace tính đáp án; chờ Người 2/lead review |", "",
             "`verified` của bảng chỉ có nghĩa header + grain có bằng chứng; không có nghĩa mọi phép tính hay dữ liệu sạch. Header 339/339 được validator đọc lại từ CSV/OOXML/SQLite schema.", "",
             "## Ngày biz_111", ""]
    for report in catalog["date_reviews"]:
        lines += [f"Nguồn `{report['source_ref']}`, cột `{report['column']}`. Phân loại: `{report['formats']}`.",
                  f"Epoch duy nhất thỏa kiểm tra: `{report['confirmed_epoch']}`. Giải quyết {report['resolved']} giá trị; unresolved {report['unresolved']}.",
                  "```json", json.dumps(report["epoch_comparison"], ensure_ascii=False, indent=2), "```",
                  "Bằng chứng: README cutoff, ngày rõ ràng hai phía của từng serial, và ngày thu tiền theo mã đơn từ nguồn độc lập. Không suy ngày đơn bằng ngày thu tiền; khoản thu khác ngày là hợp lệ với công nợ. Scalar parser vẫn từ chối numeric string khi thiếu bằng chứng.", ""]
    lines += ["## Việc chưa hoàn tất và quyết định cần lead", "",
              "- Người 2 xác nhận source contracts đủ cho trace và sửa lựa chọn nguồn nếu cách hiểu câu hỏi khác. Không đưa gold vào catalog/retrieval.",
              "- Lead duyệt policy serial CSV chỉ áp cho export đã audit; bằng chứng ngữ cảnh không bảo đảm file khác luôn sắp xếp theo ngày.",
              "- Duyệt mapping trạng thái như Không giao được, Đang xử lý, Chờ giao; không âm thầm coi là hoàn thành/huỷ.",
              "- Xác nhận xử lý grouped blanks và dedup trong cùng đơn theo rulebook §8; không dedup sổ không có đơn.",
              "- Không suy lịch sử tồn/công nợ từ snapshot cuối kỳ. Tên không unique hoặc thiếu khóa phải giữ blocker.",
              "- Môi trường uv sync --locked/test chung vẫn bị thiếu src/datamate/__init__.py; thuộc preflight Người 4, không sửa trong phần việc này.",
              "- Checksum gói chính thức chưa xác minh; fingerprint chỉ chứng minh nguồn local không đổi.", "",
              "## Source contracts còn cần review", "", "| Question ID | Business | Lý do |", "|---|---|---|"]
    for question in source_map:
        if question["status"] == "needs_review":
            detail = "; ".join(question["missing_evidence"] + question["unresolved_grain_refs"] + question["unresolved_join_edges"])
            lines += [f"| `{question['question_id']}` | {question['business_id']} | {detail} |"]
    lines += ["", "Source contract ready chỉ xác nhận đường dẫn/cột/grain/quan hệ nguồn; không xác nhận đủ evidence tại ngày hỏi hoặc đúng đáp án. `with_caveats` yêu cầu xử lý quality được nêu trong từng record.", "",
              "## Nguồn còn needs_review", "", "| Source ref | Grain/Blocker |", "|---|---|"]
    for table in tables:
        if table["grain_status"] != "verified":
            lines += [f"| `{table['source_ref']}` | {table['grain_review'].get('blocker', table['grain'])} |"]
    if not counts["needs_review"]:
        lines += ["", "Không còn grain unresolved trong 339 nguồn local. Việc này không xác nhận khóa sạch, không thêm line ID cho nguồn đơn–lô, và không thay thế review của team."]
    lines += ["", "## Vấn đề chất lượng cần chú ý", "",
              f"Có {sum(bool(t['exact_duplicate_excess_rows']) for t in tables)} nguồn có dòng raw giống nhau; xem số đếm riêng, không gọi mọi trường hợp là lỗi.",
              "Fan-out hợp lệ một-nhiều vẫn gây sai số nếu cộng tổng đơn. Payment phải aggregate theo đơn trước; phân bổ lô phải nối (đơn, dòng), không nối đơn đơn thuần.",
              "Phân bổ đơn–lô không có khóa dòng (biz_121/biz_122) được mô tả riêng; không áp quy tắc join theo line ID không tồn tại.",
              "Lookup sản phẩm–đơn vị chỉ liệt kê đơn vị lớn: unmatched cần kiểm chứng đơn vị cơ bản, không tự loại giao dịch. Khóa raw null phải được báo riêng trước mọi fill nhóm.", "",
              "| Nguồn có nhãn tổng, cần duyệt filter | Số dòng | Trong đó không có mã đơn |", "|---|---:|---:|"]
    for table in tables:
        if table.get("row_kind_review"):
            audit = table["row_kind_review"]
            lines += [f"| `{table['source_ref']}` | {audit['summary_label_rows']} | {audit['summary_rows_without_order_id']} |"]
    total_summaries = sum(t.get("row_kind_review", {}).get("summary_label_rows", 0) for t in tables)
    lines += ["", f"Tổng **{total_summaries:,}** dòng mang nhãn tổng trong bốn nguồn trên (dấu phẩy phân tách hàng nghìn).",
              "Các dòng này vẫn nằm trong raw row count và dữ liệu nguồn, không bị tự động xóa. Grain được giữ needs_review cho đến khi xác minh bộ lọc dòng giao dịch.", "",
              "| Nguồn đơn có khóa null | Cột | Số dòng |", "|---|---|---|"]
    for table in tables:
        key = table["reviewed_keys"].get("order")
        if table["logical_role"] == "orders" and key and key["null_rows"]:
            lines += [f"| `{table['source_ref']}` | {' + '.join(key['columns'])} | {key['null_rows']} |"]
    lines += ["", "| Union relation có fan-out | Matched left | Inner join rows | Hệ số |", "|---|---:|---:|---:|"]
    for edge in edges:
        if edge["fanout_on_matched_left"] and edge["fanout_on_matched_left"] > 1:
            lines += [f"| `{edge['id']}` | {edge['left_matched_rows']} | {edge['inner_join_rows']} | {edge['fanout_on_matched_left']:.6f} |"]
    lines += ["", "| Name join | Raw unmatched | Chuẩn hóa khớp thêm | Còn unmatched | Collision ở danh mục |", "|---|---:|---:|---:|---:|"]
    for edge in edges:
        audit = edge.get("name_normalization_review")
        if audit and audit["raw_unmatched_rows"]:
            lines += [f"| `{edge['id']}` | {audit['raw_unmatched_rows']} | {audit['additional_matches']} | {audit['remaining_unmatched_rows']} | {audit['right_normalized_key_collisions']} |"]
    lines += ["", "Chuẩn hóa chỉ là lookup trong memory theo rulebook §8: chữ thường, bỏ dấu, gộp khoảng trắng; giữ chữ/số/dấu câu. Chỉ cho phép khi danh mục không collision; không fuzzy-match hoặc sửa tên nguồn.", "",
              "## Source refs bàn giao Người 2", "",
              "Chi tiết 60 câu và columns/edges nằm trong `artifacts/data_prep/question_source_map.json`; đây là source handoff, không viết đè question_trace của Người 2.", "",
              "| Business | Các source refs quan trọng |", "|---|---|"]
    for bid in ("biz_101", "biz_102", "biz_111", "biz_123", "biz_124", "biz_128"):
        selected = sorted({ref for q in source_map if q["business_id"] == bid for ref in q["source_refs"]})
        lines += [f"| {bid} | " + "<br>".join(f"`{ref}`" for ref in selected) + " |"]
    lines += ["", "## Tái lập", "", "Không cần quét lại D01 nếu fingerprints còn khớp:", "", "```powershell",
              "$env:UV_CACHE_DIR = Join-Path (Get-Location) '.uv-cache'",
              "uv run --no-project --python .venv/Scripts/python.exe python scripts/review_data_catalog.py --write-docs",
              "uv run --no-project --python .venv/Scripts/python.exe python -m unittest discover -s tests -p '*catalog*.py' -v",
              "uv run --no-project --python .venv/Scripts/python.exe python scripts/validate_data_catalog.py --write-report",
              "git diff --check", "```", "",
              "Nếu chưa có artifact ban đầu, chạy build_data_catalog.py trước. Review giữ data_catalog.initial.json làm baseline bất biến; nếu nguồn khác fingerprint thì dừng, không âm thầm tái sử dụng số cũ.", "",
              "## Validation", "", "```json", json.dumps(validation, ensure_ascii=False, indent=2), "```", "",
              "Synthetic tests kiểm tra serial có/không đủ bằng chứng, sai epoch/ngày, duplicate JSON keys, bảng không liên quan chung khóa, header/OOXML/duration, SQLite handle và source fingerprint.",
              "Lỗi console Unicode cũ được tránh bằng JSON ensure_ascii khi log; validator mở được tên file/sheet thật. Hủy/hủy là hai key JSON hợp lệ khác hoa thường; không dùng PowerShell ConvertFrom-Json để kết luận duplicate keys.", "",
              "## File và Git", "", "Phạm vi tạo/sửa: scripts/build_data_catalog.py (render catalog), scripts/review_data_catalog.py, scripts/validate_data_catalog.py; tests/*catalog*.py; docs/data-schema-catalog.md; báo cáo này. Artifact chi tiết ở artifacts/data_prep/ và vẫn gitignore.",
              "Không sửa train, không sửa package/runtime/trace của thành viên khác, không commit/push.", "", "Git status ghi trước khi xuất báo cáo:", "", "```text", git_state, "```", ""]
    (ROOT / "docs/data-catalog-handoff.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/data_prep")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    result = validate(args.output)
    review.dump_json(args.output / "catalog_validation.json", result)
    if args.write_report:
        handoff(review.load_json(args.output / "data_catalog.json"), result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
