# Training Code & Model Heritage — DataMate ZAIC 2026
**Đội thi:** Zalo trừ nửa  
**Identifier:** `zalotrunua`  
**Tuân thủ:** Quy chế thi Zalo AI Challenge 2026 (Mục 8 & 9)

---

## 1. Tuyên bố Mô hình (Model Declaration)
- **Kiến trúc mô hình chính:** Qwen3.5-9B (Dense Causal Language Model, ~9 tỷ tham số).
- **Trọng số công khai:** [unsloth/Qwen3.5-9B-GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF) (Revision: `3885219b6810b007914f3a7950a8d1b469d598a5`).
- **File trọng số:** `Qwen3.5-9B-Q4_K_M.gguf` (Dung lượng: 5.68 GB, SHA-256: `03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8`).
- **Giấy phép:** Apache 2.0 (Thương mại và sử dụng hợp lệ, phát hành trước mốc 26/10/2026).
- **Giới hạn tham số:** Tổng tham số 9B $\le$ 15B theo đúng điều lệ BTC.

---

## 2. Phương pháp luận & Quá trình Huấn luyện
- **Phương pháp tiếp cận:** Hệ thống sử dụng kiến trúc **Agentic RAG / Zero-Shot In-Context Learning Text-to-SQL**.
- **Không thực hiện Fine-Tuning có trọng số:** Trọng số mô hình được giữ nguyên (frozen Q4_K_M) để đảm bảo tính ổn định và tính tái lập tối đa.
- **Cơ chế suy luận:**
  1. Trích xuất Schema Catalog động từ CSV, Excel, SQLite bằng Polars / Fastexcel.
  2. Đăng ký bảng vào máy ảo tính toán chỉ đọc Apache DataFusion.
  3. Xây dựng prompt chứa ngữ cảnh câu hỏi, ngày tham chiếu `as_of_date`, lịch âm dương `calendar.csv`, luật nghiệp vụ `rulebook.md`.
  4. Mô hình sinh câu truy vấn SQL đọc dữ liệu và kiểu dữ liệu trả về.
  5. Kiểm tra tính hợp lệ và thực thi truy vấn an toàn, ghi nhận đáp án ngay lập tức (`immediate flush`).

---

## 3. Tái lập & Kiểm thử Huấn luyện
Mô hình không cần chạy lại vòng huấn luyện gradient descent. Để kiểm chứng tính toàn vẹn của mô hình và dữ liệu, chạy:

```bash
bash train.sh
```

Script này kiểm tra mã băm SHA-256 của các tập dữ liệu (`train.zip`, `public_test.zip`) và trọng số mô hình `Qwen3.5-9B-Q4_K_M.gguf`.
