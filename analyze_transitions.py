import xml.etree.ElementTree as ET

def analyze_transition_labels(file_path, version_name):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        print(f'\n🔍 TRANSITION LABELS ANALYSIS - {version_name}')
        print('='*80)
        
        templates = root.findall('.//template')
        
        for template in templates:
            template_name_elem = template.find('name')
            template_name = template_name_elem.text if template_name_elem is not None else 'Unknown'
            
            transitions = template.findall('.//transition')
            if not transitions:
                continue
                
            print(f'\n📋 TEMPLATE: {template_name} ({len(transitions)} transitions)')
            print('-' * 60)
            
            for i, transition in enumerate(transitions, 1):
                source_elem = transition.find('source')
                target_elem = transition.find('target')
                source_ref = source_elem.get('ref') if source_elem is not None else 'Unknown'
                target_ref = target_elem.get('ref') if target_elem is not None else 'Unknown'
                
                print(f'\n  🔄 Transition {i}: {source_ref[:8]}... → {target_ref[:8]}...')
                
                labels = transition.findall('label')
                if labels:
                    for label in labels:
                        kind = label.get('kind', 'unknown')
                        text = label.text or ''
                        x = label.get('x', '0')
                        y = label.get('y', '0')
                        
                        # สีแยกตาม kind
                        if kind == 'guard':
                            print(f'     🛡️  Guard: "{text}" at ({x}, {y})')
                        elif kind == 'assignment':
                            print(f'     📝 Assignment: "{text}" at ({x}, {y})')
                        elif kind == 'select':
                            print(f'     🎯 Select: "{text}" at ({x}, {y})')
                        elif kind == 'synchronisation':
                            print(f'     🔗 Sync: "{text}" at ({x}, {y})')
                        else:
                            print(f'     ❓ {kind}: "{text}" at ({x}, {y})')
                else:
                    print(f'     ⚪ No labels')
        
        print(f'\n✅ Analysis complete for {version_name}')
        
    except Exception as e:
        print(f'❌ Error analyzing {file_path}: {str(e)}')

def compare_transition_counts():
    print('\n📊 TRANSITION COUNTS COMPARISON')
    print('='*80)
    
    files = [
        ('Result/Result_5.xml', 'REFACTOR VERSION (LocationBuilder)'),
        ('Result/Result_8.xml', 'ORIGINAL VERSION (UppaalConverter)')
    ]
    
    for file_path, version_name in files:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            templates = root.findall('.//template')
            
            total_transitions = 0
            guard_count = 0
            assignment_count = 0
            select_count = 0
            sync_count = 0
            
            for template in templates:
                template_name_elem = template.find('name')
                template_name = template_name_elem.text if template_name_elem is not None else 'Unknown'
                
                transitions = template.findall('.//transition')
                total_transitions += len(transitions)
                
                for transition in transitions:
                    labels = transition.findall('label')
                    for label in labels:
                        kind = label.get('kind', 'unknown')
                        if kind == 'guard':
                            guard_count += 1
                        elif kind == 'assignment':
                            assignment_count += 1
                        elif kind == 'select':
                            select_count += 1
                        elif kind == 'synchronisation':
                            sync_count += 1
            
            print(f'\n{version_name}:')
            print(f'  Total transitions: {total_transitions}')
            print(f'  🛡️  Guard labels: {guard_count}')
            print(f'  📝 Assignment labels: {assignment_count}')
            print(f'  🎯 Select labels: {select_count}')
            print(f'  🔗 Sync labels: {sync_count}')
            
        except Exception as e:
            print(f'❌ Error analyzing {file_path}: {str(e)}')

# Main execution
if __name__ == "__main__":
    print('Starting detailed transition labels comparison...')
    
    # Compare overall counts first
    compare_transition_counts()
    
    # Detailed analysis
    analyze_transition_labels('Result/Result_5.xml', 'REFACTOR VERSION (LocationBuilder)')
    analyze_transition_labels('Result/Result_8.xml', 'ORIGINAL VERSION (UppaalConverter)')
    
    print('\n🎯 COMPARISON COMPLETE!') 