import shutil
from pathlib import Path
import json
import datetime
from tqdm import tqdm

# Start configuration
takeout = Path("D:\\Photos\\Google Photos")
output = Path("D:\\Photos\\Organized")
keep_original_titles = True
title_format = '%Y-%m-%d %H-%M-%S'
copy = True
allow_duplicates = False
# End configuration

photo_metadata = list(takeout.rglob("*.json"))
ignored_files = [
    'metadata.json',
    'print-subscriptions.json',
    'shared_album_comments.json',
    'user-generated-memory-titles.json'
]

def generate_name(date, from_path):
    if keep_original_titles:
        return from_path.name
    extension = from_path.suffix
    return date.strftime(title_format) + extension

def should_rename(from_path, to_path):   
    if not to_path.exists():
        return False
    
    if allow_duplicates and to_path.exists():
        return True
    
    # Their sizes are different, so they are different files and we should rename
    return from_path.stat().st_size != to_path.stat().st_size

def move(from_path, to_path):
    to_path.parent.mkdir(parents=True, exist_ok=True)

    # Rename if needed
    n = 1
    original = to_path
    while should_rename(from_path, to_path):
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

with tqdm(total=len(photo_metadata)) as pbar:
    for metadata_path in photo_metadata:
        if metadata_path.name in ignored_files:
            pbar.update(1)
            continue

        file = metadata_path.open()
        contents = file.read()
        metadata = json.loads(contents)
        file.close()
        
        date_keys = ['photoTakenTime', 'creationTime']
        date_key = None
        for key in date_keys:
            if key in metadata:
                date_key = key
                break

        if date_key is None:
            print(metadata_path, 'missing date')
            pbar.update(1)
            continue

        is_archived = 'archived' in metadata and metadata['archived']
        is_trashed = 'trashed' in metadata and metadata['trashed']

        if is_trashed:
            pbar.update(1)
            continue

        path = get_image_path(metadata_path, metadata)
        create_time = int(metadata[date_key]['timestamp'])
        time = datetime.datetime.fromtimestamp(create_time)
        year = time.year
        month = time.month
        dest_name = generate_name(time, path)
        dest = output if not is_archived else output / 'Archived'
        dest = dest / str(year) / str(month) / dest_name
        if not path.exists():
            print(path, 'not found')
            pbar.update(1)
            continue
        move(path, dest)
        pbar.update(1)