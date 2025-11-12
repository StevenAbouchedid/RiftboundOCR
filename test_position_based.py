#!/usr/bin/env python
"""
Test position-based metadata extraction
"""
import os
import sys

# Windows DLL loading fix - MUST happen before any torch imports
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
    
    try:
        import torch
        torch_lib_path = os.path.join(os.path.dirname(torch.__file__), 'lib')
        if os.path.exists(torch_lib_path):
            os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(torch_lib_path)
    except Exception as e:
        print(f"Warning: Could not set up PyTorch DLL paths: {e}")

from src.ocr.parser import parse_with_two_stage
import json

print("="*60)
print("POSITION-BASED METADATA EXTRACTION TEST")
print("="*60)

test_image = "test_images/Screenshot_20251106_021827_WeChat.jpg"
print(f"\nTesting with: {test_image}\n")

result = parse_with_two_stage(test_image)

print("\n" + "="*60)
print("EXTRACTED METADATA")
print("="*60)
print(f"Player: {result.get('player')}")
print(f"Deck Name: {result.get('legend_name')}")
print(f"Placement: {result.get('placement')}")
print(f"Event: {result.get('event')}")
print(f"Date: {result.get('date')}")

print("\n" + "="*60)
print("CARD COUNTS")
print("="*60)
print(f"Legend: {len(result['cards']['legend'])} cards")
print(f"Main Deck: {len(result['cards']['main_deck'])} cards")
print(f"Battlefields: {len(result['cards']['battlefields'])} cards")
print(f"Runes: {len(result['cards']['runes'])} cards")
print(f"Side Deck: {len(result['cards']['side_deck'])} cards")

# Show sample card from main deck
if result['cards']['main_deck']:
    print("\n" + "="*60)
    print("SAMPLE CARD (First Main Deck Card)")
    print("="*60)
    card = result['cards']['main_deck'][0]
    print(f"Name (CN): {card['name_cn']}")
    print(f"Quantity: {card['quantity']}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)

