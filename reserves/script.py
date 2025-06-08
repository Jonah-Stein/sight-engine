import json


with open('data/test_sight_points.json', "r") as f:
    data = json.load(f)

#Need to see whether its lat lon or lon lat
for point in data["sightPoints"]:
    print(f"{point[0]}, {point[1]}")

with open('data/380ce8ef_tracking_data.json', "r") as f:
    data = json.load(f)
for point in data[0]["tracks"]:
    print(f"{point["lat"]}, {point["lon"]}")