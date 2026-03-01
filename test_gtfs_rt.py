import requests
from google.transit import gtfs_realtime_pb2
import time

print("Checking GTFS-RT feed...")
try:
    r = requests.get('http://localhost:8000/gtfs-rt/vehicle-positions')
    print(f"Status: {r.status_code}")
    print(f"Size: {len(r.content)} bytes")
    
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(r.content)
    
    print(f"Timestamp: {feed.header.timestamp}")
    print(f"Entities: {len(feed.entity)}")
    
    if len(feed.entity) > 0:
        v = feed.entity[0].vehicle
        print(f"Sample Vehicle: {feed.entity[0].id} - Route: {v.trip.route_id} - Pos: {v.position.latitude},{v.position.longitude}")
        
except Exception as e:
    print(f"Error: {e}")
