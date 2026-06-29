# Homework Submission - Day 3

**Họ tên:** Nguyễn Xuân Yến

## Các bài đã hoàn thành

- [x] Bài 1: Migrate sang Database
- [x] Bài 2: Mở rộng Scan API 
- [x] Bài 3: Viết Unit Tests
- [x] Bài 4: Tích hợp Frontend 
- [x] Bài 5: CI/CD với GitHub Actions 
- [x] Bài 6: Deploy với Docker Compose
- [x] Bài 7: Tính năng EASM mới
- [ ] Bài 8: Deploy lên Cloud VM 
- [ ] Bài 9: Domain & TLS/HTTPS 
- [ ] Bài 10: Auto Deploy on Merge 

## Link Repository

[Link GitHub repository]

## Link Demo (nếu có)

[Link deployed application]

## BÀI 1: Migrate sang Database
![docker compose up -d db](image-3.png)

![curl -X POST http://localhost:8080/assets](image-1.png)

![after reset server and try again](image-2.png)

## BÀI 2: Mở rộng Scan API 
![CREATE DOMAIN ASSET](image-6.png)
Lấy ID của Domain được tạo để scan DNS

![Scan Domain DNS](image-7.png)
Lấy ID của job được tạo để check status của Job
            -----------
![Show Job status](image-8.png)

![Show Job result](image-9.png)

![Overview asset result](image-10.png)
            -----------
![Create IP Asset](image-11.png)
Lấy ID của IP 8.8.8.8 để quét port hoặc CVE

![Scan Port 8.8.8.8](image-12.png)

![Check Status](image-13.png)
Kết quả báo "fail" và field error báo lỗi, chỉ có thể scan port local hoặc private ip


## Bài 3: Unit Test
![alt text](image-14.png)
![alt text](image-15.png)

## Bài 4: Tích hợp front-end 
![Giao diện chính](image-16.png)

![Giao diện Asset](image-17.png)
![Thêm Asset](image-20.png)
![Asset được thêm lưu vào danh sách](image-21.png)
![Xóa Asset](image-22.png)
![Asset được xóa thành công](image-23.png)

![Giao diện Scan](image-18.png)

![Giao diện Result](image-19.png)

## Bài 5: CICD 

![CI running](image.png)

![CI pipeline](image-4.png)

![Scan result](image-5.png)

## Bài 6: Docker Compose Deploy
![docker-compose ps](image-24.png)
![frontend access localhost:3000](image-25.png)
![health check passing](image-26.png)


# Bài 7: EASM new function


## Bài 8: Cloud VM


## Bài 9: Domain & TLS/HTTPS 



## Bài 10: Auto Deploy on Merge 