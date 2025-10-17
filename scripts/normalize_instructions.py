#!/usr/bin/env python3
from pathlib import Path
from scripts.analyze_instruction_mismatches import parse_instruction
import json

def main():
    with open('scripts/instruction_mismatches.json', encoding='utf-8') as f:
        data = json.load(f)
    print(len(data))
    print(parse_instruction('Gis umiddelbart  -   16.10.Thursday kl.20:00'))
    print(parse_instruction(' Gis umiddelbart  -   16.10.2025 kl.20:00'))

if __name__ == '__main__':
    main()
