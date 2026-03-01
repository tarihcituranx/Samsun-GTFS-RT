from data_provider import DataProvider
import json
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)

def test():
    dp = DataProvider()
    print("Fetching data for 26/17...")
    # Test for a sequence in the middle of the route
    data = dp.get_screen_data('26/17', 10)
    
    print("\n--- SCREEN DATA ---")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    if data.get('error'):
        print("\n❌ Error:", data['error'])
    else:
        print("\n✅ Data structure looks correct.")
        if data['is_simulated']:
            print("ℹ️ Mode: Simulated (No real vehicle found matching criteria)")
        else:
            print(f"🚀 Mode: Real-time (Vehicle: {data['current_bus']['plate']})")

if __name__ == "__main__":
    test()
