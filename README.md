HỆ THỐNG QUẢN LÝ KHÁCH SẠN
1. Giới thiệu
1.1. Tổng quan

Hệ thống quản lý khách sạn được xây dựng nhằm hỗ trợ các hoạt động quản lý phòng, khách hàng, đặt phòng, dịch vụ và thanh toán trong khách sạn. Hệ thống được phát triển bằng ngôn ngữ Python với giao diện Tkinter và sử dụng SQLite làm cơ sở dữ liệu.

2. Công nghệ sử dụng
2.1. Ngôn ngữ lập trình

Python

2.2. Giao diện người dùng

Tkinter

2.3. Cơ sở dữ liệu

SQLite

2.4. Thư viện hỗ trợ

Matplotlib phục vụ thống kê

3. Chức năng hệ thống
3.1. Đăng nhập hệ thống

Hệ thống cho phép người dùng đăng nhập bằng tài khoản được cấp. Sau khi đăng nhập, người dùng được phân quyền theo vai trò như quản trị viên hoặc nhân viên lễ tân.

3.2. Quản lý loại phòng
3.2.1. Thêm loại phòng

Cho phép thêm loại phòng mới vào hệ thống.

3.2.2. Xóa loại phòng

Cho phép xóa loại phòng khi không còn sử dụng.

3.2.3. Cập nhật loại phòng

Cập nhật thông tin như giá phòng, sức chứa và mô tả.

3.3. Quản lý phòng
3.3.1. Thêm phòng

Thêm phòng mới vào hệ thống.

3.3.2. Xóa phòng

Xóa phòng khi không còn sử dụng.

3.3.3. Cập nhật trạng thái phòng

Các trạng thái phòng gồm trống, đang sử dụng, đang dọn dẹp, bảo trì.

3.4. Quản lý khách hàng
3.4.1. Thêm khách hàng

Thêm thông tin khách hàng vào hệ thống.

3.4.2. Xóa khách hàng

Xóa khách hàng khi không còn sử dụng.

3.4.3. Lưu trữ thông tin khách hàng

Bao gồm họ tên, số điện thoại, căn cước công dân và địa chỉ.

3.5. Quản lý dịch vụ
3.5.1. Thêm dịch vụ

Thêm dịch vụ mới vào hệ thống.

3.5.2. Cập nhật giá dịch vụ

Xác định giá cho từng dịch vụ.

3.5.3. Quản lý đơn vị tính

Quản lý đơn vị tính của dịch vụ.

3.6. Đặt phòng và nhận phòng
3.6.1. Chọn khách hàng

Lựa chọn khách hàng trong hệ thống.

3.6.2. Chọn phòng

Chọn phòng trống phù hợp.

3.6.3. Nhập thông tin đặt phòng

Bao gồm ngày nhận phòng và ngày trả phòng.

3.6.4. Tạo đặt phòng

Lưu thông tin đặt phòng vào hệ thống.

3.6.5. Nhận phòng

Thực hiện check in cho khách.

3.7. Quản lý sử dụng dịch vụ
3.7.1. Thêm dịch vụ phát sinh

Thêm dịch vụ vào booking.

3.7.2. Tính tiền dịch vụ

Tính tiền dựa trên số lượng sử dụng.

3.8. Trả phòng và thanh toán
3.8.1. Tính tiền phòng

Tính tiền dựa trên số ngày lưu trú.

3.8.2. Tính tiền dịch vụ

Tổng hợp chi phí dịch vụ phát sinh.

3.8.3. Lập hóa đơn

Tạo hóa đơn thanh toán.

3.8.4. Thanh toán

Xác nhận thanh toán của khách hàng.

3.8.5. Cập nhật trạng thái phòng

Chuyển trạng thái phòng sau khi trả phòng.

3.9. Thống kê và báo cáo
3.9.1. Tổng doanh thu

Hiển thị tổng doanh thu của khách sạn.

3.9.2. Thống kê theo thời gian

Thống kê theo tháng hoặc khoảng thời gian.

3.9.3. Biểu đồ thống kê

Hiển thị biểu đồ nếu có sử dụng matplotlib.

4. Cơ sở dữ liệu
4.1. File dữ liệu
hotel.db
4.2. Các bảng dữ liệu

4.2.1. users
4.2.2. room_types
4.2.3. rooms
4.2.4. customers
4.2.5. services
4.2.6. bookings
4.2.7. booking_services
4.2.8. invoices

5. Cài đặt và chạy chương trình
5.1. Yêu cầu hệ thống

Python phiên bản 3.8 trở lên

5.2. Cài đặt thư viện
pip install matplotlib
5.3. Chạy chương trình
python hotel_management.py
6. Cấu trúc thư mục
hotel_management.py
hotel.db
README.md
7. Quy trình sử dụng hệ thống
7.1. Thêm loại phòng
7.2. Thêm phòng
7.3. Thêm khách hàng
7.4. Tạo đặt phòng
7.5. Ghi nhận dịch vụ
7.6. Thực hiện trả phòng và thanh toán
8. Hạn chế của hệ thống
8.1. Chưa hỗ trợ đặt phòng trực tuyến
8.2. Chưa xuất hóa đơn PDF
8.3. Giao diện còn đơn giản
9. Hướng phát triển
9.1. Xây dựng giao diện web
9.2. Tích hợp thanh toán online
9.3. Quản lý nhiều chi nhánh
9.4. Nâng cấp báo cáo
