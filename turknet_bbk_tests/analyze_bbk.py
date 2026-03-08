import json, sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    d = json.load(f)

print("=== ADDRESS RESOLVED ===")
print(json.dumps(d.get("address_resolved", {}), indent=2, ensure_ascii=False))

print("\n=== DOWNSTREAM PARSED ===")
for k, v in d.get("downstream_parsed", {}).items():
    print(f"\n--- {k} ---")
    txt = json.dumps(v, indent=2, ensure_ascii=False)
    print(txt[:600])

print("\n=== FINAL DECISION ===")
fd = d.get("final_decision", {})
print(f"confidence: {fd.get('confidence_score')}")
print(f"best_source: {d.get('best_source')}")

# Show D-Smart raw keys
ds = d.get("downstream", {}).get("dsmart", {})
print(f"\n=== D-SMART RAW KEYS ===")
print([k for k in ds.keys() if not k.startswith("_")])

# Show Milenicom raw keys
mil = d.get("downstream", {}).get("milenicom", {})
print(f"\n=== MILENICOM RAW KEYS ===")
print([k for k in mil.keys() if not k.startswith("_")])

# Show Turksat raw keys
tt = d.get("downstream", {}).get("turksat", {})
print(f"\n=== TURKSAT RAW KEYS ===")
print([k for k in tt.keys() if not k.startswith("_")])
