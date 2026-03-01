from data_provider import DataProvider
import json

dp = DataProvider()
weather = dp.fetch_weather()
print("Weather:", json.dumps(weather, ensure_ascii=False))

data = dp.get_screen_data('26/17', 10)
print("Line:", data['line_code'])
print("Weather:", data['weather'])
print("ETA:", data['eta'], "dk", "(Simulated)" if data['is_simulated'] else "(Real)")
