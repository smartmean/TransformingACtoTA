from fastapi import FastAPI, File, UploadFile
import xml.etree.ElementTree as ET
from fastapi.responses import Response

app = FastAPI()

class UppaalConverter:
    """ แปลง Activity Diagram XML → UPPAAL XML """

    def __init__(self):
        """ กำหนดค่าเริ่มต้นของ XML """
        self.nta = ET.Element("nta")
        self.declarations = ["clock t;"]  # ✅ เก็บค่าของ declaration
        self.templates = []  # ✅ เก็บหลาย template

    def add_declaration(self, text):
        """ ✅ เพิ่ม <declaration> """
        self.declarations.append(text)

    def create_template(self, name="Template"):
        """ ✅ สร้าง <template> และคืนค่าเป็น dict """
        template = ET.Element("template")
        ET.SubElement(template, "name").text = name
        ET.SubElement(template, "declaration").text = "// Local Declarations"
        self.templates.append({"name": name, "element": template, "state_map": {}, "id_counter": 0})
        return self.templates[-1]  # ✅ คืนค่า template ล่าสุด

    def add_location(self, template, node_id, node_name):
        """ ✅ เพิ่ม <location> ลงใน template """
        template["state_map"][node_id] = f"id{template['id_counter']}"
        location = ET.SubElement(template["element"], "location", id=template["state_map"][node_id])
        ET.SubElement(location, "name").text = node_name.split(",")[0].replace(" ", "_")
        template["id_counter"] += 1  # ✅ เพิ่มค่า ID

    def add_transition(self, template, source_id, target_id):
        """ ✅ เพิ่ม <transition> ลงใน template """
        source = template["state_map"].get(source_id)
        target = template["state_map"].get(target_id)
        if source and target:
            transition = ET.SubElement(template["element"], "transition")
            ET.SubElement(transition, "source", ref=source)
            ET.SubElement(transition, "target", ref=target)

    def generate_xml(self):
        """ ✅ รวมค่าทั้งหมดและสร้าง XML """
        # ✅ เพิ่ม Declaration
        for text in self.declarations:
            ET.SubElement(self.nta, "declaration").text = text

        # ✅ เพิ่ม Template
        for template in self.templates:
            self.nta.append(template["element"])

        # ✅ เพิ่ม System และ Queries
        ET.SubElement(self.nta, "system").text = "system " + ", ".join([t["name"] for t in self.templates]) + ";"
        queries = ET.SubElement(self.nta, "queries")
        query = ET.SubElement(queries, "query")
        ET.SubElement(query, "formula")
        ET.SubElement(query, "comment")

        return ET.tostring(self.nta, encoding="utf-8").decode()

@app.post("/convert-xml")
async def convert_xml(file: UploadFile = File(...)):
    try:
        # ✅ โหลด XML ที่อัปโหลด
        contents = await file.read()
        activity_root = ET.fromstring(contents)

        # ✅ สร้าง Class สำหรับแปลงข้อมูล
        converter = UppaalConverter()

        # ✅ สร้าง Template หลัก
        main_template = converter.create_template("MainTemplate")

        # ✅ ค้นหา Nodes และเพิ่ม Location
        for element in activity_root.findall(".//node"):
            converter.add_location(main_template, element.get("xmi:id"), element.get("name", "unnamed"))

        # ✅ ค้นหา Edges และเพิ่ม Transition
        for element in activity_root.findall(".//edge"):
            converter.add_transition(main_template, element.get("source"), element.get("target"))

        # ✅ แปลง XML
        uppaal_xml = converter.generate_xml()

        # ✅ ส่งกลับ XML เป็น Response
        return Response(content=uppaal_xml, media_type="application/xml")

    except Exception as e:
        return {"error": str(e)}
