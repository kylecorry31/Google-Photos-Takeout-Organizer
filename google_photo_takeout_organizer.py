import shutil
from pathlib import Path
import json
import datetime

# Start configuration
takeout = Path("D:\\Photos\\Takeout\\Google Photos")
output = Path("D:\\Photos\\Takeout\\Output2")
keep_original_titles = True
title_format = '%Y-%m-%d %H-%M-%S'
copy = True
allow_duplicates = True
# End configuration

photo_metadata = takeout.rglob("*.json")
count = 0

def generate_name(date, from_path):
    if keep_original_titles:
        return from_path.name
    extension = from_path.suffix
    return date.strftime(title_format) + extension

def move(from_path, to_path):
    to_path.parent.mkdir(parents=True, exist_ok=True)

    if allow_duplicates:
        # Rename if needed
        n = 1
        original = to_path
        while to_path.exists():
            parent = original.parent
            name = original.stem
            extension = original.suffix
            to_path = parent / (name + " (" + str(n) + ")" + extension)
            n += 1
    
    if copy:
        shutil.copy(from_path, to_path)
    else:
        shutil.move(from_path, to_path)

def get_image_path(json_path, json):
    stem = json_path.stem
    path = json_path.parent / stem
    if not path.exists():
        paths = json_path.parent.glob(stem + "*")
        for p in paths:
            if p != json_path and p.suffix != '.json':
                path = p
                break
    if not path.exists():
        name = json['title']
        path = json_path.parent / name
    return path

for metadata_path in photo_metadata:
    file = metadata_path.open()
    contents = file.read()
    metadata = json.loads(contents)
    file.close()
    path = get_image_path(metadata_path, metadata)
    create_time = int(metadata['photoTakenTime']['timestamp'])
    time = datetime.datetime.fromtimestamp(create_time)
    year = time.year
    month = time.month
    dest_name = generate_name(time, path)
    dest = output / str(year) / str(month) / dest_name
    if not path.exists():
        print(path, 'not found')
        continue
    move(path, dest)
    count += 1

if copy:
    print(str(count), 'photos copied')
else:
    print(str(count), 'photos moved')