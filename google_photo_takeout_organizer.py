import shutil
from pathlib import Path
import json
import datetime
from tqdm import tqdm

# Start configuration
takeout = Path("D:\\Photos\\Google Photos")  # Path to the directory containing the Google Photos
output = Path("D:\\Photos\\Organized")  # Path to the output directory for organizing the photos
keep_original_titles = True  # Whether to keep the original titles of the photos or generate new ones
title_format = '%Y-%m-%d %H-%M-%S'  # Format for generating new titles
copy = True  # Whether to copy the files or move them
allow_duplicates = False  # Whether to allow duplicate files in the output directory
# End configuration

photo_metadata = list(takeout.rglob("*.json"))  # Get a list of all JSON metadata files
ignored_files = [
    'metadata.json',
    'print-subscriptions.json',
    'shared_album_comments.json',
    'user-generated-memory-titles.json'
]  # List of files to ignore during the organization process

def generate_name(date, from_path):
    """
    Generate a new name for the photo based on the given date and original file path.

    Args:
        date (datetime.datetime): The date and time when the photo was taken.
        from_path (pathlib.Path): The original file path of the photo.

    Returns:
        str: The new name for the photo.
    """
    if keep_original_titles:
        return from_path.name
    extension = from_path.suffix
    return date.strftime(title_format) + extension

def should_rename(from_path, to_path):
    """
    Check if the photo should be renamed based on the from_path and to_path.

    Args:
        from_path (pathlib.Path): The original file path of the photo.
        to_path (pathlib.Path): The target file path for the photo.

    Returns:
        bool: True if the photo should be renamed, False otherwise.
    """
    if not to_path.exists():
        return False
    
    if allow_duplicates and to_path.exists():
        return True
    
    # Their sizes are different, so they are different files and we should rename
    return from_path.stat().st_size != to_path.stat().st_size

def move(from_path, to_path):
    """
    Move or copy the photo from the source path to the target path.

    Args:
        from_path (pathlib.Path): The source file path of the photo.
        to_path (pathlib.Path): The target file path for the photo.
    """
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
    """
    Get the file path of the image associated with the given JSON metadata.

    Args:
        json_path (pathlib.Path): The file path of the JSON metadata.
        json (dict): The parsed JSON metadata.

    Returns:
        pathlib.Path: The file path of the associated image.
    """
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
