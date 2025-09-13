#!/usr/bin/env python3
"""
Unified Lookup System for DPP LCA Engine
========================================

Hierarchie priorit:
1. EXISTING knowledge/ maps (ručně kurované, nejvyšší kvalita)
2. ILCD master mappings (automaticky scraped)  
3. PEFCR defaults (fallback values)

Usage:
    python unified_lookup_system.py
"""

import pandas as pd
import json
import os
from pathlib import Path

class UnifiedLookupSystem:
    def __init__(self, project_root="/Users/jakubjamny/Documents/GitHub/PEF_AI"):
        self.project_root = Path(project_root)
        self.knowledge_dir = self.project_root / "knowledge"
        self.output_dir = self.project_root / "output"
        
        # Storage for loaded maps
        self.knowledge_maps = {}
        self.ilcd_maps = {}
        self.pefcr_defaults = {}
        self.unified_lookup = {}
        
        print(f"🚀 Initializing Unified Lookup System")
        print(f"📁 Project root: {self.project_root}")
        
    def load_knowledge_maps(self):
        """Load existing knowledge/ CSV files (Priority 1)"""
        print("\n📚 Loading existing knowledge/ maps...")
        
        knowledge_files = {
            'pack_lci_map': 'pack_lci_map.csv',
            'lci_map': 'lci_map.csv', 
            'use_phase_map': 'use_phase_map.csv'
        }
        
        for map_name, filename in knowledge_files.items():
            filepath = self.knowledge_dir / filename
            if filepath.exists():
                df = pd.read_csv(filepath)
                self.knowledge_maps[map_name] = df
                print(f"  ✅ {map_name}: {len(df)} records")
                print(f"     Columns: {list(df.columns)}")
            else:
                print(f"  ❌ {filename} not found")
                
    def load_ilcd_maps(self):
        """Load scraped ILCD mappings (Priority 2)"""
        print("\n🔍 Loading ILCD master mappings...")
        
        # Master mapping
        master_file = self.output_dir / "mappings" / "master_lci_map_extended.csv"
        if master_file.exists():
            df = pd.read_csv(master_file)
            self.ilcd_maps['master'] = df
            print(f"  ✅ Master ILCD: {len(df)} records")
            
        # Category-specific mappings
        mapping_dir = self.output_dir / "mappings"
        if mapping_dir.exists():
            for csv_file in mapping_dir.glob("*_lci_map_extended.csv"):
                if csv_file.name != "master_lci_map_extended.csv":
                    category = csv_file.stem.replace("_lci_map_extended", "")
                    df = pd.read_csv(csv_file)
                    self.ilcd_maps[category] = df
                    print(f"  ✅ {category}: {len(df)} records")
    
    def load_pefcr_defaults(self):
        """Load PEFCR defaults (Priority 3)"""
        print("\n📋 Loading PEFCR defaults...")
        
        # TODO: Parse Defaults.xlsx file
        defaults_file = self.project_root / "Defaults.xlsx"
        if defaults_file.exists():
            # Load different sheets
            try:
                pefcr_sheets = pd.read_excel(defaults_file, sheet_name=None)
                for sheet_name, df in pefcr_sheets.items():
                    self.pefcr_defaults[sheet_name] = df
                    print(f"  ✅ {sheet_name}: {len(df)} records")
            except Exception as e:
                print(f"  ❌ Error loading PEFCR defaults: {e}")
        else:
            print(f"  ❌ Defaults.xlsx not found")
    
    def analyze_overlaps(self):
        """Analyze overlaps between different mapping sources"""
        print("\n🔍 Analyzing overlaps between mapping sources...")
        
        # Compare UUIDs across sources
        knowledge_uuids = set()
        ilcd_uuids = set()
        
        # Extract UUIDs from knowledge maps
        for map_name, df in self.knowledge_maps.items():
            if 'uuid' in df.columns:
                uuids = set(df['uuid'].dropna())
                knowledge_uuids.update(uuids)
                print(f"  📚 {map_name}: {len(uuids)} UUIDs")
        
        # Extract UUIDs from ILCD maps
        if 'master' in self.ilcd_maps:
            master_df = self.ilcd_maps['master']
            if 'uuid' in master_df.columns:
                ilcd_uuids = set(master_df['uuid'].dropna())
                print(f"  🔍 ILCD master: {len(ilcd_uuids)} UUIDs")
        
        # Calculate overlaps
        overlap = knowledge_uuids.intersection(ilcd_uuids)
        knowledge_only = knowledge_uuids - ilcd_uuids
        ilcd_only = ilcd_uuids - knowledge_uuids
        
        print(f"\n📊 Overlap Analysis:")
        print(f"  🔄 Overlapping UUIDs: {len(overlap)}")
        print(f"  📚 Knowledge-only UUIDs: {len(knowledge_only)}")
        print(f"  🔍 ILCD-only UUIDs: {len(ilcd_only)}")
        
        return {
            'overlap': overlap,
            'knowledge_only': knowledge_only,
            'ilcd_only': ilcd_only
        }
    
    def create_unified_lookup(self):
        """Create unified lookup table with priority hierarchy"""
        print("\n🔨 Creating unified lookup table...")
        
        unified_records = []
        
        # Priority 1: Knowledge maps
        for map_name, df in self.knowledge_maps.items():
            for _, row in df.iterrows():
                record = {
                    'source': f'knowledge_{map_name}',
                    'priority': 1,
                    'uuid': row.get('uuid', ''),
                    'material_code': row.get('material_code', row.get('key', '')),
                    'dataset_name': row.get('dataset_name', ''),
                    'lci_file': row.get('lci_file', row.get('ilcd_file', '')),
                    'fu_amount': row.get('fu_amount', 1),
                    'fu_unit': row.get('fu_unit', ''),
                    'region': row.get('region', 'GLO'),
                    'notes': row.get('notes', ''),
                    'raw_data': row.to_dict()
                }
                unified_records.append(record)
        
        # Priority 2: ILCD master (only non-overlapping)
        overlap_analysis = self.analyze_overlaps()
        
        if 'master' in self.ilcd_maps:
            master_df = self.ilcd_maps['master']
            for _, row in master_df.iterrows():
                uuid = row.get('uuid', '')
                # Only add if not already in knowledge maps
                if uuid not in overlap_analysis['overlap']:
                    record = {
                        'source': 'ilcd_master',
                        'priority': 2,
                        'uuid': uuid,
                        'material_code': '', # TBD - needs mapping logic
                        'dataset_name': row.get('name', ''),
                        'lci_file': f"processes/{uuid}.xml",
                        'fu_amount': 1,
                        'fu_unit': row.get('reference_unit', ''),
                        'region': row.get('geography', 'GLO'),
                        'notes': f"Category: {row.get('category', 'unknown')}",
                        'raw_data': row.to_dict()
                    }
                    unified_records.append(record)
        
        # Priority 3: PEFCR defaults
        # TODO: Process PEFCR defaults and add as priority 3
        
        # Create DataFrame
        self.unified_lookup = pd.DataFrame(unified_records)
        print(f"  ✅ Created unified lookup with {len(unified_records)} records")
        
        # Save to file
        output_file = self.output_dir / "unified_lookup_table.csv"
        self.unified_lookup.to_csv(output_file, index=False)
        print(f"  💾 Saved to: {output_file}")
        
        return self.unified_lookup
    
    def lookup_process(self, material_code=None, uuid=None, category=None, region="EU"):
        """
        Unified process lookup with priority hierarchy
        
        Args:
            material_code: e.g. 'pack_cardboard', 'tex_cotton_conv'
            uuid: ILCD process UUID
            category: e.g. 'materials', 'packaging', 'use_phase'
            region: Geographic region
            
        Returns:
            Best matching process record or None
        """
        if self.unified_lookup.empty:
            print("❌ Unified lookup table not loaded. Run create_unified_lookup() first.")
            return None
            
        # Search by UUID (most specific)
        if uuid:
            matches = self.unified_lookup[self.unified_lookup['uuid'] == uuid]
            if not matches.empty:
                return matches.iloc[0].to_dict()
        
        # Search by material_code
        if material_code:
            matches = self.unified_lookup[
                self.unified_lookup['material_code'].str.contains(material_code, na=False)
            ]
            if not matches.empty:
                # Sort by priority (1 = highest)
                matches = matches.sort_values('priority')
                return matches.iloc[0].to_dict()
        
        # Search by category (fuzzy)
        if category:
            matches = self.unified_lookup[
                self.unified_lookup['notes'].str.contains(category, na=False, case=False)
            ]
            if not matches.empty:
                matches = matches.sort_values('priority')
                return matches.iloc[0].to_dict()
                
        return None
    
    def generate_summary_report(self):
        """Generate summary report of unified lookup system"""
        print("\n📊 UNIFIED LOOKUP SYSTEM SUMMARY")
        print("=" * 50)
        
        # Source breakdown
        if not self.unified_lookup.empty:
            source_counts = self.unified_lookup['source'].value_counts()
            print("\n📁 Records by source:")
            for source, count in source_counts.items():
                print(f"  {source}: {count}")
        
        # Priority breakdown
        if not self.unified_lookup.empty:
            priority_counts = self.unified_lookup['priority'].value_counts().sort_index()
            print("\n🏆 Records by priority:")
            for priority, count in priority_counts.items():
                priority_name = {1: "Knowledge Maps", 2: "ILCD Master", 3: "PEFCR Defaults"}.get(priority, "Unknown")
                print(f"  Priority {priority} ({priority_name}): {count}")
        
        print(f"\n📈 Total unified records: {len(self.unified_lookup) if not self.unified_lookup.empty else 0}")

def main():
    # Initialize system
    lookup_system = UnifiedLookupSystem()
    
    # Load all mapping sources
    lookup_system.load_knowledge_maps()
    lookup_system.load_ilcd_maps()
    lookup_system.load_pefcr_defaults()
    
    # Analyze overlaps
    lookup_system.analyze_overlaps()
    
    # Create unified lookup
    lookup_system.create_unified_lookup()
    
    # Add flow UUIDs (critical for CF lookups)
    lookup_system.add_flow_uuids_to_lookup()
    
    # Validate completeness for R2/R3
    lookup_system.validate_completeness_for_r2r3()
    
    # Generate summary
    lookup_system.generate_summary_report()
    
    # Test lookup functionality
    print("\n🧪 Testing lookup functionality...")
    
    # Test cases
    test_cases = [
        {"material_code": "pack_cardboard", "desc": "Packaging cardboard"},
        {"uuid": "d05c4b39-2e68-43bb-9875-fba8fd1333a6", "desc": "Specific UUID lookup"},
        {"category": "washing", "desc": "Use phase washing"},
    ]
    
    for test in test_cases:
        print(f"\n  🔍 Test: {test['desc']}")
        result = lookup_system.lookup_process(**{k:v for k,v in test.items() if k != 'desc'})
        if result:
            print(f"    ✅ Found: {result['dataset_name'][:60]}...")
            print(f"    📍 Source: {result['source']} (Priority {result['priority']})")
        else:
            print(f"    ❌ No match found")

if __name__ == "__main__":
    main()