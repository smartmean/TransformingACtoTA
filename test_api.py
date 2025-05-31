import requests

def test_convert_xml(filename="Full_Node_simple.xml"):
    """ทดสอบการแปลง XML"""
    url = "http://localhost:8000/convert-xml"
    
    # อ่านไฟล์ XML
    filepath = f"Example_XML/{filename}"
    with open(filepath, "rb") as f:
        files = {"file": (filename, f, "text/xml")}
        
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ การแปลงสำเร็จ!")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            print(f"Output file: {result.get('output_file')}")
            print(f"Download URL: {result.get('download_url')}")
            return True
        else:
            print(f"❌ เกิดข้อผิดพลาด: {response.status_code}")
            print(response.text)
            return False

if __name__ == "__main__":
    try:
        print("🧪 ทดสอบกับไฟล์ขนาดเล็ก...")
        test_convert_xml("Demo_main_decision.xml")
        
        print("\n🧪 ทดสอบกับไฟล์ขนาดใหญ่...")
        test_convert_xml("Full_Node_simple.xml")
        
    except Exception as e:
        print(f"❌ ข้อผิดพลาด: {e}") 