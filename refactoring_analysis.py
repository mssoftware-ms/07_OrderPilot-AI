#!/usr/bin/env python3
"""
Refactoring Analysis Tool V1.0
Phase 2: Analyze inventory for dead code, duplicates, complexity, and size.
"""

import json
import os
import ast
import hashlib
from collections import defaultdict
from typing import List, Dict, Set, Tuple

# Konfiguration
MAX_LOC = 600
PROJECT_DIRS = ['src']
EXCLUDE_DIRS = ['.wsl_env', '.venv', 'venv', '.ai_exchange', '__pycache__', 'tests', 'docs']

def load_inventory(json_path: str) -> Dict:
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_project_file(file_path: str) -> bool:
    if any(ex in file_path for ex in EXCLUDE_DIRS):
        return False
    return any(file_path.startswith(d) or file_path.startswith(f"./{d}") for d in PROJECT_DIRS)

def calculate_complexity(source_code: str) -> int:
    """Schätzt zyklomatische Komplexität (McCabe)."""
    complexity = 1
    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.ExceptHandler, ast.Assert)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
    except:
        pass
    return complexity

def get_function_body(file_path: str, start: int, end: int) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Zeilennummern sind 1-basiert
            return "".join(lines[start-1:end])
    except:
        return ""

def analyze_dead_code(files: Dict) -> Tuple[List[Dict], Set[str]]:
    """
    Identifiziert potenziell toten Code.
    Strategie: Sammle alle Definitionen und suche nach Referenzen im gesamten Code.
    """
    definitions = {}  # name -> {type, file, line}
    references = defaultdict(int)
    
    # 1. Sammle Definitionen
    for path, data in files.items():
        if not is_project_file(path):
            continue
            
        for func in data.get('functions', []):
            name = func['name']
            if name.startswith('__') and name.endswith('__'): continue # Magic methods ignorieren
            if name.startswith('test_'): continue # Tests ignorieren
            definitions[name] = {'type': 'function', 'file': path, 'line': func['line_start']}
            
        for cls in data.get('classes', []):
            name = cls['name']
            definitions[name] = {'type': 'class', 'file': path, 'line': cls['line_start']}

    # 2. Suche Referenzen (Grober Scan)
    # Wir laden jeden File-Inhalt einmal und suchen nach den Namen
    all_names = set(definitions.keys())
    
    for path, data in files.items():
        if not is_project_file(path):
            continue
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                for name in all_names:
                    # Sehr einfacher Check: Zähle Vorkommen
                    # Wir ziehen 1 ab für die Definition selbst (ungenaue Heuristik, aber okay für Phase 2)
                    count = content.count(name)
                    if count > 0:
                        references[name] += count
        except:
            continue

    # 3. Bestimme Dead Code Kandidaten
    dead_candidates = []
    for name, info in definitions.items():
        # Wenn nur 1x gefunden (Definition selbst) oder 0x (sollte nicht passieren wenn Definition da ist)
        # Wir müssen vorsichtig sein: Importe zählen auch als Vorkommen in Textsuche
        ref_count = references[name]
        
        # Heuristik: < 2 Vorkommen global KÖNNTE ungenutzt sein (1 Def + 0 Calls)
        # Ausnahme: Main entry points, Framework Callbacks (on_...)
        if ref_count < 2:
            if info['type'] == 'function' and (name.startswith('on_') or 'handler' in name):
                continue
                
            dead_candidates.append({
                'name': name,
                'type': info['type'],
                'file': info['file'],
                'line': info['line'],
                'refs': ref_count
            })
            
    return dead_candidates, all_names

def analyze_duplicates(files: Dict) -> List[Dict]:
    """Findet exakte Duplikate von Funktionen."""
    hashes = defaultdict(list)
    
    for path, data in files.items():
        if not is_project_file(path):
            continue
            
        for func in data.get('functions', []):
            # Ignoriere sehr kurze Funktionen (Getter/Setter)
            if func['line_end'] - func['line_start'] < 5:
                continue
                
            body = get_function_body(path, func['line_start'], func['line_end'])
            # Normalisiere: Whitespace weg
            normalized = "".join(body.split())
            if not normalized: continue
            
            func_hash = hashlib.md5(normalized.encode('utf-8')).hexdigest()
            hashes[func_hash].append({
                'name': func['name'],
                'file': path,
                'lines': (func['line_start'], func['line_end'])
            })
            
    duplicates = []
    for h, instances in hashes.items():
        if len(instances) > 1:
            duplicates.append(instances)
            
    return duplicates

def analyze_complexity_and_size(files: Dict) -> Tuple[List[Dict], List[Dict]]:
    large_files = []
    complex_functions = []
    
    for path, data in files.items():
        if not is_project_file(path):
            continue
            
        # Size Check
        loc = data.get('code_lines', 0)
        if loc > MAX_LOC:
            large_files.append({
                'file': path,
                'loc': loc,
                'functions': len(data.get('functions', [])),
                'classes': len(data.get('classes', []))
            })
            
        # Complexity Check
        for func in data.get('functions', []):
            body = get_function_body(path, func['line_start'], func['line_end'])
            cc = calculate_complexity(body)
            if cc > 15: # Warnung ab 15
                complex_functions.append({
                    'name': func['name'],
                    'file': path,
                    'line': func['line_start'],
                    'cc': cc,
                    'loc': func['line_end'] - func['line_start']
                })
                
    return large_files, complex_functions

def generate_report(dead_code, duplicates, large_files, complex_funcs):
    print("# 🔍 ANALYSE-REPORT (Phase 2)\n")
    
    print(f"## 1. DATEIGRÖSSEN-ANALYSE (> {MAX_LOC} LOC)")
    if large_files:
        print(f"⚠️  {len(large_files)} Dateien müssen gesplittet werden:")
        print(f"| {'Datei':<60} | {'LOC':<6} | {'Fkt':<4} | {'Kls':<4} |")
        print("|" + "-"*62 + "|" + "-"*8 + "|" + "-"*6 + "|" + "-"*6 + "|")
        for f in sorted(large_files, key=lambda x: x['loc'], reverse=True):
            print(f"| {f['file']:<60} | {f['loc']:<6} | {f['functions']:<4} | {f['classes']:<4} |")
    else:
        print("✅ Keine Dateien über dem Limit.")
        
    print("\n" + "-"*80 + "\n")
    
    print("## 2. DUPLIKAT-ANALYSE (Exakte Matches)")
    if duplicates:
        print(f"⚠️  {len(duplicates)} Duplikat-Gruppen gefunden:")
        for i, group in enumerate(duplicates, 1):
            print(f"\nGruppe {i}:")
            for inst in group:
                print(f"  - {inst['file']}:{inst['lines'][0]} -> {inst['name']}()")
    else:
        print("✅ Keine exakten Duplikate gefunden.")

    print("\n" + "-"*80 + "\n")

    print("## 3. KOMPLEXITÄTS-ANALYSE (CC > 15)")
    if complex_funcs:
        print(f"⚠️  {len(complex_funcs)} komplexe Funktionen:")
        print(f"| {'Funktion':<40} | {'Datei':<40} | {'CC':<4} | {'LOC':<4} |")
        print("|" + "-"*42 + "|" + "-"*42 + "|" + "-"*6 + "|" + "-"*6 + "|")
        for f in sorted(complex_funcs, key=lambda x: x['cc'], reverse=True)[:20]: # Top 20
            print(f"| {f['name']:<40} | {os.path.basename(f['file']):<40} | {f['cc']:<4} | {f['loc']:<4} |")
        if len(complex_funcs) > 20:
            print(f"... und {len(complex_funcs)-20} weitere.")
    else:
        print("✅ Keine kritische Komplexität gefunden.")

    print("\n" + "-"*80 + "\n")

    print("## 4. DEAD CODE KANDIDATEN (Vorsichtige Schätzung)")
    if dead_code:
        print(f"ℹ️  {len(dead_code)} potenzielle Kandidaten (weniger als 2 Referenzen gefunden):")
        for c in dead_code[:20]:
            print(f"- {c['type']} `{c['name']}` in {os.path.basename(c['file'])}:{c['line']}")
        if len(dead_code) > 20:
            print(f"... und {len(dead_code)-20} weitere.")
    else:
        print("✅ Kein offensichtlicher Dead Code gefunden.")

    print("\n" + "="*80)
    print("ZUSAMMENFASSUNG & AKTIONSEMPFEHLUNG")
    print(f"- Splitting erforderlich: {len(large_files)} Dateien")
    print(f"- Refactoring erforderlich: {len(duplicates)} Duplikate, {len(complex_funcs)} komplexe Funktionen")
    print("="*80)

if __name__ == "__main__":
    inventory = load_inventory('refactoring_inventory.json')
    files = inventory.get('files', {})
    
    dead_code, _ = analyze_dead_code(files)
    duplicates = analyze_duplicates(files)
    large_files, complex_funcs = analyze_complexity_and_size(files)
    
    generate_report(dead_code, duplicates, large_files, complex_funcs)
