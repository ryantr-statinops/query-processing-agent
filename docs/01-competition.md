# DataMate challenge scope and rules

## Inputs and outputs

Each question has an ID, a `business_id`, and an `as_of_date`. Load the matching business package, which can contain CSV, Excel, or SQLite files and a README describing the business. The split also supplies a rulebook and a shared solar–lunar calendar. Resolve relative dates using `as_of_date` and submit a typed answer keyed by the question ID. [DataMate description](https://challenge.zalo.ai/portal/datamate/)

The following synthetic question is in Vietnamese to match the track's input. It asks how many cups of peach tea were sold last month.

```jsonl
{"id":"demo_01","business_id":"demo_shop","question":"Tháng trước bán được mấy ly trà đào?","as_of_date":"2026-03-04"}
```

The example contains five qualifying cups, so the response uses the `number` type with a value of `5`.

```jsonl
{"id":"demo_01","type":"number","answer":5}
```

## Scoring

Penalized Accuracy (PA) equals `(correct − wrong) / total questions`. Each question has equal weight. A correct answer earns `+1`, a wrong answer earns `−1`, and abstaining or omitting an answer earns `0`. The evaluator requires both the correct type and a matching value for ordinary answers. Predicting `unanswerable` earns `+1` on a matching reference and `−1` on an answerable question. Score ties are settled by total inference time in the organizers' rerun, then by earlier submission. [DataMate evaluation](https://challenge.zalo.ai/portal/datamate/)

| Type | What the evaluator checks |
| --- | --- |
| `number` | Exact numerical match against the reference value. Use the required unit and precision. |
| `percent` | Match after rounding to two decimal places, including the sign. Use the percentage value, so 12.5% is encoded as `12.5`. |
| `string` | Exact match after normalization against accepted forms. Preserve Vietnamese diacritics. Accepted forms can include name variants from the data and the corresponding code. |
| `date` | ISO `YYYY-MM-DD`, or `YYYY-MM` for a question about a month. |
| `boolean` | JSON `true` or `false`. |
| `list` | Match elements in order using the applicable string or number rules. |
| `table` | Supply `columns` and `rows`. Columns are aligned by normalized name with positional fallback, and rows are compared as a set. |
| `unanswerable` | Match the reference label for insufficient evidence. |
| `abstain` | Always scores zero. |

For ranking questions, apply the stated criterion or the rulebook default to valid orders. Sort the criterion descending and resolve ties by code ascending. The test sets exclude ties at the requested cutoff, including first place for superlatives. If fewer than `k` candidates qualify, return all of them in order. Verify the exact answer matching and serialization rules against the official evaluator. [DataMate evaluation](https://challenge.zalo.ai/portal/datamate/)

## Rules that affect the architecture

- **Models.** The combined inference limit is **15B parameters** across language models, embedders, rerankers, and classifiers, even if they run at different times. Count all mixture-of-experts parameters. The underlying weights must have been publicly released before October 26, 2026, under a compatible license. Quantization and fine-tuning are permitted. List the models in the submission README. [DataMate rules](https://challenge.zalo.ai/portal/datamate/)
- **Execution.** Inference runs offline in Docker. The organizers mount the dataset at `/data` with read-only access and collect `/result/submission.jsonl`. Generated code can run inside the container. Answers must be produced automatically. Use identifiers for routing data and matching predictions to questions. The rules prohibit hard-coded answers and solution logic keyed to specific question or business IDs. [DataMate rules](https://challenge.zalo.ai/portal/datamate/)
- **Development data.** The rules allow the supplied training set, synthetic data, and eligible public data and models. They prohibit training on public or private test data and obtaining answers to test questions. Split the training set by business for calibration and internal evaluation. [DataMate rules](https://challenge.zalo.ai/portal/datamate/), [General regulations](https://challenge.zalo.ai/regulations)
- **Compute and reproducibility.** The reference machine has two RTX 5090 GPUs with 32 GB of VRAM each and 512 GB of RAM. The **six-hour** wall-clock limit covers the full private test, including model loading. Final ranking uses the organizers' Docker rerun. The stated reproducibility criterion is an absolute difference of at most `0.03` PA between the uploaded output and the rerun. If execution stops early, unwritten answers count as abstentions. [DataMate rules](https://challenge.zalo.ai/portal/datamate/)

## Submission milestones

All times are GMT+7.

| Date | Deliverable |
| --- | --- |
| October 26–November 16 | Run the public test and upload JSONL. The portal allows up to five public submissions per day. |
| November 16, 23:59 | Submit the Docker package and freeze the solution. The guidance asks for a checksum and a public Google Drive download link. The organizers use the last of up to two solution submissions. |
| November 20 | Private test release. The track guidance lists 09:00, while the general timeline lists 11:00. Confirm the release time on the portal before the run. |
| November 23, 23:59 | Upload the private-test JSONL produced by the frozen solution. |

[DataMate submission guidance](https://challenge.zalo.ai/portal/datamate/), [General timeline](https://challenge.zalo.ai/#timeline)

The **Data** tab requires sign-in, and the Docker Guide PDF was unavailable during this review. Confirm the kit layout, evaluator version, required JSONL fields, log format, base image, and exact Docker command once the official kit and guide are available. [DataMate Docker Guide](https://dl-challenge.zalo.ai/2026/datamate_dkewxftdzo/zac2026_DataMate_docker_guideline_final.pdf)
