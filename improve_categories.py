#!/usr/bin/env python3
"""
Vylepšený kategorizátor ILCD procesů - oprava XML parsing + lepší kategorizace
"""

import json
import pandas as pd
import re

def improve_categorization():
    """Vylepší kategorizaci existujících procesů"""
    
    # Načti master inventory
    with open('output/analysis/ilcd_master_inventory.json', 'r') as f:
        processes = json.load(f)
    
    print(f"Načítám {len(processes)} procesů pro rekategorizaci...")
    
    # Vylepšené kategorizační pravidla
    def categorize_process(tech_desc):
        if not tech_desc:
            return "unknown"
        
        desc_lower = tech_desc.lower()
        
        # PACKAGING
        packaging_keywords = [
            'adhesive', 'carton', 'cardboard', 'packaging', 'box', 'container',
            'film', 'bag', 'wrap', 'bottle', 'cap', 'closure', 'label',
            'hot-melt', 'glue', 'tape', 'corrugated'
        ]
        
        # MATERIALS (textile + other)
        materials_keywords = [
            'cotton', 'polyester', 'fiber', 'yarn', 'fabric', 'textile',
            'wool', 'silk', 'linen', 'viscose', 'nylon', 'acrylic',
            'spinning', 'weaving', 'knitting', 'dyeing', 'finishing'
        ]
        
        # USE PHASE
        use_phase_keywords = [
            'washing', 'drying', 'ironing', 'cleaning', 'laundry',
            'detergent', 'softener', 'stain', 'care'
        ]
        
        # TRANSPORT
        transport_keywords = [
            'transport', 'truck', 'ship', 'plane', 'freight', 'cargo',
            'delivery', 'logistics', 'lorry', 'vessel', 'aircraft'
        ]
        
        # END OF LIFE
        eol_keywords = [
            'recycling', 'incineration', 'landfill', 'disposal', 'waste',
            'recovery', 'treatment', 'municipal', 'solid waste'
        ]
        
        # ENERGY & UTILITIES
        energy_keywords = [
            'electricity', 'energy', 'power', 'heat', 'steam', 'gas',
            'coal', 'oil', 'nuclear', 'renewable', 'grid'
        ]
        
        # Kategorizace podle priority
        if any(word in desc_lower for word in packaging_keywords):
            return "packaging"
        elif any(word in desc_lower for word in materials_keywords):
            return "materials"
        elif any(word in desc_lower for word in use_phase_keywords):
            return "use_phase"
        elif any(word in desc_lower for word in transport_keywords):
            return "transport"
        elif any(word in desc_lower for word in eol_keywords):
            return "eol"
        elif any(word in desc_lower for word in energy_keywords):
            return "energy"
        else:
            return "unknown"
    
    # Rekategorizuj všechny procesy
    updated_processes = []
    category_counts = {}
    
    for process in processes:
        # Použij technology field pro kategorizaci
        new_category = categorize_process(process.get('technology', ''))
        process['process_type'] = new_category
        process['classification'] = new_category
        
        # Počítej kategorie
        category_counts[new_category] = category_counts.get(new_category, 0) + 1
        updated_processes.append(process)
    
    # Ulož aktualizované procesy
    with open('output/analysis/ilcd_master_inventory_improved.json', 'w') as f:
        json.dump(updated_processes, f, indent=2)
    
    # Vytvoř aktualizované CSV mappingy
    df = pd.DataFrame(updated_processes)
    
    # Master mapping
    df.to_csv('output/mappings/master_lci_map_improved.csv', index=False)
    
    # Kategorizované mappingy
    by_type = df.groupby('process_type')
    
    for process_type, group in by_type:
        if process_type != 'unknown':  # Přeskočíme unknown
            group.to_csv(f'output/mappings/{process_type}_lci_map_improved.csv', index=False)
            print(f"Vytvořeno: {process_type}_lci_map_improved.csv s {len(group)} procesy")
    
    print("\nVylepšená kategorizace - souhrn:")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count} procesů")
    
    return updated_processes, category_counts

def analyze_sample_processes():
    """Analyzuj vzorové procesy pro pochopení struktury"""
    
    with open('output/analysis/ilcd_master_inventory.json', 'r') as f:
        processes = json.load(f)
    
    print("Analýza vzorových procesů:")
    print("=" * 50)
    
    # Ukázkové procesy s neprázdnou technology
    samples = [p for p in processes if p.get('technology', '').strip()][:10]
    
    for i, process in enumerate(samples):
        print(f"\nProces {i+1}:")
        print(f"  UUID: {process['uuid']}")
        print(f"  Technology: {process['technology'][:100]}...")
        print(f"  Current type: {process['process_type']}")
    
    # Statistiky
    tech_filled = len([p for p in processes if p.get('technology', '').strip()])
    print(f"\nStatistiky:")
    print(f"  Celkem procesů: {len(processes)}")
    print(f"  S technology popisem: {tech_filled}")
    print(f"  Bez popisu: {len(processes) - tech_filled}")

if __name__ == "__main__":
    print("Spouštím vylepšenou kategorizaci ILCD procesů...")
    
    # Analýza vzorových dat
    analyze_sample_processes()
    
    print("\n" + "="*50)
    
    # Vylepšená kategorizace
    updated_processes, category_counts = improve_categorization()
    
    print(f"\nÚspěšně rekategorizováno {len(updated_processes)} procesů!")
    print("\nNové soubory:")
    print("  output/analysis/ilcd_master_inventory_improved.json")
    print("  output/mappings/master_lci_map_improved.csv")
    print("  output/mappings/{category}_lci_map_improved.csv")
