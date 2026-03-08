import asyncio
import sys
import os

# Add Turannet to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Turannet"))

import api_services

async def main():
    bbk = "37735014" 
    print(f"Testing JIO Fallback with BBK: {bbk}")
    result = await api_services.query_jio_fallback(bbk)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
