import requests
from datetime import datetime
import mysql.connector

# -----------------------
# 1. Database Connection
# -----------------------
db_config = {
    "host": "ibcs.cfwyaai4qy7a.ap-southeast-1.rds.amazonaws.com",
    "port": 3306,
    "user": "admin",
    "password": "Muuluu0710$",
    "database": "traffic_ia"  # Make sure this matches the DB you created
}

# Connect to the database
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()


API_KEY = "AIzaSyBiz1TbGLEzrbfOFUgPnIJ_tb-5SHg1p5M"
destination = "Human International School, Ulaanbaatar"

# List of origins (English + Ulaanbaatar, Mongolia)
origins_base = [
    "Time Square",
    "Enkhjin Khotkhon",
    "Nomun Village",
    "Japan Town",
    "Hunnu 2222",
    "Narnii Khoroolol",
    "VIP Residence",
    "Roma Town",
    "Orgil Stadium",
    "White Hill",
    "River Garden",
    "Tsengeldekh Khotkhon",
    "Royal Green Villa",
    "Crystal Town",
    "King Tower",
    "Bogd Ar",
    "Gereg Villa",
    "Green Villa",
    "Zaisan Village",
    "Luxury Zaisan",
    "Marshal King Tower",
    "Mogul Town",
    "Olymp Khotkhon",
    "Rapid Harsh (Rapid Residence/Palace)",
    "Romana Residence",
    "Seoul Royal County",
    "Shambala Khotkhon",
    "Shine Ugluu",
    "English Garden"
]
origins = [f"{place}, Ulaanbaatar, Mongolia" for place in origins_base]

# -----------------------
# 3. Process & Insert Data
# -----------------------
for origin in origins:
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "departure_time": "now",  # "now" requires a billed account for live traffic
        "key": API_KEY,
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Current timestamp
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if not data.get('routes'):
        print(f"ERROR: No routes found for origin: {origin}")
        
        # Insert a row with minimal info indicating no data
        sql = """
        INSERT INTO traffic
        (timestamp, origin, destination, normal_time_min, traffic_time_min, difference, traffic_level, traffic_level_color)
        VALUES (%s, %s, %s, NULL, NULL, NULL, %s, NULL);
        """
        values = (timestamp_str, origin, destination, "No Data")
        cursor.execute(sql, values)
        conn.commit()
        continue
    
    try:
        # Extract travel times (seconds)
        normal_time_seconds = data['routes'][0]['legs'][0]['duration']['value']
        traffic_time_seconds = data['routes'][0]['legs'][0]['duration_in_traffic']['value']
        
        # Convert to minutes
        normal_time_min = normal_time_seconds / 60
        traffic_time_min = traffic_time_seconds / 60
        
        # Calculate difference
        difference = traffic_time_min - normal_time_min
        
        # Determine traffic level
        ratio = traffic_time_seconds / normal_time_seconds
        if ratio < 1.2:
            traffic_level = "Low Traffic"
            traffic_level_color = "Green"
        elif ratio < 1.5:
            traffic_level = "Moderate Traffic"
            traffic_level_color = "Yellow"
        else:
            traffic_level = "Heavy Traffic"
            traffic_level_color = "Red"
        
        # Print to console
        print(f"{timestamp_str} | Origin: {origin}")
        print(f"  Destination: {destination}")
        print(f"  Normal Time: {normal_time_min:.1f} min")
        print(f"  Traffic Time: {traffic_time_min:.1f} min")
        print(f"  Difference:   {difference:.1f} min")
        print(f"  Traffic Level: {traffic_level} ({traffic_level_color})")
        print("-----------------------------------")
        
        # Insert into MySQL
        sql = """
        INSERT INTO traffic
        (timestamp, origin, destination, normal_time_min, traffic_time_min, difference, traffic_level, traffic_level_color)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = (
            timestamp_str,
            origin,
            destination,
            normal_time_min,
            traffic_time_min,
            difference,
            traffic_level,
            traffic_level_color
        )
        cursor.execute(sql, values)
        conn.commit()
    
    except KeyError:
        print(f"ERROR: Traffic data not available for origin: {origin}")
        
        # Insert partial info
        sql = """
        INSERT INTO traffic
        (timestamp, origin, destination, normal_time_min, traffic_time_min, difference, traffic_level, traffic_level_color)
        VALUES (%s, %s, %s, NULL, NULL, NULL, %s, NULL);
        """
        values = (timestamp_str, origin, destination, "No Traffic Data")
        cursor.execute(sql, values)
        conn.commit()
        continue

# Close the DB connection when done
cursor.close()
conn.close()
print("\nDone inserting data into MySQL database!")