#!/usr/bin/env python3
"""
Enhanced XML Scraper for Business Logic Mapping - FIXED VERSION
==============================================================

Fixes indentation issues and tests improved mapping on 50 files
"""

import os
import json
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
import re
from collections import defaultdict
from difflib import SequenceMatcher

class EnhancedXMLScraper:
    def __init__(self, project_root="/Users/jakubjamny/Documents/GitHub/PEF_AI"):
        self.project_root = Path(project_root)
        self.processes_dir = self.project_root / "data" / "ilcd" / "processes"
        
        # EXPANDED business logic mapping patterns
        self.material_code_patterns = {
            # === TEXTILES & MATERIALS (EXPANDED) ===
            'tex_cotton_conv': [
                'cotton', 'conventional cotton', 'cotton fiber', 'cotton fibre',
                'raw cotton', 'cotton production', 'cotton cultivation', 'cotton ginning',
                'upland cotton', 'cotton lint', 'seed cotton', 'bomull', 'baumwolle',
                'coton', 'algodón', 'cotton yarn', 'cotton spinning'
            ],
            'tex_cotton_org': [
                'organic cotton', 'bio cotton', 'biological cotton', 'eco cotton',
                'sustainable cotton', 'gots cotton', 'certified organic cotton',
                'ökologische baumwolle', 'coton biologique'
            ],
            'tex_pet_virgin': [
                'polyester', 'PET fiber', 'virgin polyester', 'polyester fiber',
                'polyethylene terephthalate', 'PET production', 'polymer PET',
                'polyester staple', 'polyester filament', 'virgin PET',
                'polyesterfaser', 'fibre polyester', 'tereftalato'
            ],
            'tex_pet_recycl': [
                'recycled polyester', 'rPET', 'recycled PET', 'post-consumer PET',
                'bottle-to-fiber', 'recycled polymer', 'secondary PET',
                'mechanical recycling polyester', 'chemical recycling PET',
                'recycelter polyester', 'polyester recyclé'
            ],
            'tex_wool': [
                'wool', 'sheep wool', 'virgin wool', 'merino wool', 'lamb wool',
                'wool fiber', 'wool production', 'wool scouring', 'wool combing',
                'raw wool', 'greasy wool', 'clean wool', 'wolle', 'laine', 'lana'
            ],
            'tex_linen': [
                'linen', 'flax', 'flax fiber', 'linen fiber', 'flax production',
                'linum', 'flax retting', 'flax scutching', 'linen yarn',
                'leinen', 'lin', 'lino', 'flachs'
            ],
            'tex_viscose': [
                'viscose', 'rayon', 'lyocell', 'modal', 'tencel', 'bamboo fiber',
                'regenerated cellulose', 'cellulose fiber', 'wood pulp fiber',
                'viscose production', 'dissolving pulp', 'viskose', 'rayonne'
            ],
            'tex_nylon': [
                'nylon', 'polyamide', 'PA6', 'PA66', 'nylon fiber', 'polyamide fiber',
                'caprolactam', 'adipic acid', 'hexamethylenediamine',
                'nylon production', 'polyamide production', 'polyamidfaser'
            ],
            'tex_elastane': [
                'elastane', 'spandex', 'lycra', 'polyurethane fiber', 'stretch fiber',
                'elastic fiber', 'PU fiber', 'segmented polyurethane',
                'elasthan', 'élasthanne'
            ],
            
            # === PACKAGING (EXPANDED) ===
            'pack_cardboard': [
                'cardboard', 'carton', 'corrugated', 'corrugated cardboard',
                'corrugated board', 'cardboard box', 'carton board', 'containerboard',
                'linerboard', 'corrugated packaging', 'kraft pulp', 'paperboard',
                'wellpappe', 'carton ondulé', 'cartón corrugado'
            ],
            'pack_plastic_pp': [
                'polypropylene', 'PP bag', 'plastic bag', 'PP packaging',
                'propylene polymer', 'polypropylene film', 'PP woven bag',
                'polypropylen', 'polypropylène'
            ],
            'pack_plastic_pe': [
                'polyethylene', 'PE film', 'plastic film', 'PE bag',
                'polyethylene packaging', 'LDPE', 'HDPE', 'linear polyethylene',
                'polyethylen', 'polyéthylène'
            ],
            'pack_paper': [
                'paper bag', 'kraft paper', 'paper packaging', 'paper sack',
                'papier', 'papel', 'papiertüte'
            ],
            
            # === USE PHASE (EXPANDED) ===
            'wash_30': [
                'wash', '30°c', '30 degrees', 'cold wash', 'washing 30',
                'laundry 30', 'household washing', 'domestic washing',
                'waschen', 'lavage', 'lavado'
            ],
            'wash_40': [
                'wash', '40°c', '40 degrees', 'warm wash', 'washing 40',
                'laundry 40', 'washing machine', 'waschen 40'
            ],
            'wash_60': [
                'wash', '60°c', '60 degrees', 'hot wash', 'washing 60',
                'heißwäsche', 'lavage chaud'
            ],
            'wash_hand': [
                'hand wash', 'handwash', 'manual washing', 'washing by hand',
                'handwäsche', 'lavage à la main'
            ],
            'dry_tumble': [
                'tumble dry', 'machine dry', 'drying', 'dryer', 'tumble drying',
                'mechanical drying', 'hot air drying', 'trockner', 'séchage'
            ],
            'dry_air': [
                'air dry', 'line dry', 'natural dry', 'hang drying',
                'lufttrocknung', 'séchage à l\'air'
            ],
            'iron_low': [
                'iron', 'low temperature', 'ironing', 'pressing', 'steam iron',
                'bügeln', 'repassage'
            ],
            'iron_med': ['iron', 'medium temperature', 'mittlere temperatur'],
            'iron_high': ['iron', 'high temperature', 'hohe temperatur'],
            
            # === TRANSPORT (EXPANDED) ===
            'trans_truck': [
                'truck', 'road transport', 'lorry', 'freight transport',
                'cargo truck', 'delivery truck', 'LKW', 'camión', 'camion'
            ],
            'trans_ship': [
                'ship', 'sea transport', 'container ship', 'ocean freight',
                'maritime transport', 'cargo ship', 'vessel', 'schiff', 'navire'
            ],
            'trans_plane': [
                'plane', 'air transport', 'cargo aircraft', 'air cargo',
                'freight aircraft', 'aviation', 'flugzeug', 'avión'
            ],
            'trans_train': [
                'train', 'rail transport', 'railway', 'freight train',
                'cargo train', 'zug', 'tren', 'chemin de fer'
            ],
            
            # === END OF LIFE (EXPANDED) ===
            'eol_recycl_mech': [
                'mechanical recycling', 'recycling', 'mechanical recovery',
                'physical recycling', 'mechanisches recycling', 'recyclage mécanique'
            ],
            'eol_recycl_chem': [
                'chemical recycling', 'depolymerization', 'molecular recycling',
                'chemisches recycling', 'recyclage chimique'
            ],
            'eol_incineration': [
                'incineration', 'energy recovery', 'waste incineration',
                'thermal treatment', 'energy from waste', 'waste to energy',
                'verbrennung', 'incinération'
            ],
            'eol_landfill': [
                'landfill', 'disposal', 'landfilling', 'waste disposal',
                'sanitary landfill', 'controlled landfill', 'deponie', 'décharge'
            ],
            
            # === NEW CATEGORIES ===
            'tex_spinning': [
                'spinning', 'yarn production', 'fiber processing', 'staple fiber',
                'filament', 'spinnen', 'filature'
            ],
            'tex_weaving': [
                'weaving', 'fabric production', 'loom', 'warp', 'weft',
                'textile production', 'weben', 'tissage'
            ],
            'tex_dyeing': [
                'dyeing', 'fabric dyeing', 'textile dyeing', 'coloration',
                'färben', 'teinture'
            ],
            'energy_electricity': [
                'electricity', 'grid electricity', 'power mix', 'electrical energy',
                'electricity production', 'power generation', 'strom', 'électricité'
            ]
        }
        
        # NEGATIVE PATTERNS (avoid false positives)
        self.negative_patterns = {
            'tex_cotton_conv': ['polyester', 'nylon', 'synthetic', 'plastic', 'PET'],
            'tex_pet_virgin': ['cotton', 'wool', 'natural', 'bio', 'organic'],
            'tex_pet_recycl': ['virgin', 'new', 'primary'],
            'pack_cardboard': ['plastic', 'metal', 'glass', 'PE', 'PP'],
            'pack_plastic_pe': ['paper', 'cardboard', 'metal', 'glass'],
            'pack_plastic_pp': ['paper', 'cardboard', 'metal', 'PE'],
            'wash_30': ['40°', '60°', '90°', 'hot'],
            'wash_40': ['30°', '60°', '90°', 'cold'],
            'wash_60': ['30°', '40°', 'cold'],
        }
        
        # FUZZY MATCHING THRESHOLD  
        self.fuzzy_threshold = 0.65
        
        # CONTEXT BOOST RULES
        self.context_rules = [
            {
                'keywords': ['fiber', 'fibre', 'yarn', 'fabric', 'textile', 'cloth'],
                'boost_categories': ['tex_'],
                'boost_factor': 1.5
            },
            {
                'keywords': ['packaging', 'package', 'box', 'bag', 'bottle', 'container'],
                'boost_categories': ['pack_'],
                'boost_factor': 1.5  
            },
            {
                'keywords': ['wash', 'laundry', 'household', 'domestic', 'cleaning'],
                'boost_categories': ['wash_', 'dry_', 'iron_'],
                'boost_factor': 1.5
            },
            {
                'keywords': ['transport', 'freight', 'cargo', 'delivery', 'shipping'],
                'boost_categories': ['trans_'],
                'boost_factor': 1.5
            },
            {
                'keywords': ['recycling', 'waste', 'disposal', 'end-of-life', 'recovery'],
                'boost_categories': ['eol_'],
                'boost_factor': 1.5
            }
        ]
        
        # Parameter extraction patterns
        self.param_patterns = {
            'kg_per_m2': [
                r'(\d+(?:\.\d+)?)\s*g/m[²2]',      
                r'(\d+(?:\.\d+)?)\s*kg/m[²2]',     
                r'basis weight.*?(\d+(?:\.\d+)?)',   
                r'grammage.*?(\d+(?:\.\d+)?)'       
            ],
            'temp_c': [
                r'(\d+)°?[Cc]',                     
                r'(\d+)\s*degrees?',                
                r'temperature.*?(\d+)',             
            ],
            'transport_km': [
                r'(\d+(?:\.\d+)?)\s*km',           
                r'(\d+(?:\.\d+)?)\s*kilometer',    
                r'distance.*?(\d+(?:\.\d+)?)'      
            ]
        }
        
        self.results = []
        
    def extract_text_content(self, xml_file):
        """Extract all text content from XML for analysis"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            text_parts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip().lower())
                    
            return ' '.join(text_parts)
            
        except Exception as e:
            print(f"Error extracting text from {xml_file}: {e}")
            return ""
    
    def extract_flow_uuids(self, xml_file):
        """Extract flow UUIDs from exchanges"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            flow_uuids = []
            for elem in root.iter():
                if 'exchange' in elem.tag.lower():
                    for child in elem.iter():
                        if 'refObjectId' in child.attrib:
                            flow_uuid = child.attrib['refObjectId']
                            if flow_uuid:
                                flow_uuids.append(flow_uuid)
                        elif child.text and len(child.text) == 36 and '-' in child.text:
                            flow_uuids.append(child.text)
            
            return list(set(flow_uuids))
            
        except Exception as e:
            print(f"Error extracting flows from {xml_file}: {e}")
            return []
    
    def extract_specific_parameters(self, text_content):
        """Extract specific parameters like kg_per_m2, temp_c"""
        params = {}
        
        for param_name, patterns in self.param_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    try:
                        value = float(matches[0])
                        if param_name == 'kg_per_m2' and 'g/m' in text_content:
                            value = value / 1000
                        params[param_name] = value
                        break
                    except:
                        continue
        
        return params
    
    def infer_material_code(self, text_content, process_name, category):
        """Enhanced intelligent material_code inference"""
        text_lower = text_content.lower()
        name_lower = process_name.lower()
        
        best_match = ""
        best_score = 0
        
        for material_code, keywords in self.material_code_patterns.items():
            score = 0
            
            # FACTOR 1: Category alignment  
            code_prefix = material_code.split('_')[0]
            if category == code_prefix:
                score += 2
            elif code_prefix == 'tex' and category in ['materials', 'dyeing', 'finishing']:
                score += 1.5
            elif code_prefix == 'pack' and category == 'packaging':
                score += 2
            elif code_prefix == 'eol' and category in ['eol', 'waste']:
                score += 2
                
            # FACTOR 2: Direct keyword matching
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in text_lower:
                    score += 1
                if keyword_lower in name_lower:
                    score += 2
                    
                # FACTOR 3: Fuzzy matching
                name_similarity = SequenceMatcher(None, keyword_lower, name_lower).ratio()
                if name_similarity > self.fuzzy_threshold:
                    score += name_similarity
                    
            # FACTOR 4: Context boost
            for rule in self.context_rules:
                context_match = any(kw in text_lower for kw in rule['keywords'])
                if context_match:
                    for boost_cat in rule['boost_categories']:
                        if material_code.startswith(boost_cat):
                            score *= rule['boost_factor']
                            
            # FACTOR 5: Negative patterns penalty
            negative_words = self.negative_patterns.get(material_code, [])
            for negative in negative_words:
                if negative.lower() in text_lower or negative.lower() in name_lower:
                    score *= 0.3
                    
            # Update best match
            min_threshold = 2.5
            if score > best_score and score >= min_threshold:
                best_score = score
                best_match = material_code
        
        return best_match, best_score

    def extract_enhanced_metadata(self, xml_file):
        """Extract enhanced metadata from single XML file with improved parsing"""
        try:
            # Read the entire XML file as text since ILCD uses mixed text/XML format
            with open(xml_file, 'r', encoding='utf-8', errors='ignore') as f:
                xml_content = f.read()
            
            uuid = xml_file.stem
            
            # IMPROVED EXTRACTION using text patterns
            name = self.extract_process_name(xml_content)
            category = self.extract_process_category(xml_content)  
            geography = self.extract_geography(xml_content)
            reference_unit = self.extract_reference_unit(xml_content)
            
            # Enhanced text content for analysis
            text_content = self.extract_text_content_improved(xml_content)
            flow_uuids = self.extract_flow_uuids_improved(xml_content)
            specific_params = self.extract_specific_parameters(text_content)
            
            # Determine category if not found
            if not category or category == 'unknown':
                category = self.guess_category_from_name(name)
            
            # Infer material_code using improved data
            material_code, confidence = self.infer_material_code(text_content, name, category)
            
            # Create keywords from full content
            keywords = list(set([
                word.lower() for word in re.findall(r'\b[a-zA-Z]{3,}\b', text_content)
                if len(word) > 2 and word.lower() not in ['the', 'and', 'for', 'with', 'this', 'that']
            ]))[:15]
            
            return {
                'uuid': uuid,
                'name': name,
                'category': category,
                'reference_unit': reference_unit,
                'geography': geography,
                'material_code': material_code,
                'material_code_confidence': confidence,
                'kg_per_m2': specific_params.get('kg_per_m2'),
                'temp_c': specific_params.get('temp_c'), 
                'transport_km': specific_params.get('transport_km'),
                'flow_uuids': flow_uuids,
                'flow_count': len(flow_uuids),
                'keywords': keywords,
                'text_excerpt': text_content[:300],
                'xml_file': str(xml_file.relative_to(self.project_root))
            }
            
        except Exception as e:
            print(f"Error processing {xml_file}: {e}")
            return None
    
    def extract_process_name(self, xml_content):
        """Extract process name from ILCD XML content"""
        # Look for patterns like process descriptions at the beginning
        patterns = [
            r'([a-zA-Z][^,\n]{10,100}(?:spinning|weaving|dyeing|washing|transport|packaging|recycling|production)[^,\n]{0,50})',
            r'(spinning[^,\n]{10,100})',
            r'(weaving[^,\n]{10,100})',  
            r'(dyeing[^,\n]{10,100})',
            r'(washing[^,\n]{10,100})',
            r'(transport[^,\n]{10,100})',
            r'(packaging[^,\n]{10,100})',
            r'(recycling[^,\n]{10,100})',
            r'production[^,\n]{10,100}',
            # Fallback: look for service descriptions
            r'service of ([^,\n]{20,100})',
            # Look for activity descriptions
            r'activity[^:]{0,20}: ([^,\n]{20,100})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, xml_content, re.IGNORECASE)
            if matches:
                name = matches[0] if isinstance(matches[0], str) else matches[0][0]
                # Clean up the name
                name = re.sub(r'\s+', ' ', name.strip())
                if len(name) > 10:  # Reasonable name length
                    return name
                    
        # If no pattern matches, try to extract from UUID context
        uuid_match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', xml_content)
        if uuid_match:
            # Look around the UUID for descriptive text
            uuid_pos = uuid_match.start()
            context = xml_content[max(0, uuid_pos-200):uuid_pos+200]
            
            # Extract meaningful text near UUID
            context_patterns = [
                r'([a-zA-Z][^<>\n]{15,80}(?:fiber|yarn|fabric|textile|cotton|polyester|wool))',
                r'([a-zA-Z][^<>\n]{15,80}(?:packaging|bag|box|container))',
                r'([a-zA-Z][^<>\n]{15,80}(?:transport|truck|ship|plane))'
            ]
            
            for pattern in context_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                if matches:
                    return matches[0].strip()
        
        return "Unknown Process"
    
    def extract_process_category(self, xml_content):
        """Extract process category from ILCD XML content"""  
        # Look for category indicators in text
        category_patterns = {
            'materials': [
                r'(textile|fiber|yarn|fabric|cotton|polyester|wool|spinning|weaving)',
                r'Other Services.*spinning',
                r'Other services.*spinning'
            ],
            'packaging': [
                r'(packaging|package|box|bag|container|cardboard)',
                r'Other Services.*packaging'  
            ],
            'transport': [
                r'(transport|freight|cargo|truck|ship|plane|rail)',
                r'Other Services.*transport'
            ],
            'use_phase': [
                r'(washing|drying|ironing|laundry|household)',
                r'Other Services.*(wash|dry|iron)'
            ],
            'eol': [
                r'(recycling|disposal|waste|incineration|landfill)',
                r'Other Services.*(recycl|disposal)'
            ],
            'energy': [
                r'(electricity|energy|power|heat|steam)',
                r'Other Services.*(electric|energy)'
            ],
            'chemicals': [
                r'(chemical|solvent|auxiliary|dye)',
                r'Other Services.*chemical'
            ]
        }
        
        for category, patterns in category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, xml_content, re.IGNORECASE):
                    return category
        
        # Look for explicit category mentions
        if re.search(r'Other Services', xml_content):
            return 'services'
        if re.search(r'Elementary flow', xml_content):
            return 'flow'
            
        return 'unknown'
    
    def extract_geography(self, xml_content):
        """Extract geography from ILCD XML content"""
        geo_patterns = [
            r'\b(GLO|EU|RER|US|CN|IN|BR|DE|FR|IT|ES)\b',
            r'(Europe|European|Global|China|India|Brazil|Germany|France)',
            r'(production mix|at plant|market|regional)'
        ]
        
        for pattern in geo_patterns:
            matches = re.findall(pattern, xml_content)
            if matches:
                return matches[0]
                
        return 'GLO'  # Default to global
    
    def extract_reference_unit(self, xml_content):
        """Extract reference unit from ILCD XML content"""
        unit_patterns = [
            r'\b(kg|m3|MJ|kWh|tkm|m2|piece|item)\b',
            r'per\s+(kg|kilogram|gram|meter|liter)',
            r'1\s+(kg|kilogram|m3|MJ|kWh)'
        ]
        
        for pattern in unit_patterns:
            matches = re.findall(pattern, xml_content, re.IGNORECASE)
            if matches:
                return matches[0].lower()
                
        return 'kg'  # Default unit
    
    def extract_text_content_improved(self, xml_content):
        """Extract all meaningful text content for analysis"""
        # Remove XML tags but keep the text content
        clean_text = re.sub(r'<[^>]+>', ' ', xml_content)
        
        # Remove excessive whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # Extract meaningful sentences (remove very short fragments)
        sentences = [s.strip() for s in clean_text.split('.') if len(s.strip()) > 10]
        
        return ' '.join(sentences).lower()
    
    def extract_flow_uuids_improved(self, xml_content):
        """Extract flow UUIDs with improved patterns"""
        # UUID pattern
        uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        
        # Find all UUIDs
        uuids = re.findall(uuid_pattern, xml_content, re.IGNORECASE)
        
        # Remove duplicates and filter out the process UUID itself
        unique_uuids = list(set(uuids))
        
        # Remove the main process UUID (usually the filename)
        process_uuid = self.extract_process_uuid(xml_content)
        if process_uuid in unique_uuids:
            unique_uuids.remove(process_uuid)
            
        return unique_uuids
    
    def extract_process_uuid(self, xml_content):
        """Extract the main process UUID"""
        # Look for UUID patterns at the beginning or in specific contexts
        uuid_patterns = [
            r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
        ]
        
        for pattern in uuid_patterns:
            matches = re.findall(pattern, xml_content, re.IGNORECASE)
            if matches:
                return matches[0]  # Return first UUID as process UUID
                
        return None
    
    def guess_category_from_name(self, name):
        """Guess category from process name"""
        name_lower = name.lower()
        
        category_keywords = {
            'materials': ['fiber', 'cotton', 'polyester', 'wool', 'fabric', 'textile', 'yarn'],
            'packaging': ['cardboard', 'plastic bag', 'carton', 'packaging', 'box'],
            'use_phase': ['wash', 'dry', 'iron', 'cleaning', 'tumble'],
            'transport': ['truck', 'ship', 'plane', 'rail', 'transport', 'cargo'],
            'energy': ['electricity', 'steam', 'heat', 'energy'],
            'chemicals': ['chemical', 'solvent', 'dye', 'auxiliary']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
                
        return 'unknown'
    
    def process_all_xmls(self, max_files=None):
        """Process all XML files and extract enhanced metadata"""
        print(f"🔍 Starting enhanced XML scraping...")
        print(f"📁 Processing directory: {self.processes_dir}")
        
        xml_files = list(self.processes_dir.glob("*.xml"))
        
        if max_files:
            xml_files = xml_files[:max_files]
            print(f"🚧 Limited to {max_files} files for testing")
        
        print(f"📄 Found {len(xml_files)} XML files to process")
        
        results = []
        
        for i, xml_file in enumerate(xml_files, 1):
            if i % 25 == 0:
                print(f"📈 Progress: {i}/{len(xml_files)} ({i/len(xml_files)*100:.1f}%)")
            
            metadata = self.extract_enhanced_metadata(xml_file)
            if metadata:
                results.append(metadata)
        
        self.results = results
        print(f"✅ Successfully processed {len(results)} files")
        
        return results
    
    def analyze_results(self):
        """Analyze extraction results and generate statistics"""
        if not self.results:
            print("❌ No results to analyze")
            return
            
        print(f"\n📊 ENHANCED EXTRACTION RESULTS")
        print("=" * 50)
        
        total = len(self.results)
        
        # Material code mapping success
        mapped = len([r for r in self.results if r['material_code']])
        print(f"🎯 Material code mapping: {mapped}/{total} ({mapped/total*100:.1f}%)")
        
        # Specific parameters extraction
        kg_per_m2_found = len([r for r in self.results if r['kg_per_m2'] is not None])
        temp_c_found = len([r for r in self.results if r['temp_c'] is not None])
        flow_uuids_found = len([r for r in self.results if r['flow_uuids']])
        
        print(f"📏 kg_per_m2 extracted: {kg_per_m2_found}/{total} ({kg_per_m2_found/total*100:.1f}%)")
        print(f"🌡️  temp_c extracted: {temp_c_found}/{total} ({temp_c_found/total*100:.1f}%)")
        print(f"🔗 Flow UUIDs extracted: {flow_uuids_found}/{total} ({flow_uuids_found/total*100:.1f}%)")
        
        # Category distribution of mapped processes
        mapped_by_category = defaultdict(int)
        for r in self.results:
            if r['material_code']:
                mapped_by_category[r['category']] += 1
        
        print(f"\n📈 Mapped processes by category:")
        for category, count in sorted(mapped_by_category.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
        # Material code distribution
        material_code_dist = defaultdict(int)
        for r in self.results:
            if r['material_code']:
                material_code_dist[r['material_code']] += 1
        
        print(f"\n🏷️  Top material codes found:")
        for code, count in sorted(material_code_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {code}: {count}")
    
    def save_results(self):
        """Save enhanced results to files"""
        if not self.results:
            print("❌ No results to save")
            return
            
        output_dir = self.project_root / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Save as JSON
        json_file = output_dir / "enhanced_ilcd_metadata_test.json"
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"💾 JSON saved: {json_file}")
        
        # Save as CSV
        csv_file = output_dir / "enhanced_ilcd_metadata_test.csv"
        df = pd.DataFrame(self.results)
        df.to_csv(csv_file, index=False)
        print(f"💾 CSV saved: {csv_file}")

def main():
    scraper = EnhancedXMLScraper()
    
    # FULL RUN: Process all 5007 files
    print("🚀 RUNNING ENHANCED MAPPING ON ALL FILES")
    print("=" * 50)
    print("⚠️  This will take several minutes to process 5007 XML files...")
    
    results = scraper.process_all_xmls()  # No max_files limit = full run
    
    # Analyze results
    scraper.analyze_results()
    
    # Save results
    scraper.save_results()
    
    # Enhanced analysis for full run
    print(f"\n🎯 FULL DATABASE ANALYSIS:")
    print("=" * 50)
    
    mapped_results = [r for r in results if r['material_code']]
    high_confidence = [r for r in mapped_results if r['material_code_confidence'] >= 4.0]
    medium_confidence = [r for r in mapped_results if 2.5 <= r['material_code_confidence'] < 4.0]
    
    print(f"📊 Final Statistics:")
    print(f"  Total XML files processed: {len(results)}")
    print(f"  Successfully mapped: {len(mapped_results)}")
    print(f"  High confidence (≥4.0): {len(high_confidence)}")
    print(f"  Medium confidence (2.5-4.0): {len(medium_confidence)}")
    print(f"  Overall success rate: {len(mapped_results)/len(results)*100:.1f}%")
    
    # Category breakdown
    category_dist = {}
    for r in mapped_results:
        cat = r['category']
        category_dist[cat] = category_dist.get(cat, 0) + 1
    
    print(f"\n📈 Mapped processes by category:")
    for category, count in sorted(category_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")
    
    # Material code breakdown
    material_dist = {}
    for r in mapped_results:
        code = r['material_code']
        material_dist[code] = material_dist.get(code, 0) + 1
    
    print(f"\n🏷️  Top 15 material codes found:")
    for code, count in sorted(material_dist.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {code}: {count}")
    
    # Flow UUID statistics
    with_flows = [r for r in results if r['flow_uuids']]
    total_flows = sum(len(r['flow_uuids']) for r in with_flows)
    
    print(f"\n🔗 Flow UUID Statistics:")
    print(f"  Processes with flow UUIDs: {len(with_flows)}/{len(results)} ({len(with_flows)/len(results)*100:.1f}%)")
    print(f"  Total unique flow UUIDs: {total_flows}")
    print(f"  Average flows per process: {total_flows/len(with_flows) if with_flows else 0:.1f}")
    
    # Parameter extraction statistics
    with_kg_per_m2 = [r for r in results if r['kg_per_m2'] is not None]
    with_temp_c = [r for r in results if r['temp_c'] is not None]
    
    print(f"\n📏 Parameter Extraction:")
    print(f"  kg_per_m2 extracted: {len(with_kg_per_m2)}/{len(results)} ({len(with_kg_per_m2)/len(results)*100:.1f}%)")
    print(f"  temp_c extracted: {len(with_temp_c)}/{len(results)} ({len(with_temp_c)/len(results)*100:.1f}%)")
    
    print(f"\n💾 OUTPUT FILES:")
    print(f"  enhanced_ilcd_metadata_test.json - Full metadata")
    print(f"  enhanced_ilcd_metadata_test.csv - Tabular format")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"  1. Integrate with unified_lookup_system.py")
    print(f"  2. Update R2/R3 scripts to use enhanced mappings")
    print(f"  3. Test complete R1→R2→R3 workflow")
    
    print(f"\n✅ Enhanced scraping completed successfully!")
    print(f"   Ready for integration into DPP workflow.")
    
    return results

if __name__ == "__main__":
    main()