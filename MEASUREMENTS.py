import json

counter = 0
with open('/root/MEASUREMENTS') as f:
    data = json.load(f)
for results in data['results']:
    for series in results['series']:
        for values in series['values']:
            counter += 1
print(counter)