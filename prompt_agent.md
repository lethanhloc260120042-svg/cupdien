Markdown

# ⚡ Master Plan: Hệ thống Thông báo Cúp điện Địa phương (Local Power Outage Notifier)

## 🎯 Ngữ cảnh (Context)
Bạn là một Expert Full-Stack Developer (chuyên gia về Django, Python, PostgreSQL và Frontend UI). Bạn đang nhận một dự án hoàn toàn trống (Empty Project) và cần xây dựng từ con số 0.

Ứng dụng này là một trang web cho phép người dùng xem lịch cúp điện, đăng nhập bằng Google, và đăng ký nhận thông báo (qua Email và Web Push Notification) nếu khu vực phường/xã của họ sắp bị cúp điện.

Dữ liệu cúp điện sẽ được cào (scrape) tự động từ trang web điện lực, sau đó so sánh với danh sách khu vực người dùng đã đăng ký để gửi thông báo.

## 🛠 Tech Stack
- **Backend:** Django, Celery (cho background tasks & cronjobs).
- **Database:** Supabase (PostgreSQL).
- **Authentication:** Google OAuth 2.0 (django-allauth).
- **Frontend:** Django Templates + Tailwind CSS (thông qua CDN cho nhanh và đồng bộ). Vanilla JS cho logic UI.
- **Web Scraping:** Selenium + BeautifulSoup.
- **Thông báo:** SMTP Email (Django Email Backend) & Web Push Notifications (thông qua service worker).

## 🔑 Môi trường (Environment Variables)
Bạn PHẢI sử dụng cấu hình dưới đây để setup file `.env` và file `settings.py` của Django:

**Database (Supabase PostgreSQL):**
```env
DATABASE_URL=postgres://postgres.ajsxndxzvfdqnupgbibf:cupdien@@2004@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres

Email SMTP (Gmail):
Đoạn mã

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=lethanhloc2612004@gmail.com
EMAIL_HOST_PASSWORD=gqhn khbs wxzl ydgc
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=DevLearn <lethanhloc2612004@gmail.com>

🌍 API Hành chính Việt Nam (Vietnam Administrative Units)

Để làm form chọn Tỉnh/Thành -> Quận/Huyện -> Phường/Xã cho người dùng thêm khu vực nhận thông báo, sử dụng Open API hoàn toàn miễn phí này:

    API Endpoint: https://provinces.open-api.vn/api/?depth=3

    API này luôn cập nhật các đơn vị hành chính sau sáp nhập. Hãy viết Javascript gọi API này để tạo 3 thẻ <select> phụ thuộc nhau (Cascading Dropdown).

📋 Checklist Công việc (Master Plan)

Bạn hãy thực hiện từng bước dưới đây. Làm xong bước nào, hãy đánh dấu [x] và báo cáo tiến độ trước khi chuyển sang bước tiếp theo.
Giai đoạn 1: Khởi tạo & Cấu hình cơ bản

    [x] Khởi tạo dự án Django mới và tạo app chính (vd: core).

    [x] Cấu hình settings.py để kết nối với Supabase PostgreSQL (sử dụng gói dj-database-url và psycopg2-binary).

    [x] Cài đặt và cấu hình django-allauth để kích hoạt chức năng Login bằng Google.

    [x] Setup thư mục templates và static, tích hợp Tailwind CSS (qua script tag CDN). Tạo base template với Navbar, Footer chuẩn UI/UX hiện đại.

Giai đoạn 2: Database Models

    [x] Tạo model UserProfile mở rộng từ User của Django.

    [x] Tạo model OutageData: Lưu trữ lịch cúp điện (Quận, Phường/Khu vực, Ngày, Giờ bắt đầu, Giờ kết thúc, Lý do, Trạng thái).

    [x] Tạo model UserSubscription: Lưu thông tin các khu vực người dùng muốn nhận thông báo. Các trường: user (ForeignKey), province_code, province_name, district_code, district_name, ward_code, ward_name. User có thể có nhiều Subscriptions.

Giai đoạn 3: UI & Tính năng dành cho User

    [x] Xây dựng trang Home: Hiển thị bảng/lưới lịch cúp điện được lấy từ database OutageData.

    [x] Xây dựng Dashboard cá nhân (chỉ cho user đã đăng nhập):

        Xem danh sách các Phường/Xã đang theo dõi.

        Tích hợp 3 Dropdown (Tỉnh - Quận - Phường) gọi dữ liệu từ provinces.open-api.vn bằng Vanilla JS.

        Nút Submit để lưu khu vực theo dõi vào DB.

        Nút/Toggle "Cấp quyền nhận thông báo trên trình duyệt" (Kích hoạt Web Push API).

    [x] Tạo các View (CRUD) cho phép user Thêm/Xóa khu vực nhận thông báo.

Giai đoạn 4: Logic Scraping & Matching (Xử lý nền với Celery)

    [ ] Cấu hình Celery và Redis (hoặc dùng database-backed broker nếu Redis chưa sẵn sàng).

    [x] Tích hợp script Python cào dữ liệu cúp điện (Selenium + BeautifulSoup) thành một Celery Task chạy định kỳ (vd: mỗi sáng lúc 6h) / Hoặc Management Command. Dữ liệu cào về lưu vào model OutageData.

    [x] Viết hàm check_and_notify() logic:

        Lấy dữ liệu cúp điện trong 7 ngày tới.

        Tìm kiếm trong chuỗi Khu vực cúp điện xem có chứa tên Phường/Xã (ward_name) hoặc Quận/Huyện (district_name) mà bất kỳ User nào đang follow không.

        Gom nhóm các lịch bị ảnh hưởng theo từng User.

Giai đoạn 5: Hệ thống Cảnh báo (Notification)

    [x] Code logic Gửi Email: Với các user bị ảnh hưởng (match ở GĐ 4), render một template email HTML đẹp đẽ báo cho họ biết: Ngày nào, Giờ nào, Khu vực nào cúp điện. Sử dụng cấu hình SMTP đã cho.

    [x] Tích hợp Web Push Notification: Cài đặt Service Worker ở Frontend để nhận thông báo đẩy. Khi có lịch match, push thẳng notification về thiết bị của user.
