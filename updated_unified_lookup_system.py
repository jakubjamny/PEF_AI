#!/usr/bin/env python3
"""
Updated Unified Lookup System - Enhanced Data Integration
=======================================================

Integrates enhanced ILCD metadata (4674 processes) with existing knowledge maps.
Hierarchie priorit: knowledge/ (33) → enhanced ILCD (4674) → PEFCR defaults

Usage:
    python updated_unified_lookup_system.py
"""

import pandas as pd
import json
import os
from pathlib import Path

class UpdatedUnifiedLookupSystem:
    def __init__(self, project_root="/Users/jakubjamny/Documents/GitHub/PEF_AI"):
        self.project_root = Path(project_root)
        self.knowledge_dir = self.project_root / "knowledge"
        self.output_dir = self.project_root / "output"
        
        # Storage for loaded maps
        self.knowledge_maps = {}
        self.enhanced_ilcd_data = None
        self.pefcr_defaults = {}
        self.unified_lookup = {}
        
        print(f"🚀 Initializing Updated Unified Lookup System")
        print(f"📁 Project root: {self.project_root}")
        
    def load_knowledge_maps(self):
        """Load existing knowledge/ CSV files (Priority 1)"""
        print(f"\n📚 Loading existing knowledge/ maps...")
        
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
                
    def load_enhanced_ilcd_data(self):
        """Load enhanced ILCD metadata (Priority 2)"""
        print(f"\n🔍 Loading enhanced ILCD metadata...")
        
        enhanced_file = self.output_dir / "enhanced_ilcd_metadata_test.csv"
        if enhanced_file.exists():
            df = pd.read_csv(enhanced_file)
            self.enhanced_ilcd_data = df
            print(f"  ✅ Enhanced ILCD: {len(df)} records")
            print(f"     Columns: {list(df.columns)}")
            
            # Statistics
            mapped_count = len(df[df['material_code'].notna() & (df['material_code'] != '')])
            print(f"     Mapped processes: {mapped_count} ({mapped_count/len(df)*100:.1f}%)")
            
        else:
            print(f"  ❌ enhanced_ilcd_metadata_test.csv not found")
            
    def load_pefcr_defaults(self):
        """Load PEFCR defaults (Priority 3)"""
        print(f"\n📋 Loading PEFCR defaults...")
        
        defaults_file = self.project_root / "Defaults.xlsx"
        if defaults_file.exists():
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
        """Analyze overlaps between knowledge maps and enhanced ILCD data"""
        print(f"\n🔍 Analyzing overlaps between mapping sources...")
        
        # Extract UUIDs from knowledge maps
        knowledge_uuids = set()
        for map_name, df in self.knowledge_maps.items():
            if 'uuid' in df.columns:
                uuids = set(df['uuid'].dropna().astype(str))
                knowledge_uuids.update(uuids)
                print(f"  📚 {map_name}: {len(uuids)} UUIDs")
        
        # Extract UUIDs from enhanced ILCD data
        enhanced_uuids = set()
        if self.enhanced_ilcd_data is not None:
            enhanced_uuids = set(self.enhanced_ilcd_data['uuid'].dropna().astype(str))
            print(f"  🔍 Enhanced ILCD: {len(enhanced_uuids)} UUIDs")
        
        # Calculate overlaps
        overlap = knowledge_uuids.intersection(enhanced_uuids)
        knowledge_only = knowledge_uuids - enhanced_uuids
        enhanced_only = enhanced_uuids - knowledge_uuids
        
        print(f"\n📊 Overlap Analysis:")
        print(f"  🔄 Overlapping UUIDs: {len(overlap)}")
        print(f"  📚 Knowledge-only UUIDs: {len(knowledge_only)}")
        print(f"  🔍 Enhanced-only UUIDs: {len(enhanced_only)}")
        
        return {
            'overlap': overlap,
            'knowledge_only': knowledge_only,
            'enhanced_only': enhanced_only
        }
    
    def create_unified_lookup(self):
        """Create unified lookup table with priority hierarchy"""
        print(f"\n🔨 Creating unified lookup table...")
        
        unified_records = []
        overlap_analysis = self.analyze_overlaps()
        
        # Priority 1: Knowledge maps (highest priority)
        print(f"  📚 Adding Priority 1: Knowledge maps")
        for map_name, df in self.knowledge_maps.items():
            for _, row in df.iterrows():
                # Clean up material_code/key field
                material_code = row.get('material_code', row.get('key', ''))
                if pd.isna(material_code):
                    material_code = ''
                    
                record = {
                    'source': f'knowledge_{map_name}',
                    'priority': 1,
                    'uuid': str(row.get('uuid', '')),
                    'material_code': str(material_code),
                    'dataset_name': str(row.get('dataset_name', row.get('item', ''))),
                    'lci_file': str(row.get('lci_file', row.get('ilcd_file', row.get('file', '')))),
                    'fu_amount': row.get('fu_amount', 1),
                    'fu_unit': str(row.get('fu_unit', 'kg')),
                    'region': str(row.get('region', 'GLO')),
                    'notes': str(row.get('notes', '')),
                    # Enhanced parameters
                    'kg_per_m2': row.get('kg_per_m2'),
                    'temp_c': row.get('temp_c'),
                    'process_type': str(row.get('process_type', '')),
                    'ef_uuid': str(row.get('ef_uuid', '')),
                    'flow_uuids': str(row.get('flow_uuids', '[]')),
                    'flow_count': row.get('flow_count', 0),
                    'keywords': str(row.get('keywords', '[]')),
                    'material_code_confidence': row.get('material_code_confidence', 5.0),  # High confidence for knowledge
                    'category': str(row.get('category', 'unknown')),
                    'enhanced': True,
                    'raw_data': json.dumps(row.to_dict(), default=str)
                }
                unified_records.append(record)
        
        print(f"    Added {len(unified_records)} knowledge records")
        
        # Priority 2: Enhanced ILCD data (only non-overlapping)
        if self.enhanced_ilcd_data is not None:
            print(f"  🔍 Adding Priority 2: Enhanced ILCD data")
            enhanced_added = 0
            
            for _, row in self.enhanced_ilcd_data.iterrows():
                uuid = str(row.get('uuid', ''))
                
                # Only add if not already in knowledge maps
                if uuid not in overlap_analysis['overlap']:
                    # Only add if has valid material_code
                    material_code = row.get('material_code', '')
                    if pd.notna(material_code) and material_code != '' and material_code != 'null':
                        
                        # Parse flow_uuids if it's a string
                        flow_uuids_raw = row.get('flow_uuids', '[]')
                        if isinstance(flow_uuids_raw, str):
                            try:
                                flow_uuids_list = json.loads(flow_uuids_raw)
                                if isinstance(flow_uuids_list, list):
                                    flow_uuids = json.dumps(flow_uuids_list)
                                    flow_count = len(flow_uuids_list)
                                else:
                                    flow_uuids = '[]'
                                    flow_count = 0
                            except:
                                flow_uuids = '[]' 
                                flow_count = 0
                        else:
                            flow_uuids = '[]'
                            flow_count = 0
                            
                        record = {
                            'source': 'enhanced_ilcd',
                            'priority': 2,
                            'uuid': uuid,
                            'material_code': str(material_code),
                            'dataset_name': str(row.get('name', '')),
                            'lci_file': f"processes/{uuid}.xml",
                            'fu_amount': 1,
                            'fu_unit': str(row.get('reference_unit', 'kg')),
                            'region': str(row.get('geography', 'GLO')),
                            'notes': f"Category: {row.get('category', 'unknown')}",
                            # Enhanced parameters from new scraper
                            'kg_per_m2': row.get('kg_per_m2'),
                            'temp_c': row.get('temp_c'),
                            'process_type': str(row.get('category', '')),
                            'ef_uuid': '',
                            'flow_uuids': flow_uuids,
                            'flow_count': flow_count,
                            'keywords': str(row.get('keywords', '[]')),
                            'material_code_confidence': row.get('material_code_confidence', 0.0),
                            'category': str(row.get('category', 'unknown')),
                            'enhanced': True,
                            'raw_data': json.dumps(row.to_dict(), default=str)
                        }
                        unified_records.append(record)
                        enhanced_added += 1
                        
            print(f"    Added {enhanced_added} enhanced ILCD records")
        
        # Priority 3: PEFCR defaults would go here if needed
        
        # Create DataFrame
        self.unified_lookup = pd.DataFrame(unified_records)
        print(f"  ✅ Created unified lookup with {len(unified_records)} total records")
        
        # Save to file
        output_file = self.output_dir / "updated_unified_lookup_table.csv"
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
                self.unified_lookup['material_code'].str.contains(material_code, na=False, case=False)
            ]
            if not matches.empty:
                # Sort by priority (1 = highest)
                matches = matches.sort_values(['priority', 'material_code_confidence'], ascending=[True, False])
                return matches.iloc[0].to_dict()
        
        # Search by category (fuzzy)
        if category:
            matches = self.unified_lookup[
                (self.unified_lookup['category'].str.contains(category, na=False, case=False)) |
                (self.unified_lookup['notes'].str.contains(category, na=False, case=False))
            ]
            if not matches.empty:
                matches = matches.sort_values(['priority', 'material_code_confidence'], ascending=[True, False])
                return matches.iloc[0].to_dict()
                
        return None
    
    def generate_summary_report(self):
        """Generate summary report of updated unified lookup system"""
        print(f"\n📊 UPDATED UNIFIED LOOKUP SYSTEM SUMMARY")
        print("=" * 50)
        
        if self.unified_lookup.empty:
            print("❌ No unified lookup table to analyze")
            return
            
        # Source breakdown
        source_counts = self.unified_lookup['source'].value_counts()
        print(f"\n📁 Records by source:")
        for source, count in source_counts.items():
            print(f"  {source}: {count}")
        
        # Priority breakdown
        priority_counts = self.unified_lookup['priority'].value_counts().sort_index()
        print(f"\n🏆 Records by priority:")
        for priority, count in priority_counts.items():
            priority_name = {1: "Knowledge Maps", 2: "Enhanced ILCD", 3: "PEFCR Defaults"}.get(priority, "Unknown")
            print(f"  Priority {priority} ({priority_name}): {count}")
        
        # Material code coverage
        with_material_code = self.unified_lookup[
            (self.unified_lookup['material_code'].notna()) & 
            (self.unified_lookup['material_code'] != '') &
            (self.unified_lookup['material_code'] != 'null')
        ]
        
        print(f"\n🏷️  Material code coverage:")
        print(f"  With material_code: {len(with_material_code)}/{len(self.unified_lookup)} ({len(with_material_code)/len(self.unified_lookup)*100:.1f}%)")
        
        # Category breakdown
        category_counts = with_material_code['category'].value_counts()
        print(f"\n📈 Top categories with material codes:")
        for category, count in category_counts.head(10).items():
            print(f"  {category}: {count}")
            
        # Material code distribution
        material_code_counts = with_material_code['material_code'].value_counts()
        print(f"\n🎯 Top material codes:")
        for code, count in material_code_counts.head(15).items():
            print(f"  {code}: {count}")
        
        # Flow UUID statistics
        with_flows = self.unified_lookup[
            (self.unified_lookup['flow_uuids'].notna()) & 
            (self.unified_lookup['flow_uuids'] != '[]')
        ]
        
        print(f"\n🔗 Flow UUID coverage:")
        print(f"  Processes with flow UUIDs: {len(with_flows)}/{len(self.unified_lookup)} ({len(with_flows)/len(self.unified_lookup)*100:.1f}%)")
        
        # Quality metrics
        high_confidence = with_material_code[with_material_code['material_code_confidence'] >= 4.0]
        medium_confidence = with_material_code[
            (with_material_code['material_code_confidence'] >= 2.5) & 
            (with_material_code['material_code_confidence'] < 4.0)
        ]
        
        print(f"\n📊 Mapping quality:")
        print(f"  High confidence (≥4.0): {len(high_confidence)}")
        print(f"  Medium confidence (2.5-4.0): {len(medium_confidence)}")
        print(f"  Total with confidence data: {len(with_material_code)}")
        
        print(f"\n📈 Overall system statistics:")
        print(f"  Total processes available: {len(self.unified_lookup)}")
        print(f"  Business logic mapped: {len(with_material_code)} ({len(with_material_code)/len(self.unified_lookup)*100:.1f}%)")
        print(f"  Ready for R2/R3 integration: ✅")

def main():
    # Initialize system
    lookup_system = UpdatedUnifiedLookupSystem()
    
    # Load all mapping sources
    lookup_system.load_knowledge_maps()
    lookup_system.load_enhanced_ilcd_data()
    lookup_system.load_pefcr_defaults()
    
    # Create unified lookup
    lookup_system.create_unified_lookup()
    
    # Generate summary
    lookup_system.generate_summary_report()
    
    # Test lookup functionality
    print(f"\n🧪 Testing lookup functionality...")
    
    # Test cases
    test_cases = [
        {"material_code": "pack_cardboard", "desc": "Packaging cardboard"},
        {"material_code": "tex_cotton_conv", "desc": "Conventional cotton"},
        {"material_code": "tex_spinning", "desc": "Spinning process"},
        {"material_code": "eol_incineration", "desc": "Waste incineration"},
        {"category": "washing", "desc": "Use phase washing"},
    ]
    
    for test in test_cases:
        print(f"\n  🔍 Test: {test['desc']}")
        result = lookup_system.lookup_process(**{k:v for k,v in test.items() if k != 'desc'})
        if result:
            print(f"    ✅ Found: {result['dataset_name'][:50]}...")
            print(f"    📍 Source: {result['source']} (Priority {result['priority']})")
            print(f"    🎯 Material code: {result['material_code']}")
        else:
            print(f"    ❌ No match found")
    
    print(f"\n✅ Updated unified lookup system ready for R2/R3 integration!")

if __name__ == "__main__":
    main()