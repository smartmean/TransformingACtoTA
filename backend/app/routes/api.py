from fastapi import APIRouter, File, UploadFile
from fastapi.responses import HTMLResponse, Response
import xml.etree.ElementTree as ET
import traceback
import os
from ..services.converter import XmlConverter
from ..config import Settings

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the HTML frontend"""
    try:
        # Look for index.html in frontend directory
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "frontend", "index.html")
        if os.path.exists(frontend_path):
            with open(frontend_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return HTMLResponse(
                "<h1>Frontend not found</h1><p>Please ensure index.html exists in the frontend directory.</p>", 
                status_code=404
            )
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading frontend</h1><p>{str(e)}</p>", status_code=500)

@router.post("/convert-xml-download")
async def convert_xml_download(file: UploadFile = File(...)):
    """API endpoint ที่ส่ง XML content กลับโดยตรง"""
    try:
        contents = await file.read()
        activity_root = ET.fromstring(contents)

        converter = XmlConverter()
        converter.set_activity_root(activity_root)
        main_template = converter.process_nodes()

        # Initialize variables
        converter.template_manager.created_transitions = set()
        
        # Generate UPPAAL XML
        result_xml = converter.generate_xml()
        
        # ตรวจสอบและแก้ไข main template transitions
        converter.validate_main_template_transitions()
        
        # Generate UPPAAL XML อีกครั้งหลังแก้ไข
        result_xml = converter.generate_xml()
        
        # แสดงสรุป DeclarationManager
        converter.template_manager.declaration_manager.print_summary()
        
        # Write to output file
        output_filename = f"{Settings.RESULT_DIR}/Result_{len(converter.template_manager.templates)}.xml"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(result_xml)
        
        # ส่ง XML content กลับโดยตรง
        return Response(
            content=result_xml, 
            media_type="application/xml", 
            headers={
                "Content-Disposition": f"attachment; filename={file.filename.replace('.xml', '_converted.xml')}"
            }
        )

    except ET.ParseError as e:
        return {"error": f"XML parsing error: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
        return {"error": f"Unexpected error: {str(e)}"}

@router.post("/convert-xml")
async def convert_xml(file: UploadFile = File(...)):
    """API endpoint สำหรับแปลง XML และส่งผลลัพธ์กลับ"""
    try:
        contents = await file.read()
        activity_root = ET.fromstring(contents)

        converter = XmlConverter()
        converter.set_activity_root(activity_root)
        main_template = converter.process_nodes()

        # Initialize variables
        converter.template_manager.created_transitions = set()
        
        # Generate UPPAAL XML
        result_xml = converter.generate_xml()
        
        # ตรวจสอบและแก้ไข main template transitions
        converter.validate_main_template_transitions()
        
        # Generate UPPAAL XML อีกครั้งหลังแก้ไข
        result_xml = converter.generate_xml()
        
        # แสดงโครงสร้าง main template
        converter.print_main_template_structure()
        
        # วิเคราะห์ fork templates
        converter.print_fork_templates_analysis()
        
        # ตรวจสอบความครบถ้วนของ fork templates
        converter.validate_fork_template_coverage()
        
        # แสดงสรุป DeclarationManager
        converter.template_manager.declaration_manager.print_summary()
        
        # Write to output file
        output_filename = f"{Settings.RESULT_DIR}/Result_{len(converter.template_manager.templates)}.xml"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(result_xml)
            
        return {"result": "Conversion successful"}

    except ET.ParseError as e:
        return {"error": f"XML parsing error: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
        return {"error": f"Unexpected error: {str(e)}"} 