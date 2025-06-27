# XML to UPPAAL Converter

A web application for converting XML Activity Diagrams to UPPAAL format.

## 🏗️ Project Structure

```
TransformingACtoTA/
├── backend/                 # Backend API (FastAPI)
│   ├── app/
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── config.py       # Configuration settings
│   │   ├── routes/
│   │   │   └── api.py      # API endpoints
│   │   └── services/
│   │       └── converter.py # XML to UPPAAL conversion logic
│   └── requirements.txt    # Python dependencies
├── frontend/               # Frontend (HTML/CSS/JS)
│   └── index.html         # Main frontend interface
├── shared/                 # Shared resources
│   ├── Example_XML/       # Example XML files
│   └── Result/            # Generated UPPAAL files
└── README.md              # This file
```

## 🚀 Quick Start

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   python -m app.main
   ```

### Frontend Access

- **Main Interface:** http://127.0.0.1:8000/
- **API Documentation:** http://127.0.0.1:8000/docs

## 📁 Directory Structure Explained

### Backend (`/backend`)
- **`app/main.py`** - FastAPI application setup and server configuration
- **`app/config.py`** - Application settings and configuration
- **`app/routes/api.py`** - API endpoints for XML conversion
- **`app/services/converter.py`** - Core conversion logic

### Frontend (`/frontend`)
- **`index.html`** - User interface for file upload and conversion

### Shared (`/shared`)
- **`Example_XML/`** - Sample XML files for testing
- **`Result/`** - Generated UPPAAL files

## 🔧 API Endpoints

- **`GET /`** - Serve frontend interface
- **`POST /convert-xml`** - Convert XML to UPPAAL (returns JSON)
- **`POST /convert-xml-download`** - Convert XML to UPPAAL (downloads file)

## 🎯 Benefits of This Structure

1. **Separation of Concerns** - Backend and frontend are clearly separated
2. **Scalability** - Easy to add new features to either backend or frontend
3. **Maintainability** - Clear organization makes code easier to maintain
4. **Deployment Flexibility** - Can deploy backend and frontend separately
5. **Team Collaboration** - Different teams can work on different parts

## 🛠️ Development

### Adding New API Endpoints
1. Add new routes in `backend/app/routes/api.py`
2. Import and include in `backend/app/main.py`

### Adding New Services
1. Create new service files in `backend/app/services/`
2. Import and use in routes

### Frontend Changes
1. Modify files in `frontend/` directory
2. Access via `http://127.0.0.1:8000/`

## 📝 Notes

- The backend serves the frontend static files
- All generated files are saved in `shared/Result/`
- Example files are available in `shared/Example_XML/`

## ✨ คุณสมบัติ

- 🌐 **Web Interface**: อินเตอร์เฟซที่ใช้งานง่าย สามารถลากและวางไฟล์ได้
- 📁 **รองรับหลายรูปแบบ**: รองรับไฟล์ .xml และ .uml
- ⚡ **แปลงทันที**: แปลงไฟล์และดาวน์โหลดผลลัพธ์ได้ทันที
- 🎯 **API Endpoint**: รองรับการเรียกใช้ผ่าน API

## 🚀 การติดตั้งและรัน

### 1. ติดตั้ง Dependencies

**สำหรับ Windows:**
```bash
py -m pip install -r backend/requirements.txt
```

**สำหรับ macOS/Linux:**
```bash
pip install -r backend/requirements.txt
```

### 2. รันเซิร์ฟเวอร์

**วิธีที่ 1 (แนะนำ):**
```bash
python run.py
```

**วิธีที่ 2:**
```bash
cd backend
python -m app.main
```

**วิธีที่ 3:**
```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. เปิดใช้งาน

เปิดเบราว์เซอร์และไปที่: **http://127.0.0.1:8000**

## 📖 วิธีการใช้งาน

### ผ่าน Web Interface

1. เปิดเบราว์เซอร์ไปที่ http://127.0.0.1:8000
2. เลือกไฟล์ Activity Diagram (.xml หรือ .uml) โดย:
   - คลิกที่พื้นที่อัปโหลด หรือ
   - ลากและวางไฟล์ลงในพื้นที่อัปโหลด
3. คลิกปุ่ม "Convert to UPPAAL"
4. รอให้การแปลงเสร็จสิ้น
5. คลิก "Download Result" เพื่อดาวน์โหลดไฟล์ผลลัพธ์

### ผ่าน API

```bash
curl -X POST "http://127.0.0.1:8000/convert-xml" \
     -H "accept: application/xml" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_activity_diagram.xml"
```

## 🔧 การปรับแต่ง

- **เปลี่ยนพอร์ต**: แก้ไขในไฟล์ `backend/app/config.py`
- **เปลี่ยน host**: แก้ไขในไฟล์ `backend/app/config.py`

## 🔍 การทดสอบ

มีไฟล์ตัวอย่างในโฟลเดอร์ `shared/Example_XML/` ที่สามารถใช้ทดสอบได้
