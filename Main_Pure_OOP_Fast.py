"""
High-Performance Pure OOP FastAPI Application
ใช้ optimized infrastructure components เพื่อประสิทธิภาพสูงสุด
"""
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, Response
import traceback
import os
import time

# Import Fast OOP components
from domain.interfaces import IConverter
from application.xml_converter_fast import FastXmlConverter

app = FastAPI()

class FastXmlConverterWrapper(IConverter):
    """
    High-Performance wrapper implementation 
    ใช้ optimized converter สำหรับความเร็วสูงสุด
    """
    
    def __init__(self):
        # ใช้ fast converter ที่ปรับปรุงประสิทธิภาพแล้ว
        self.fast_converter = FastXmlConverter()
        
    def convert(self, xml_content: str) -> str:
        """แปลง XML content เป็น Timed Automata XML โดยใช้ high-performance architecture"""
        try:
            start_time = time.time()
            result = self.fast_converter.convert(xml_content)
            end_time = time.time()
            print(f"⚡ Fast conversion completed in {end_time - start_time:.4f} seconds")
            return result
            
        except Exception as e:
            raise ValueError(f"Fast conversion failed: {str(e)}")

# Serve the HTML file at root
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(
            "<h1>Frontend not found</h1><p>Please ensure index.html exists in the same directory.</p>", 
            status_code=404
        )

@app.post("/convert-xml-fast")
async def convert_xml_fast(file: UploadFile = File(...)):
    """
    High-Performance API Endpoint สำหรับการแปลง Activity Diagram XML เป็น Timed Automata XML
    ใช้ optimized Pure OOP architecture
    """
    try:
        # วัดเวลาการอ่านไฟล์
        start_time = time.time()
        
        # อ่านไฟล์ XML
        contents = await file.read()
        xml_content = contents.decode('utf-8')
        read_time = time.time()
        
        # สร้าง fast converter instance
        converter = FastXmlConverterWrapper()
        
        # แปลง XML
        ta_xml = converter.convert(xml_content)
        conversion_time = time.time()
        
        print(f"📁 File read time: {read_time - start_time:.4f}s")
        print(f"⚙️ Conversion time: {conversion_time - read_time:.4f}s")
        print(f"🚀 Total time: {conversion_time - start_time:.4f}s")
        
        # คืนผลลัพธ์เป็น XML response
        return Response(content=ta_xml, media_type="application/xml")
        
    except UnicodeDecodeError as e:
        return {"error": f"File encoding error: {str(e)}"}
    except ValueError as e:
        return {"error": f"Conversion error: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
        return {"error": f"Unexpected error: {str(e)}"}

@app.post("/convert-xml")
async def convert_xml_original(file: UploadFile = File(...)):
    """
    Original API Endpoint สำหรับเปรียบเทียบประสิทธิภาพ
    """
    try:
        from application.xml_converter import xmlConverter as OriginalConverter
        
        start_time = time.time()
        
        # อ่านไฟล์ XML
        contents = await file.read()
        xml_content = contents.decode('utf-8')
        read_time = time.time()
        
        # สร้าง original converter instance
        converter = OriginalConverter()
        
        # แปลง XML
        ta_xml = converter.convert(xml_content)
        conversion_time = time.time()
        
        print(f"📁 Original - File read time: {read_time - start_time:.4f}s")
        print(f"⚙️ Original - Conversion time: {conversion_time - read_time:.4f}s")
        print(f"🐌 Original - Total time: {conversion_time - start_time:.4f}s")
        
        # คืนผลลัพธ์เป็น XML response
        return Response(content=ta_xml, media_type="application/xml")
        
    except Exception as e:
        print(f"Original converter error: {str(e)}")
        return {"error": f"Original conversion error: {str(e)}"}

if __name__ == "__main__":
    """Command line usage สำหรับการทำงานแบบ standalone และเปรียบเทียบประสิทธิภาพ"""
    import os
    from application.xml_converter import xmlConverter as OriginalConverter
    
    # Define input and output folders
    input_file = "Example_XML/Demo_fork2_simple.xml"
    base_output_file = "Result/Result_Fast_OOP"
    base_original_file = "Result/Result_Original_OOP"
    
    # Create Result directory if it doesn't exist
    os.makedirs("Result", exist_ok=True)
    
    # Find next available file number
    counter = 1
    while os.path.exists(f"{base_output_file}_{counter}.xml"):
        counter += 1
    
    fast_output_file = f"{base_output_file}_{counter}.xml"
    original_output_file = f"{base_original_file}_{counter}.xml"
    
    try:
        # Read the input XML file
        with open(input_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        print("🚀 Starting Performance Comparison...")
        print("=" * 50)
        
        # Test Fast Converter
        print("⚡ Testing Fast Converter...")
        fast_start = time.time()
        fast_converter = FastXmlConverterWrapper()
        fast_ta_xml = fast_converter.convert(xml_content)
        fast_end = time.time()
        fast_time = fast_end - fast_start
        
        # Write fast result
        with open(fast_output_file, 'w', encoding='utf-8') as f:
            f.write(fast_ta_xml)
        
        print("🐌 Testing Original Converter...")
        original_start = time.time()
        original_converter = OriginalConverter()
        original_ta_xml = original_converter.convert(xml_content)
        original_end = time.time()
        original_time = original_end - original_start
        
        # Write original result
        with open(original_output_file, 'w', encoding='utf-8') as f:
            f.write(original_ta_xml)
        
        # Performance Summary
        print("=" * 50)
        print("📊 PERFORMANCE COMPARISON RESULTS:")
        print("=" * 50)
        print(f"⚡ Fast Converter:     {fast_time:.4f} seconds")
        print(f"🐌 Original Converter: {original_time:.4f} seconds")
        
        if fast_time > 0:
            speed_improvement = original_time / fast_time
            time_saved = original_time - fast_time
            print(f"🚀 Speed Improvement:  {speed_improvement:.2f}x faster")
            print(f"⏱️ Time Saved:         {time_saved:.4f} seconds")
        else:
            print(f"🚀 Speed Improvement:  Very fast (< 0.0001s)")
            print(f"⏱️ Time Saved:         {original_time:.4f} seconds")
            
        print("=" * 50)
        
        # File size comparison
        fast_size = os.path.getsize(fast_output_file)
        original_size = os.path.getsize(original_output_file)
        
        print("📁 FILE SIZE COMPARISON:")
        print(f"⚡ Fast Output:     {fast_size:,} bytes")
        print(f"🐌 Original Output: {original_size:,} bytes")
        
        print(f"✅ Fast result saved to: {fast_output_file}")
        print(f"✅ Original result saved to: {original_output_file}")
        
        # Quick validation
        print("\n🔍 QUICK VALIDATION:")
        print(f"⚡ Fast converter generated {len(fast_ta_xml.split('<location'))-1} locations")
        print(f"🐌 Original converter generated {len(original_ta_xml.split('<location'))-1} locations")
        
    except Exception as e:
        print(f"❌ Performance test error: {str(e)}")
        print(traceback.format_exc()) 