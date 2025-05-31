import xml.etree.ElementTree as ET
from Main_Beyone_fixed import *

# สร้าง converter และ parse XML แบบเดียวกับ main program
with open('Example_XML/Full_Node_simple.xml', 'r', encoding='utf-8') as f:
    contents = f.read()
activity_root = ET.fromstring(contents)

converter = UppaalConverter()
converter.set_activity_root(activity_root) 