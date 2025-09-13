#!/usr/bin/env python3
"""
ILCD Process Scraper for macOS
Usage: python3 scrape_ilcd_macos.py
"""

import os
import json
import csv
import xml.etree.ElementTree as ET
import pandas as pd
import re
from pathlib import Path

def setup_directories():
    """Create output directories"""
    directories = [
        'output/analysis',
        'output/mappings', 
        'output/pefcr_defaults'
    ]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("📁 Created output directories")

def extract_pefcr_defaults():
    """Extract PEFCR defaults from Excel file"""
    print("📊 Extracting PEFCR defaults from Excel...")
    
    try:
        # Read the Excel file
        excel_file = 'AFW_PEFCR_v3.1_AnnexVII  Inventory modelling and default datasets.xlsx'
        
        # Read the "Default datasets & DQR" sheet
        df = pd.read_excel(excel_file, sheet_name='Default datasets & DQR', header=None)
        
        # Process the data (assuming first row might be headers)
        pefcr_defaults = []
        
        for index, row in df.iterrows():
            if pd.notna(row.iloc[7]) and len(str(row.iloc[7])) > 10:  # UUID column
                pefcr_default = {
                    'category': str(row.iloc[0]) if pd.notna(row.iloc[0]) else 'unknown',
                    'lcs_stage': str(row.iloc[1]) if pd.notna(row.iloc[1]) else '',
                    'material_name': str(row.iloc[2]) if pd.notna(row.iloc[2]) else '',
                    'region': str(row.iloc[3]) if pd.notna(row.iloc[3]) else 'GLO',
                    'dataset_name': str(row.iloc[4]) if pd.notna(row.iloc[4]) else '',
                    'unit': str(row.iloc[5]) if pd.notna(row.iloc[5]) else 'kg',
                    'database': str(row.iloc[6]) if pd.notna(row.iloc[6]) else 'EF Database 3.1',
                    'uuid': str(row.iloc[7]),
                    'dqr_rel': row.iloc[8] if pd.notna(row.iloc[8]) else 2,
                    'dqr_tech': row.iloc[9] if pd.notna(row.iloc[9]) else 2,
                    'dqr_temp': row.iloc[10] if pd.notna(row.iloc[10]) else 2,
                    'dqr_geo': row.iloc[11] if pd.notna(row.iloc[11]) else 2,
                    'dqr_overall': row.iloc[12] if pd.notna(row.iloc[12]) else 2
                }
                pefcr_defaults.append(pefcr_default)
        
        # Save as JSON
        with open('output/pefcr_defaults/pefcr_defaults.json', 'w') as f:
            json.dump(pefcr_defaults, f, indent=2)
        
        # Save as CSV
        pefcr_df = pd.DataFrame(pefcr_defaults)
        pefcr_df.to_csv('output/mappings/pefcr_master_map.csv', index=False)
        
        print(f"✅ Extracted {len(pefcr_defaults)} PEFCR default processes")
        return pefcr_defaults
        
    except Exception as e:
        print(f"⚠️  Could not process Excel file: {e}")
        print("Continuing with ILCD scraping...")
        return []

def extract_process_data(xml_path):
    """Extract data from single ILCD XML process"""
    try:
        # Parse XML
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Extract UUID from filename
        uuid = Path(xml_path).stem
        
        # Extract dataset name (handle namespaces)
        dataset_name = ""
        for elem in root.iter():
            if elem.tag.endswith('name') and elem.text:
                dataset_name = elem.text.strip()
                break
        
        # Extract functional unit
        fu_unit = "kg"
        fu_amount = 1
        for elem in root.iter():
            if elem.tag.endswith('referenceToReferenceUnit') and elem.text:
                fu_unit = elem.text.strip()
                break
        
        # Extract geography
        region = "GLO"
        for elem in root.iter():
            if elem.tag.endswith('locationOfOperationSupplyOrProduction'):
                region = elem.get('location', 'GLO')
                break
        
        # Classify process type based on name
        name_lower = dataset_name.lower()
        process_type = "unknown"
        
        if any(word in name_lower for word in ['packaging', 'carton', 'box', 'film', 'bag']):
            process_type = "packaging"
        elif any(word in name_lower for word in ['cotton', 'polyester', 'fiber', 'yarn', 'fabric']):
            process_type = "materials"
        elif any(word in name_lower for word in ['washing', 'drying', 'ironing', 'cleaning']):
            process_type = "use_phase"
        elif any(word in name_lower for word in ['transport', 'truck', 'ship', 'plane', 'freight']):
            process_type = "transport"
        elif any(word in name_lower for word in ['recycling', 'incineration', 'landfill', 'disposal']):
            process_type = "eol"
        
        # Extract technology description
        technology = ""
        for elem in root.iter():
            if elem.tag.endswith('technologyDescriptionAndIncludedProcesses') and elem.text:
                technology = elem.text.strip()[:100]  # Truncate
                break
        
        # Extract kg_per_m2 for packaging
        kg_per_m2 = ""
        if process_type == "packaging" and technology:
            match = re.search(r'(\d+(?:\.\d+)?)\s*g/m2', technology, re.IGNORECASE)
            if match:
                kg_per_m2 = str(float(match.group(1)) / 1000)  # Convert g/m2 to kg/m2
        
        # Extract temperature for use phase
        temp_c = ""
        if process_type == "use_phase":
            temp_match = re.search(r'(\d+)°?c', name_lower)
            if temp_match:
                temp_c = temp_match.group(1)
            elif 'cold' in name_lower:
                temp_c = "30"
            elif 'hot' in name_lower:
                temp_c = "60"
            else:
                temp_c = "40"  # PEFCR default
        
        return {
            'uuid': uuid,
            'dataset_name': dataset_name.replace('"', '""'),  # Escape quotes
            'process_type': process_type,
            'lci_file': f'processes/{uuid}.xml',
            'fu_amount': fu_amount,
            'fu_unit': fu_unit,
            'region': region,
            'classification': process_type,
            'kg_per_m2': kg_per_m2,
            'temp_c': temp_c,
            'technology': technology,
            'notes': 'scraped_from_ilcd'
        }
        
    except Exception as e:
        print(f"⚠️  Warning: Could not process {xml_path}: {e}")
        return None

def scrape_ilcd_processes():
    """Scrape all ILCD XML processes"""
    print("🔍 Scraping ILCD XML processes...")
    
    processes_dir = Path('data/ilcd/processes')
    if not processes_dir.exists():
        print("❌ processes directory not found. Please ensure data/ilcd/processes exists.")
        return []
    
    xml_files = list(processes_dir.glob('*.xml'))
    print(f"📁 Found {len(xml_files)} XML files to process...")
    
    all_processes = []
    processed = 0
    
    for xml_file in xml_files:
        process_data = extract_process_data(xml_file)
        
        if process_data:
            all_processes.append(process_data)
            processed += 1
            
            if processed % 100 == 0:
                print(f"  📊 Processed {processed}/{len(xml_files)} files...")
    
    print(f"✅ Successfully processed {len(all_processes)} ILCD processes")
    
    # Save master inventory as JSON
    with open('output/analysis/ilcd_master_inventory.json', 'w') as f:
        json.dump(all_processes, f, indent=2)
    
    # Save master mapping CSV
    df = pd.DataFrame(all_processes)
    df.to_csv('output/mappings/master_lci_map.csv', index=False)
    
    # Generate category-specific mappings
    by_type = df.groupby('process_type')
    
    for process_type, group in by_type:
        group.to_csv(f'output/mappings/{process_type}_lci_map.csv', index=False)
        print(f"  📄 Generated {process_type}_lci_map.csv with {len(group)} processes")
    
    print("\n📈 Summary by process type:")
    for process_type, group in by_type:
        print(f"  {process_type}: {len(group)} processes")
    
    return all_processes

def generate_material_codes(processes):
    """Generate systematic material codes"""
    print("🔗 Generating material code mappings...")
    
    material_codes = []
    
    for process in processes:
        name = process['dataset_name'].lower()
        process_type = process['process_type']
        
        # Generate material code based on process type and name
        if process_type == 'packaging':
            if 'cardboard' in name or 'carton' in name:
                material_code = 'pack_card_corr'
            elif 'plastic' in name or 'film' in name:
                material_code = 'pack_plastic_film'
            elif 'paper' in name:
                material_code = 'pack_paper'
            else:
                material_code = f'pack_{process["uuid"][:8]}'
        elif process_type == 'materials':
            if 'cotton' in name:
                material_code = 'tex_cotton_conv'
            elif 'polyester' in name or 'pet' in name:
                material_code = 'tex_pet_virgin'
            elif 'wool' in name:
                material_code = 'tex_wool_virgin'
            else:
                material_code = f'tex_{process["uuid"][:8]}'
        elif process_type == 'use_phase':
            if 'washing' in name:
                material_code = 'use_wash_machine'
            elif 'drying' in name:
                material_code = 'use_dry_machine'
            else:
                material_code = f'use_{process["uuid"][:8]}'
        else:
            material_code = f'{process_type}_{process["uuid"][:8]}'
        
        material_codes.append({
            'material_code': material_code,
            'uuid': process['uuid'],
            'dataset_name': process['dataset_name'],
            'process_type': process['process_type']
        })
    
    # Save material code mapping
    df = pd.DataFrame(material_codes)
    df.to_csv('output/mappings/material_code_map.csv', index=False)
    
    print(f"✅ Generated material codes for {len(material_codes)} processes")

def main():
    """Main execution function"""
    print("🔄 Starting ILCD Process Scraping & Mapping Generation...")
    
    # Setup
    setup_directories()
    
    # Extract PEFCR defaults
    pefcr_defaults = extract_pefcr_defaults()
    
    # Scrape ILCD processes
    ilcd_processes = scrape_ilcd_processes()
    
    # Generate material codes
    if ilcd_processes:
        generate_material_codes(ilcd_processes)
    
    print("\n🎉 ILCD Scraping & Mapping Complete!")
    print("\n📁 Generated files:")
    print("  output/analysis/ilcd_master_inventory.json")
    print("  output/mappings/master_lci_map.csv")
    print("  output/mappings/pefcr_master_map.csv")
    print("  output/mappings/material_code_map.csv")
    print("  output/mappings/{packaging,materials,use_phase,transport,eol}_lci_map.csv")
    print("\n📊 Next steps:")
    print("  1. Review generated mappings")
    print("  2. Merge with existing knowledge/ CSV files")
    print("  3. Update R2/R3 scripts to use master mappings")
    print("  4. Test with sample product data")

if __name__ == "__main__":
    main()
