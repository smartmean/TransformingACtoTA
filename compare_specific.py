import xml.etree.ElementTree as ET

def compare_decision_logic():
    print("🔍 DECISION LOGIC COMPARISON - MAIN TEMPLATE ONLY")
    print("="*80)
    
    files = [
        ('Result/Result_9.xml', 'REFACTOR VERSION (NEW)'),
        ('Result/Result_8.xml', 'ORIGINAL VERSION')
    ]
    
    for file_path, version_name in files:
        print(f"\n📋 {version_name}:")
        print("-" * 50)
        
        tree = ET.parse(file_path)
        
        # Find main template
        for template in tree.getroot().findall('.//template'):
            name_elem = template.find('name')
            if name_elem is not None and name_elem.text == 'Template':
                
                print(f"Main Template Found - Processing transitions...")
                transitions = template.findall('.//transition')
                
                decision_related = []
                for i, trans in enumerate(transitions, 1):
                    source = trans.find('source').get('ref')
                    target = trans.find('target').get('ref')
                    
                    # Check if involves Decision2
                    labels = trans.findall('label')
                    has_decision_logic = False
                    
                    for label in labels:
                        text = label.text or ''
                        kind = label.get('kind', '')
                        
                        if ('Decision2' in text or 
                            'select' in kind or 
                            ('guard' in kind and ('Decision' in text or '==' in text))):
                            has_decision_logic = True
                            decision_related.append({
                                'transition': i,
                                'source': source[:8] + "...",
                                'target': target[:8] + "...",
                                'kind': kind,
                                'text': text
                            })
                
                print(f"Found {len(decision_related)} decision-related transitions:")
                
                for dr in decision_related:
                    print(f"  T{dr['transition']}: {dr['source']} → {dr['target']}")
                    print(f"    {dr['kind'].upper()}: {dr['text']}")
                
                if not decision_related:
                    print("  ❌ NO DECISION LOGIC FOUND!")
                
                break

if __name__ == "__main__":
    compare_decision_logic() 