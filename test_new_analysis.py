import requests
import json

# Test with Full_Node_simple.xml
url = "http://localhost:8000/convert-xml"

try:
    with open("Example_XML/Full_Node_simple.xml", "rb") as f:
        files = {"file": ("Full_Node_simple.xml", f, "application/xml")}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print("=== CONVERSION RESULT ===")
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        if 'output_file' in result:
            print(f"Output file: {result['output_file']}")
            
            # Check file size
            import os
            if os.path.exists(result['output_file']):
                file_size = os.path.getsize(result['output_file'])
                print(f"File size: {file_size} bytes")
                
                # Read and analyze the result
                with open(result['output_file'], 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    template_count = content.count('<template>')
                    print(f"Generated {template_count} templates")
                    print(f"Total lines: {len(lines)}")
                    
                    # Count templates by name
                    import re
                    template_names = re.findall(r'<name>([^<]+)</name>', content)
                    print(f"Template names: {template_names}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"Test failed: {e}") 