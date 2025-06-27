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
py -m pip install -r requirements.txt
```

**สำหรับ macOS/Linux:**
```bash
pip install -r requirements.txt
```

### 2. รันเซิร์ฟเวอร์

**สำหรับ Windows:**
```bash
py run_server.py
```

**สำหรับ macOS/Linux:**
```bash
python run_server.py
```

หรือรันด้วย uvicorn โดยตรง:

**สำหรับ Windows:**
```bash
py -m uvicorn Main_Beyone:app --host 0.0.0.0 --port 8000 --reload
```

**สำหรับ macOS/Linux:**
```bash
uvicorn Main_Beyone:app --host 0.0.0.0 --port 8000 --reload
```

### 3. เปิดใช้งาน

**สำหรับ Windows:**
```bash
start http://localhost:8000
```

**สำหรับ macOS/Linux:**
```bash
open http://localhost:8000    # macOS
xdg-open http://localhost:8000  # Linux
```

หรือเปิดเบราว์เซอร์และไปที่: **http://localhost:8000**

## 📖 วิธีการใช้งาน

### ผ่าน Web Interface

1. เปิดเบราว์เซอร์ไปที่ http://localhost:8000
2. เลือกไฟล์ Activity Diagram (.xml หรือ .uml) โดย:
   - คลิกที่พื้นที่อัปโหลด หรือ
   - ลากและวางไฟล์ลงในพื้นที่อัปโหลด
3. คลิกปุ่ม "Convert to UPPAAL"
4. รอให้การแปลงเสร็จสิ้น
5. คลิก "Download Result" เพื่อดาวน์โหลดไฟล์ผลลัพธ์

### ผ่าน API

```bash
curl -X POST "http://localhost:8000/convert-xml" \
     -H "accept: application/xml" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_activity_diagram.xml"
```

## 📁 โครงสร้างไฟล์

```
├── Main_Beyone.py      # FastAPI backend หลัก
├── index.html          # Frontend web interface
├── run_server.py       # Script สำหรับรันเซิร์ฟเวอร์
├── requirements.txt    # Python dependencies
├── README.md          # คู่มือการใช้งาน
├── Example_XML/       # ไฟล์ตัวอย่าง
└── Result/           # โฟลเดอร์สำหรับเก็บผลลัพธ์
```

## 🔧 การปรับแต่ง

- **เปลี่ยนพอร์ต**: แก้ไขในไฟล์ `run_server.py` บรรทัดที่มี `port=8000`
- **เปลี่ยน host**: แก้ไขในไฟล์ `run_server.py` บรรทัดที่มี `host="0.0.0.0"`

## 🔍 การทดสอบ

มีไฟล์ตัวอย่างในโฟลเดอร์ `Example_XML/` ที่สามารถใช้ทดสอบได้:
- `AP3.uml`
- `leave request system.uml`
- และอื่น ๆ

## ❗ ข้อกำหนด

- Python 3.7+
- FastAPI
- Uvicorn
- python-multipart

## 🐛 การแก้ไขปัญหา

### ปัญหาที่พบบ่อย:

1. **ไม่สามารถเปิดเบราว์เซอร์ได้**
   - ตรวจสอบว่าเซิร์ฟเวอร์รันแล้ว
   - ลองเข้า http://127.0.0.1:8000 แทน

2. **ไฟล์แปลงไม่ได้**
   - ตรวจสอบรูปแบบไฟล์ว่าเป็น .xml หรือ .uml
   - ตรวจสอบว่าไฟล์เป็น Activity Diagram XML ที่ถูกต้อง

3. **ข้อผิดพลาด Import**
   ```bash
   pip install -r requirements.txt
   ```

## 📞 การสนับสนุน

หากพบปัญหาหรือต้องการความช่วยเหลือ โปรดแจ้งผ่าน Issues ใน repository นี้ 