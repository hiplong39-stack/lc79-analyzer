# LC79 Analyzer V3.1

Website responsive dùng FastAPI + HTML/CSS/JavaScript. Có giao diện thống kê 3 xúc xắc, kiểm tra/lưu chuỗi MD5 và API docs.

## Chạy trên máy tính

Yêu cầu Python 3.10+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn lc79_api:app --host 127.0.0.1 --port 8000
```

Mở http://127.0.0.1:8000  
Tài liệu API: http://127.0.0.1:8000/docs

## Mở trên iPhone cùng Wi-Fi

Chạy server trên máy tính:
```bash
uvicorn lc79_api:app --host 0.0.0.0 --port 8000
```
Tìm IP LAN của máy tính (ví dụ 192.168.1.20), rồi trên iPhone cùng Wi-Fi mở:
`http://192.168.1.20:8000`

Đây là cách thử nghiệm trong mạng nội bộ, không phải website công khai. Muốn truy cập từ mọi nơi cần deploy lên hosting/server có HTTPS.

## API

- `GET /health`
- `GET /v1/dice/theory`
- `POST /v1/dice/analyze`
- `POST /v1/history/analyze`
- `POST /v1/md5/inspect`
- `POST /v1/md5/batch`

Ví dụ request:
```json
{
  "rounds": [
    {"round_id": "6995429", "dice": [4, 5, 6]},
    {"round_id": "6995430", "dice": [2, 3, 4]}
  ]
}
```

## Giới hạn quan trọng

- Không phải API chính thức của LC79 và không tự kết nối/đăng nhập/đọc dữ liệu LC79.
- Chỉ phân tích dữ liệu người dùng nhập.
- Hash MD5 không thể đảo ngược để lấy kết quả. Kiểm tra độ dài/hex không chứng minh tính xác thực.
- Không có cam kết dự đoán chính xác 90%; thống kê quá khứ không bảo đảm phiên sau.
- Luật Tài/Xỉu 3 xúc xắc trong code là quy tắc phổ biến: bộ ba tách riêng, Xỉu 4–10, Tài 11–17. Hãy xác nhận luật cụ thể của bàn chơi trước khi dùng.


## V3 Browser Connect (Safari bookmarklet)

1. Start the website/API as described above.
2. Open the website and choose **Kết nối trình duyệt**.
3. Copy the bookmarklet code.
4. In Safari, create a bookmark, edit its URL, and paste the bookmarklet code.
5. Open the LC79 page and tap that bookmark. It copies visible page text.
6. Return to LC79 Analyzer, paste the captured text, and inspect candidates.
7. Review extracted candidates manually; only then use them as analysis input.

The bookmarklet reads visible DOM text only. It cannot reliably read canvas/WebGL, hidden application state, protected APIs, or content in another frame/origin. It does not access login cookies/passwords, bypass site controls, or place bets. It is a user-triggered capture, not a background/live connection.


## V3.1 - giao diện và Safari
- Điều hướng tab dùng event delegation, hỗ trợ thao tác chạm trên iPhone và nút bàn phím.
- Trạng thái API hiển thị rõ; giao diện vẫn điều hướng được khi API chưa chạy.
- Bổ sung xử lý lỗi, trạng thái đang chạy, escape dữ liệu khi hiển thị bảng và lưu MD5 an toàn hơn.
- Bookmarklet chỉ sao chép văn bản DOM đang hiển thị do người dùng chủ động kích hoạt. Trên Safari iPhone, nếu clipboard bị chặn, bookmarklet mở hộp văn bản để người dùng tự sao chép.
- Không truy cập cookie, mật khẩu, API riêng tư, không tự động hóa đặt cược và không cam kết dự đoán.
