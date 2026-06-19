graph TD
    %% Định nghĩa các Style
    classDef frontend fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef proxy fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px;
    classDef api fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef service fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef database fill:#ffebee,stroke:#d32f2f,stroke-width:2px;
    classDef cicd fill:#eceff1,stroke:#546e7a,stroke-width:2px;

    %% ==========================================
    %% TẦNG CLIENT / FRONTEND
    %% ==========================================
    subgraph Tầng_Frontend ["🖥️ Tầng Giao Diện (web/)"]
        UI_JS["app.js<br>(Xử lý Logic Giao diện)"]:::frontend
        UI_HTML["index.html<br>(Render Dashboard)"]:::frontend
        
        UI_HTML --> UI_JS
        Action1(["1️⃣ Bấm 'Add Asset'"]) --> UI_JS
        Action2(["2️⃣ Bấm 'Trigger Scan'"]) --> UI_JS
        Action3(["3️⃣ Render Kết quả/Tags"]) --> UI_HTML
    end

    %% ==========================================
    %% TẦNG REVERSE PROXY
    %% ==========================================
    subgraph Tầng_Mạng ["🌐 Tầng Mạng / Proxy"]
        Nginx["nginx.conf<br>(Cổng 80, Điều hướng & Bảo mật)"]:::proxy
    end

    %% ==========================================
    %% TẦNG API / BACKEND ROUTER
    %% ==========================================
    subgraph Tầng_API ["⚙️ Tầng Giao Tiếp (internal/handler/)"]
        AppPY["app.py<br>(Khởi động Flask app)"]:::api
        Router["router.py<br>(Định nghĩa các Endpoints)"]:::api
        
        AppPY --> Router
    end

    %% ==========================================
    %% TẦNG SERVICE / CORE LOGIC
    %% ==========================================
    subgraph Tầng_Service ["🧠 Tầng Dịch Vụ & Model (internal/)"]
        Model["model/asset.py<br>(Validate Asset & Job)"]:::service
        ScanSvc["service/scan_service.py<br>(Tạo Background Thread)"]:::service
        Scanners["service/scanners.py<br>(Logic DNS, SSL, Port, CVE...)"]:::service
        Security["Kiểm tra An toàn<br>(Hàm is_local_host)"]:::service
        Analyzer["service/analyzer.py<br>(So sánh Diff/Delta)"]:::service
        
        Router -->|Tạo Object| Model
        ScanSvc -->|Khởi chạy| Scanners
        Scanners --> Security
    end

    %% ==========================================
    %% TẦNG DỮ LIỆU
    %% ==========================================
    subgraph Tầng_Data ["💾 Tầng Lưu Trữ (internal/storage/ & migrations/)"]
        DBDriver["database.py<br>(Giao tiếp DB qua Driver)"]:::database
        Migration["001_create_assets.up.sql<br>(Tạo bảng schema)"]:::database
        DB[(PostgreSQL / SQLite)]:::database
        
        DBDriver --> Migration
        Migration --> DB
    end

    %% ==========================================
    %% PIPELINE CI/CD
    %% ==========================================
    subgraph Tầng_CICD ["🚀 Tự động hóa CI/CD (.github/workflows/ci.yml)"]
        Push[Git Push / PR]:::cicd
        Lint[Flake8 Linting]:::cicd
        Test[Pytest Unit Tests]:::cicd
        Trivy[Trivy Security Scan]:::cicd
        DockerBuild[Docker Build Image]:::cicd
        
        Push --> Lint --> Test --> Trivy --> DockerBuild
    end

    %% ==========================================
    %% KẾT NỐI CÁC LUỒNG DỮ LIỆU (WORKFLOWS)
    %% ==========================================
    
    %% Luồng: Thêm Asset mới
    UI_JS -- "POST /api/assets" --> Nginx
    Nginx --> Router
    Router -- "Nếu hợp lệ" --> Model
    Model -- "Lưu Asset" --> DBDriver
    
    %% Luồng: Thực hiện Quét
    UI_JS -- "POST /api/assets/{id}/scan" --> Nginx
    Nginx --> Router
    Router -- "Gọi hàm start_scan()" --> ScanSvc
    ScanSvc -. "Trả HTTP 202 (Pending) ngay lập tức" .-> Router
    ScanSvc -- "Chạy ngầm (Worker)" --> Scanners
    Scanners -- "Kiểm tra Target có phải IP Public" --> Security
    Security -- "Cho phép Active Scan" --> Scanners
    Scanners -- "Lưu Log Kết quả vào DB" --> DBDriver
    
    %% Luồng: Phân tích & Render
    Analyzer -. "So sánh Cũ/Mới" .-> Scanners
    Router -- "GET /api/assets/{id}/results" --> DBDriver
    DBDriver -- "Trả về JSON" --> UI_JS
    UI_JS -- "Vẽ Badge/Cảnh báo" --> Action3