"""
Pure OOP FastAPI Application ที่ใช้ infrastructure components เต็มรูปแบบ
ปฏิบัติตาม Clean Architecture และ SOLID principles
ใช้ Complete OOP Converter ที่มี infrastructure components ครบถ้วน
"""
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, Response
import traceback
import os
import time

# Import OOP components - ใช้ architecture แบบแบ่งหน้าที่
from domain.interfaces import IConverter
from application.xml_converter_complete_oop_fixed import CompleteOOPConverterFixed

app = FastAPI()

class xmlConverter(IConverter):
    """
    Complete OOP implementation ที่ใช้ infrastructure components เต็มรูปแบบ (Fixed Version)
    ปฏิบัติตาม Clean Architecture และ SOLID principles
    ใช้ Complete OOP Converter ที่แก้ไขแล้ว (Strategy, Factory, Builder, Repository patterns)
    """
    
    def __init__(self):
        # ใช้ complete OOP converter ที่แก้ไขแล้ว
        self.application_converter = CompleteOOPConverterFixed()
        
    def convert(self, xml_content: str) -> str:
        """แปลง XML content เป็น Timed Automata XML โดยใช้ Complete OOP architecture (Fixed)"""
        try:
            start_time = time.time()
            result = self.application_converter.convert(xml_content)
            end_time = time.time()
            print(f"🏗️ Complete OOP Fixed conversion completed in {end_time - start_time:.4f} seconds")
            
            # แสดงสถิติ OOP architecture
            stats = self.application_converter.get_conversion_stats()
            print(f"📊 Architecture: {stats['architecture']}")
            print(f"🎯 Design Patterns: {len(stats['design_patterns'])} patterns used")
            print(f"🏗️ Infrastructure Components: {len(stats['infrastructure_components'])} components")
            
            return result
            
        except Exception as e:
            raise ValueError(f"Conversion failed: {str(e)}")

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

@app.post("/convert-xml")
async def convert_xml(file: UploadFile = File(...)):
    """
    API Endpoint สำหรับการแปลง Activity Diagram XML เป็น Timed Automata XML
    ใช้ Pure OOP architecture
    """
    try:
        # อ่านไฟล์ XML
        contents = await file.read()
        xml_content = contents.decode('utf-8')
        
        # สร้าง converter instance
        converter = xmlConverter()
        
        # แปลง XML
        ta_xml = converter.convert(xml_content)
        
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

if __name__ == "__main__":
    """Command line usage สำหรับการทำงานแบบ standalone"""
    import os
    
    # Define input and output folders
    input_file = "Example_XML/Demo_fork2_simple2.xml"
    #input_file = "Example_XML/AP2.xml"
    base_output_file = "Result/Result_Pure_OOP"
    
    # Create Result directory if it doesn't exist
    os.makedirs("Result", exist_ok=True)
    
    # Find next available file number
    counter = 1
    while os.path.exists(f"{base_output_file}_{counter}.xml"):
        counter += 1
    
    output_file = f"{base_output_file}_{counter}.xml"
    
    try:
        # Read the input XML file
        with open(input_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Create converter and process
        print(f"🔄 Starting conversion of {input_file}...")
        converter = xmlConverter()
        ta_xml = converter.convert(xml_content)
        
        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(ta_xml)
            
        print(f"Successfully converted {input_file} to {output_file}")
        print(f"📁 Output file size: {len(ta_xml)} characters")
        
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        print(traceback.format_exc()) 