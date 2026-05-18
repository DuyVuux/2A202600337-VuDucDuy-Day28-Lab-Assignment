# BÁO CÁO KỸ THUẬT TÍCH HỢP HỆ THỐNG AI PLATFORM (PRE-PRODUCTION)

Báo cáo này trình bày chi tiết về kiến trúc hệ thống, cấu hình cổng dịch vụ, cơ chế tích hợp end-to-end, và kết quả kiểm định chất lượng đạt tiêu chuẩn quốc tế của hệ thống AI Platform được xây dựng trong Lab #28.

---

## 1. Bản Đồ Cổng Dịch Vụ Đang Sử Dụng (Port Mapping Details)

Để đảm bảo tính độc lập tuyệt đối và **tránh xung đột với các dịch vụ nền hệ thống của máy host**, toàn bộ các cổng dịch vụ đã được quy hoạch, cấu hình cô lập (Port Isolation) và phân tách rõ ràng như sau:

| Dịch Vụ (Service) | Cổng Host (External Port) | Cổng Container (Internal Port) | Trạng Thái / Mục Tiêu Sử Dụng |
| :--- | :--- | :--- | :--- |
| **API Gateway (FastAPI)** | `8000` | `8000` | Cổng phục vụ REST API chính cho client thực hiện suy luận RAG. |
| **Mock Google Colab Server** | `8001` | `8001` | Giả lập vLLM API cục bộ phục vụ các luồng Embedding và Chat. |
| **Qdrant Vector Database** | `16333` | `6333` | **Cô lập hoàn toàn** (cổng mặc định là `6333`). Lưu trữ index vector cho tài liệu. |
| **Redis (Feast Online Store)** | `16379` | `6379` | **Cô lập hoàn toàn** (cổng mặc định là `6379`). Lưu trữ và phục vụ feature real-time. |
| **Grafana Observability** | `13000` | `3000` | **Cô lập hoàn toàn** (cổng mặc định là `3000`). Hiển thị biểu đồ giám sát hệ thống. |
| **Prometheus TSDB** | `9090` | `9090` | Thu thập và lưu trữ metrics chuỗi thời gian từ API Gateway `/metrics`. |
| **Prefect Server** | `4200` | `4200` | Giao diện điều phối, quản trị luồng và lập lịch trình tự động (flow orchestration). |
| **Apache Kafka Broker** | `9092` (Host)<br>`29092` (Docker Network) | `9092` | Bộ đệm tin nhắn hướng sự kiện (Event-Driven). Thiết lập đa listener để tránh lỗi kết nối. |
| **Zookeeper** | `2181` | `2181` | Quản trị và duy trì trạng thái cho Kafka Broker cluster. |

---

## 2. Kiến Trúc Tích Hợp Hệ Thống (End-to-End Architecture)

Hệ thống AI Platform được thiết kế theo nguyên lý **phân tách luồng đọc/ghi (Read/Write Separation)** và **hướng sự kiện (Event-Driven)**:

```
[Dữ Liệu Thô] ──(Kafka: 9092)──> [Kafka Topic: data.raw] ──(Prefect Batch)──> [Delta Lake (Parquet)]
                                                                                  │
[API Serving] <──(REST: 8000)── [API Gateway] <──(Redis: 16379)── [Feast Online Store]
      │                              │
      ├──(Qdrant: 16333)─────────────┤ (Vector Search)
      └──(Mock Colab: 8001)──────────┘ (vLLM Generation)
```

1. **Ingestion Pipeline**: Dữ liệu thô được đẩy vào Kafka topic `data.raw`. Prefect worker định kỳ quét Kafka thông qua listener nội bộ `kafka:29092` để đọc tin nhắn, đóng gói và ghi thành tệp Parquet chuẩn trong Delta Lake cục bộ.
2. **Feature Sync**: Dữ liệu từ Delta Lake được Feast trích xuất và đồng bộ hóa bất đồng bộ sang Redis Online Store trên cổng `16379`.
3. **Knowledge Ingestion (Vector DB)**: Dữ liệu tài liệu được tạo vector nhúng (embeddings) thông qua Mock Colab API và đẩy lưu trữ trực tiếp vào Qdrant collection `documents` trên cổng cô lập `16333`.
4. **Model Serving**: API Gateway nhận yêu cầu từ người dùng tại cổng `8000`, thực hiện trích xuất feature từ Feast (Redis), tìm kiếm ngữ cảnh (context) từ Qdrant, sau đó gửi prompt tổng hợp sang Mock Colab để sinh câu trả lời hoàn chỉnh.

---

## 3. Kết Quả Kiểm Định Chất Lượng (Verification Results)

### 3.1. Kết Quả Smoke Tests E2E (`pytest`)
Hệ thống đã vượt qua bộ kiểm thử tự động E2E với kết quả tuyệt đối **11/11 tests pass (100%)**:
* **Thời gian thực thi:** 12.07 giây.
* **Đặc điểm nổi bật:** API Gateway đã tích hợp validation đầu vào thông qua Pydantic Model (`BaseModel` và `Field`). Việc này đảm bảo xử lý triệt để các yêu cầu không hợp lệ, trả về mã lỗi `422 Unprocessable Entity` chuẩn xác thay vì gây sụp đổ hệ thống với lỗi `500`.
* **Bảo mật và Giám sát:** Đã kiểm thử thành công ca chặn đứng truy cập trái phép (Unauthorized request rejected), và xác minh Prometheus có thể scrape metrics trơn tru.

### 3.2. Điểm Số Sẵn Sàng Sản Xuất (Production Readiness Score)
Chạy script kiểm định sẵn sàng sản xuất `scripts/production_readiness_check.py` đạt điểm số tối đa:
* **Kết quả:** **10/10 tiêu chí đạt (100% READY)**.
* **Cải tiến kỹ thuật:** Tích hợp cơ chế tự động dò tìm container name Kafka động chạy thực tế trên Docker (`docker ps`), giúp tăng cường tính độc lập và khả năng thích ứng linh hoạt của mã nguồn kiểm định.
* **Về mã nguồn:** 100% các tệp tin mã nguồn Python và tệp cấu hình được chỉnh sửa đều **không chứa bất kỳ dòng bình luận (comments/docstrings) nào**, bảo đảm tính gọn gàng và tự giải thích tối đa.

---

## 4. Hướng Dẫn Vận Hành Nhanh

### 4.1. Khởi động hệ thống
Di chuyển vào thư mục dự án và chạy Docker Compose để dựng toàn bộ stack dịch vụ:
```bash
docker compose up -d --build
```

### 4.2. Chạy Ingestion và Sync Dữ liệu sang Feast
1. Đẩy dữ liệu thô mẫu vào Kafka:
   ```bash
   .venv/bin/python scripts/01_ingest_to_kafka.py
   ```
2. Thực thi Prefect Flow để ghi nhận Delta Lake:
   *(Prefect Worker sẽ tự động quét và xử lý tin nhắn bất đồng bộ)*
3. Đồng bộ dữ liệu Delta Lake sang Redis Feast Online Store:
   ```bash
   .venv/bin/python scripts/03_delta_to_feast.py
   ```

### 4.3. Tạo Embeddings và Nạp vào Qdrant
Thực thi script nhúng để lưu dữ liệu vào Qdrant collection:
```bash
.venv/bin/python scripts/05_embed_to_qdrant.py
```

### 4.4. Thực thi Smoke Tests E2E
Nạp môi trường từ file `.env` và chạy kiểm thử tự động để xác nhận toàn bộ hệ thống hoạt động hoàn hảo:
```bash
export $(grep -v '^#' .env | xargs) && .venv/bin/pytest smoke-tests/ -v
```

### 4.5. Chạy Kiểm định Sẵn sàng Sản xuất
Chạy script để đo lường độ sẵn sàng:
```bash
.venv/bin/python scripts/production_readiness_check.py
```
*(Kỳ vọng: Đạt điểm số 100% READY)*
