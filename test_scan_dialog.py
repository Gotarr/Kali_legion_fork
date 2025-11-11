"""Test the New Scan Dialog."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from legion.ui.dialogs import NewScanDialog

print("=" * 60)
print("NEW SCAN DIALOG TEST")
print("=" * 60)

app = QApplication(sys.argv)

# Test the dialog
print("\n[1] Showing New Scan dialog...")
print("    Fill in a target and click OK")

result = NewScanDialog.get_scan_parameters()

if result:
    target, scan_type, options = result
    print(f"\n[SUCCESS] Scan configured!")
    print(f"  Target: {target}")
    print(f"  Type: {scan_type}")
    print(f"  Options: {options}")
else:
    print("\n[CANCELLED] User cancelled the dialog")

print("\n" + "=" * 60)
