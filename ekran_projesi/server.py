from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import os
from data_provider import DataProvider
from datetime import datetime

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Data Provider
dp = DataProvider()

# Base Directory - Absolute Path Fix
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Serve Static Files (HTML, CSS, JS, Images)
import mimetypes
mimetypes.init()
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")
app.mount("/assets", StaticFiles(directory=os.path.join(BASE_DIR, "assets")), name="assets")

@app.get("/api/screen-data")
async def get_screen_data(line: str = "26/17", stop_seq: int = 10):
    """
    API to get all data needed for the screen.
    line: Line Code (e.g. 26/17)
    stop_seq: Current stop sequence (Simulation parameter)
    """
    try:
        # 1. Transport Data
        transport_data = dp.get_screen_data(line, stop_seq)
        
        # 2. Content Data (News, Weather - cached from file)
        content_path = os.path.join(BASE_DIR, "content_data.json")
        content_data = {}
        if os.path.exists(content_path):
            with open(content_path, "r", encoding="utf-8") as f:
                content_data = json.load(f)
        
        # 3. Add Live Events
        try:
            events = dp.fetch_events(limit=5)
            content_data["events"] = events
        except Exception as e:
            print(f"Events error: {e}")
            content_data["events"] = []
        
        return {
            "transport": transport_data,
            "content": content_data,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/lines")
async def get_lines():
    """Get list of available bus lines from database"""
    try:
        import sqlite3
        db_path = r"c:\Users\mete2\OneDrive\Masaüstü\test\samsun_v25.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get unique lines that have stops
        cursor.execute("""
            SELECT DISTINCT hat as code FROM hat_durak 
            WHERE hat NOT LIKE '%TUR%' 
            ORDER BY hat
        """)
        rows = cursor.fetchall()
        conn.close()
        
        lines = []
        for r in rows:
            code = r['code']
            # Extract short code from verbose name
            short_code = code.split(' - ')[0] if ' - ' in code else code
            lines.append({
                "code": code,
                "name": code,
                "short_code": short_code
            })
        
        return {"lines": lines, "count": len(lines)}
    except Exception as e:
        return {"error": str(e), "lines": []}

@app.get("/api/events")
async def get_events():
    """Get upcoming Samsun events from biletinial.com"""
    try:
        events = dp.fetch_events(limit=8)
        return {"events": events, "count": len(events)}
    except Exception as e:
        return {"error": str(e), "events": []}

@app.get("/")
async def root():
    # Redirect to index.html
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

# Serve other files directly from root (like logos)
@app.get("/{filename}")
async def get_file(filename: str):
    from fastapi.responses import FileResponse
    file_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

if __name__ == "__main__":
    print("Starting Setup...")
    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8001)
