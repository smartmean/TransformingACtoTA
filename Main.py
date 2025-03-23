from fastapi import FastAPI, File, UploadFile  # type: ignore
import xml.etree.ElementTree as ET
from fastapi.responses import Response  # type: ignore

app = FastAPI()

class UppaalConverter:
    """ แปลง Activity Diagram XML → UPPAAL XML """

    def __init__(self):
        self.nta = ET.Element("nta")
        self.declarations = ["clock t;"]
        self.templates = []

    def add_declaration(self, text):
        self.declarations.append(text)

    def create_template(self, name="Template"):
        template = ET.Element("template")
        ET.SubElement(template, "name").text = name
        ET.SubElement(template, "declaration").text = "// Local declarations\nclock t;"
        self.templates.append({
            "name": name,
            "element": template,
            "state_map": {},
            "id_counter": 0,
            "x_offset": 0,
            "position_map": {},
            "initial_id": None
        })
        return self.templates[-1]

    def add_location(self, template, node_id, node_name, node_type):
        loc_id = f"id{template['id_counter']}"
        template['state_map'][node_id] = loc_id

        x = template['x_offset']
        y = 100
        template['position_map'][node_id] = (x, y)

        location = ET.SubElement(template["element"], "location", id=loc_id, x=str(x), y=str(y))
        label_name = node_name.split(",")[0].replace(" ", "_")
        ET.SubElement(location, "name", x=str(x - 50), y=str(y - 30)).text = label_name

        if node_type in ("uml:InitialNode", "InitialNode"):
            template["initial_id"] = loc_id

        template['id_counter'] += 1
        template['x_offset'] += 150

    def add_transition(self, template, source_id, target_id, source_name="", target_name=""):
        source = template["state_map"].get(source_id)
        target = template["state_map"].get(target_id)
        if source and target:
            trans_id = f"id{template['id_counter']}"
            transition = ET.SubElement(template["element"], "transition", id=trans_id)
            ET.SubElement(transition, "source", ref=source)
            ET.SubElement(transition, "target", ref=target)
            template['id_counter'] += 1

            x1, y1 = template["position_map"].get(source_id, (0, 0))
            x2, y2 = template["position_map"].get(target_id, (0, 0))
            x_mid = (x1 + x2) // 2
            y_mid = (y1 + y2) // 2

            if "," in source_name and "t=" in source_name:
                try:
                    time_val = int(source_name.split("t=")[-1].strip())
                    ET.SubElement(transition, "label", kind="guard", x=str(x_mid), y=str(y_mid - 25)).text = f"t>{time_val}"
                    ET.SubElement(transition, "label", kind="assignment", x=str(x_mid), y=str(y_mid)).text = "t:=0"
                except:
                    pass

    def generate_xml(self):
        for text in self.declarations:
            ET.SubElement(self.nta, "declaration").text = text

        for template in self.templates:
            element = template["element"]

            # Extract and remove children
            name_el = element.find("name")
            decl_el = element.find("declaration")
            locations = element.findall("location")
            transitions = element.findall("transition")

            for child in list(element):
                element.remove(child)

            # Append name and declaration
            if name_el is not None:
                element.append(name_el)
            if decl_el is not None:
                element.append(decl_el)

            # Append locations
            for loc in locations:
                element.append(loc)

            # Insert init after locations
            if template["initial_id"] is not None:
                ET.SubElement(element, "init", ref=template["initial_id"])

            # Append transitions
            for trans in transitions:
                element.append(trans)

            self.nta.append(element)

        ET.SubElement(self.nta, "system").text = f"""T1 = {self.templates[0]['name']}();
system T1;"""
        queries = ET.SubElement(self.nta, "queries")
        query = ET.SubElement(queries, "query")
        ET.SubElement(query, "formula")
        ET.SubElement(query, "comment")

        raw_xml = ET.tostring(self.nta, encoding="utf-8").decode()
        header = '<?xml version="1.0" encoding="utf-8"?>\n'
        doctype = "<!DOCTYPE nta PUBLIC '-//Uppaal Team//DTD Flat System 1.6//EN' " \
                  "'http://www.it.uu.se/research/group/darts/uppaal/flat-1_6.dtd'>\n"
        return header + doctype + raw_xml


@app.post("/convert-xml")
async def convert_xml(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        activity_root = ET.fromstring(contents)

        converter = UppaalConverter()
        main_template = converter.create_template("Template")

        node_info = {}

        for node in activity_root.findall(".//{*}node"):
            node_id = node.get("{http://www.omg.org/spec/XMI/20131001}id")
            node_name = node.get("name", "unnamed")
            node_type = node.get("{http://www.omg.org/spec/XMI/20131001}type", node.tag.split("}")[-1])
            node_info[node_id] = node_name
            converter.add_location(main_template, node_id, node_name, node_type)

        for edge in activity_root.findall(".//{*}edge"):
            src = edge.get("source")
            tgt = edge.get("target")
            converter.add_transition(
                main_template, src, tgt,
                source_name=node_info.get(src, ""),
                target_name=node_info.get(tgt, "")
            )

        uppaal_xml = converter.generate_xml()
        return Response(content=uppaal_xml, media_type="application/xml")

    except Exception as e:
        return {"error": str(e)}
