#!/usr/bin/env python3
"""
Analyzátor unknown procesů + rozšířená kategorizace
"""

import pandas as pd
import json
import re
from collections import Counter

def analyze_unknown_processes():
    """Analyzuje unknown procesy pro identifikaci nových kategorií"""
    
    print("Načítám unknown procesy...")
    df = pd.read_csv('output/mappings/master_lci_map_improved.csv')
    unknown = df[df['process_type'] == 'unknown'].copy()
    
    print(f"Analyzuji {len(unknown)} unknown procesů")
    
    # Analyzuj nejčastější termíny
    all_tech = ' '.join(unknown['technology'].fillna('').astype(str))
    words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{4,}\b', all_tech)]
    common_words = Counter(words).most_common(50)
    
    print("\nNejčastější termíny v unknown procesech:")
    for word, count in common_words[:20]:
        print(f"  {word}: {count}x")
    
    # Analyzuj vzorové unknown procesy
    print("\nVzorové unknown procesy:")
    samples = unknown.sample(min(10, len(unknown)))
    for idx, row in samples.iterrows():
        tech = row['technology'][:100] if row['technology'] else 'N/A'
        print(f"  UUID: {row['uuid']}")
        print(f"  Tech: {tech}...")
        print()
    
    return unknown, common_words

def extended_categorization():
    """Rozšířená kategorizace založená na analýze unknown procesů"""
    
    # Načti původní data
    with open('output/analysis/ilcd_master_inventory_improved.json', 'r') as f:
        processes = json.load(f)
    
    print(f"Spouštím rozšířenou kategorizaci pro {len(processes)} procesů...")
    
    def categorize_extended(tech_desc):
        if not tech_desc:
            return "unknown"
        
        desc_lower = tech_desc.lower()
        
        # ROZŠÍŘENÉ KATEGORIE
        
        # CHEMICALS & BASIC MATERIALS
        chemicals_keywords = [
            'chemical', 'acid', 'base', 'polymer', 'resin', 'solvent',
            'catalyst', 'additive', 'compound', 'synthesis', 'reaction',
            'methanol', 'ethanol', 'benzene', 'acetone', 'ammonia'
        ]
        
        # METALS & MINING
        metals_keywords = [
            'steel', 'iron', 'aluminum', 'copper', 'zinc', 'metal',
            'mining', 'extraction', 'smelting', 'casting', 'forging',
            'alloy', 'ore', 'furnace', 'refinery'
        ]
        
        # CONSTRUCTION & BUILDING
        construction_keywords = [
            'concrete', 'cement', 'brick', 'tile', 'window', 'door',
            'construction', 'building', 'infrastructure', 'road',
            'asphalt', 'gravel', 'sand', 'stone'
        ]
        
        # AGRICULTURE & FOOD
        agriculture_keywords = [
            'agriculture', 'farming', 'crop', 'grain', 'wheat', 'corn',
            'fertilizer', 'pesticide', 'food', 'meat', 'dairy',
            'processing', 'harvest', 'irrigation'
        ]
        
        # ELECTRONICS & TECHNOLOGY
        electronics_keywords = [
            'electronic', 'semiconductor', 'silicon', 'chip', 'circuit',
            'computer', 'display', 'battery', 'capacitor', 'resistor',
            'pcb', 'wafer', 'lithium'
        ]
        
        # WATER & UTILITIES
        utilities_keywords = [
            'water', 'wastewater', 'sewage', 'treatment', 'purification',
            'municipal', 'utility', 'infrastructure', 'supply',
            'distribution', 'pipeline'
        ]
        
        # PŮVODNÍ KATEGORIE (s rozšířením)
        
        # PACKAGING (rozšířeno)
        packaging_keywords = [
            'adhesive', 'carton', 'cardboard', 'packaging', 'box', 'container',
            'film', 'bag', 'wrap', 'bottle', 'cap', 'closure', 'label',
            'hot-melt', 'glue', 'tape', 'corrugated', 'polyethylene',
            'polypropylene', 'blister', 'tray', 'pouch'
        ]
        
        # MATERIALS (rozšířeno)
        materials_keywords = [
            'cotton', 'polyester', 'fiber', 'yarn', 'fabric', 'textile',
            'wool', 'silk', 'linen', 'viscose', 'nylon', 'acrylic',
            'spinning', 'weaving', 'knitting', 'dyeing', 'finishing',
            'thread', 'filament', 'staple', 'blend'
        ]
        
        # USE PHASE (rozšířeno)
        use_phase_keywords = [
            'washing', 'drying', 'ironing', 'cleaning', 'laundry',
            'detergent', 'softener', 'stain', 'care', 'maintenance',
            'service', 'operation', 'usage'
        ]
        
        # TRANSPORT (rozšířeno)
        transport_keywords = [
            'transport', 'truck', 'ship', 'plane', 'freight', 'cargo',
            'delivery', 'logistics', 'lorry', 'vessel', 'aircraft',
            'rail', 'train', 'maritime', 'aviation', 'road'
        ]
        
        # END OF LIFE (rozšířeno)
        eol_keywords = [
            'recycling', 'incineration', 'landfill', 'disposal', 'waste',
            'recovery', 'treatment', 'municipal', 'solid waste',
            'composting', 'anaerobic', 'biogas', 'sorting'
        ]
        
        # ENERGY (rozšířeno)
        energy_keywords = [
            'electricity', 'energy', 'power', 'heat', 'steam', 'gas',
            'coal', 'oil', 'nuclear', 'renewable', 'grid', 'solar',
            'wind', 'hydroelectric', 'biomass', 'diesel', 'gasoline'
        ]
        
        # KATEGORIZACE (priorita podle specifičnosti)
        if any(word in desc_lower for word in electronics_keywords):
            return "electronics"
        elif any(word in desc_lower for word in chemicals_keywords):
            return "chemicals"
        elif any(word in desc_lower for word in metals_keywords):
            return "metals"
        elif any(word in desc_lower for word in construction_keywords):
            return "construction"
        elif any(word in desc_lower for word in agriculture_keywords):
            return "agriculture"
        elif any(word in desc_lower for word in utilities_keywords):
            return "utilities"
        elif any(word in desc_lower for word in packaging_keywords):
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
        new_category = categorize_extended(process.get('technology', ''))
        process['process_type'] = new_category
        process['classification'] = new_category
        
        category_counts[new_category] = category_counts.get(new_category, 0) + 1
        updated_processes.append(process)
    
    # Ulož výsledky
    with open('output/analysis/ilcd_master_inventory_extended.json', 'w') as f:
        json.dump(updated_processes, f, indent=2)
    
    df = pd.DataFrame(updated_processes)
    df.to_csv('output/mappings/master_lci_map_extended.csv', index=False)
    
    # Vytvoř kategorizované mappingy
    by_type = df.groupby('process_type')
    
    for process_type, group in by_type:
        if process_type != 'unknown':
            group.to_csv(f'output/mappings/{process_type}_lci_map_extended.csv', index=False)
            print(f"Vytvořeno: {process_type}_lci_map_extended.csv s {len(group)} procesy")
    
    print("\nRozšířená kategorizace - finální souhrn:")
    total_categorized = sum(count for cat, count in category_counts.items() if cat != 'unknown')
    total_processes = len(updated_processes)
    
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_processes) * 100
        print(f"  {category}: {count} procesů ({percentage:.1f}%)")
    
    print(f"\nCelková úspěšnost kategorizace: {total_categorized}/{total_processes} ({(total_categorized/total_processes)*100:.1f}%)")
    
    return updated_processes, category_counts

def main():
    print("🔍 Analýza unknown procesů")
    print("=" * 50)
    
    # Analýza unknown procesů
    unknown_data, common_words = analyze_unknown_processes()
    
    print("\n🔄 Rozšířená kategorizace")
    print("=" * 50)
    
    # Rozšířená kategorizace
    updated_processes, category_counts = extended_categorization()
    
    print(f"\n🎉 Hotovo! Rozšířená kategorizace dokončena.")
    print("\nNové soubory:")
    print("  output/analysis/ilcd_master_inventory_extended.json")
    print("  output/mappings/master_lci_map_extended.csv")
    print("  output/mappings/{category}_lci_map_extended.csv")

if __name__ == "__main__":
    main()
