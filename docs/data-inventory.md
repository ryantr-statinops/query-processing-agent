# Data inventory

Snapshot generated from the local competition package. Source files are left unchanged.

## train

- Businesses: 30
- Files: 162
- File types: .csv: 21, .jsonl: 2, .md: 31, .sqlite: 1, .xlsx: 107
- Questions: 3000
- Answers: 3000; types: boolean: 23, date: 145, list: 193, number: 1884, percent: 578, string: 88, table: 19, unanswerable: 70

| Business | Questions | Files | Formats | README |
|---|---:|---:|---|---|
| `biz_101` | 40 | 1 | .csv × 1 | yes |
| `biz_102` | 119 | 2 | .xlsx × 2 | yes |
| `biz_103` | 119 | 2 | .xlsx × 2 | yes |
| `biz_104` | 119 | 2 | .xlsx × 2 | yes |
| `biz_105` | 119 | 6 | .xlsx × 6 | yes |
| `biz_106` | 119 | 10 | .xlsx × 10 | yes |
| `biz_107` | 40 | 1 | .xlsx × 1 | yes |
| `biz_108` | 119 | 7 | .xlsx × 7 | yes |
| `biz_109` | 118 | 2 | .xlsx × 2 | yes |
| `biz_110` | 40 | 1 | .csv × 1 | yes |
| `biz_111` | 118 | 5 | .csv × 5 | yes |
| `biz_112` | 118 | 3 | .xlsx × 3 | yes |
| `biz_113` | 40 | 1 | .xlsx × 1 | yes |
| `biz_114` | 40 | 1 | .csv × 1 | yes |
| `biz_115` | 118 | 4 | .xlsx × 4 | yes |
| `biz_116` | 118 | 1 | .xlsx × 1 | yes |
| `biz_117` | 118 | 7 | .xlsx × 7 | yes |
| `biz_118` | 118 | 4 | .xlsx × 4 | yes |
| `biz_119` | 118 | 10 | .xlsx × 10 | yes |
| `biz_120` | 118 | 10 | .xlsx × 10 | yes |
| `biz_121` | 118 | 2 | .xlsx × 2 | yes |
| `biz_122` | 118 | 9 | .xlsx × 9 | yes |
| `biz_123` | 118 | 1 | .sqlite × 1 | yes |
| `biz_124` | 118 | 13 | .csv × 1, .xlsx × 12 | yes |
| `biz_125` | 40 | 1 | .csv × 1 | yes |
| `biz_126` | 40 | 1 | .xlsx × 1 | yes |
| `biz_127` | 118 | 5 | .csv × 5 | yes |
| `biz_128` | 118 | 8 | .xlsx × 8 | yes |
| `biz_129` | 118 | 5 | .csv × 5 | yes |
| `biz_130` | 118 | 3 | .xlsx × 3 | yes |

## public_test

- Businesses: 14
- Files: 97
- File types: .csv: 11, .jsonl: 1, .md: 15, .sqlite: 1, .xlsx: 69
- Questions: 1000

| Business | Questions | Files | Formats | README |
|---|---:|---:|---|---|
| `dev_001` | 87 | 2 | .xlsx × 2 | yes |
| `dev_002` | 41 | 18 | .xlsx × 18 | yes |
| `dev_003` | 129 | 7 | .csv × 1, .xlsx × 6 | yes |
| `dev_004` | 96 | 7 | .xlsx × 7 | yes |
| `dev_005` | 87 | 23 | .xlsx × 23 | yes |
| `dev_006` | 111 | 1 | .sqlite × 1 | yes |
| `dev_007` | 60 | 3 | .csv × 3 | yes |
| `dev_008` | 99 | 4 | .xlsx × 4 | yes |
| `dev_009` | 21 | 1 | .csv × 1 | yes |
| `dev_010` | 59 | 5 | .csv × 5 | yes |
| `dev_011` | 40 | 1 | .xlsx × 1 | yes |
| `dev_012` | 50 | 2 | .xlsx × 2 | yes |
| `dev_013` | 57 | 3 | .xlsx × 3 | yes |
| `dev_014` | 63 | 3 | .xlsx × 3 | yes |

## Next inventory pass

- Record each representative training question ID and its intended data path: business README, source files, sheets/tables, relevant columns, and rulebook clause.
- Inspect source schemas and data quality without modifying competition files.
- Compare derived answers with `train/answers.jsonl` and record discrepancies for investigation.
- Keep business-level development/holdout grouping from `configs/splits/seed_2026.json` when selecting examples or comparing experiments.
- `configs/representative_questions.json` contains 60 training questions: two per business, copied from train questions and labels. The set covers all observed answer types; trace each question to source sheets/tables and rulebook clauses.
