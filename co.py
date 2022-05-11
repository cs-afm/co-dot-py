import csv
import os
import argparse
import hashlib
from pathlib import Path
import xxhash
import json
from datetime import datetime

VERSION = '0.2.6'

parser = argparse.ArgumentParser(
    prog='co-dot-py',
    description='A little cli tool for moving things around'
    )
parser.version = VERSION

parser.add_argument(
    '-s',
    metavar='path/to/source',
    type=str,
    help='Source path (file or directory)'
    )
parser.add_argument(
    '-d',
    metavar='path/to/destination',
    type=str,
    help='Destination path (directory)'
    )
parser.add_argument(
    '-x',
    action='store_true',
    help='Select xxHash instead of md5')

parser.add_argument(
    '-m',
    action='store_true',
    help='Dump hashcodes on a JSON manifest .Filename pattern: "filename_HASHTYPE.json" (e.g. "video.mp4_md5.json")')

parser.add_argument(
    '-r',
    action='store_true',
    help='Recursive mode: co.pies everything from the source path')

parser.add_argument(
    '-hib',
    action='store_true',
    help='High buffer size')

parser.add_argument(
    '-l',
    action='store_true',
    help='Legacy manifest format (.json)')
### ### ### ###
def adjust_filesize(size):
    for unit in ['B','KiB','MiB','GiB','TiB','PiB','EiB','ZiB']:
        if abs(size) < 1024.0:
            return f'{round(size, 2)} {unit}'
        size /= 1024.0
    return f'{round(size, 2)} YiB'

def get_transfer_speed(transferred_size, start_time):
    delta = datetime.now() - start_time
    timedelta_milliseconds = (delta.seconds * 1000) + (delta.microseconds / 1000)
    timedelta_seconds = timedelta_milliseconds / 1000
    if timedelta_seconds > 0:
        transferred_bytes = (transferred_size / timedelta_seconds)
        return adjust_filesize(transferred_bytes)
    return 'unknown'
### ### ### ###
def copy_file(src_path, dst_path, xxHash_switch, buffersize, caller='myself'):
    if os.path.isdir(dst_path):
        dst_path = os.path.join(dst_path, os.path.basename(src_path))

    while os.path.exists(dst_path):
        dst_path = os.path.join(
            os.path.dirname(dst_path),
            f'co.py_{os.path.basename(dst_path)}'
        )

    with open(src_path, 'rb') as src, open(dst_path, 'wb+') as dst:
        src_stats = os.stat(src_path)
        src_timestamps = (src_stats.st_atime, src_stats.st_mtime)
        filesize = src_stats.st_size
        transferred_size = 0
        progress_print = 0

        hash_func, hash_type = [xxhash.xxh3_128, 'xxHash-128'] if xxHash_switch else [hashlib.md5, 'md5']
        hash_src = hash_func()
        hash_dst = hash_func()

        start_time = datetime.now()
        while True:
            chunk_src = src.read(buffersize)
            chunk_size = len(chunk_src)
            if chunk_src == b'':
                break

            # Update source hash data and write chunk:
            hash_src.update(chunk_src)
            dst.write(chunk_src)

            # Read destination and update its hash:
            dst.seek(-chunk_size, 1)
            chunk_dst = dst.read(chunk_size)
            hash_dst.update(chunk_dst)

            transferred_size += chunk_size
            transfer_speed = get_transfer_speed(transferred_size, start_time)
            progress = int((transferred_size / filesize) * 100)
            if progress != progress_print:
                progress_print = progress
                print(f'Copying "{os.path.basename(src_path)}": {str(progress_print)}% - Transferred: {adjust_filesize(transferred_size)}/{adjust_filesize(filesize)} (at {transfer_speed}/s) - {datetime.now() - start_time}', end="\r", flush=True)

        hash_src = hash_src.hexdigest()
        hash_dst = hash_dst.hexdigest()

        if ( hash_src != hash_dst ):
            print('src: ' + hash_src)
            print('dst: ' + hash_dst)
            raise Exception('hash mismatch')

        # Copy atime and mtime from src to dst
        os.utime(dst_path, src_timestamps)

        if caller == 'myself':
            print(' ' * 200, end="\r", flush=True)
            print('Copying: done!')
            print(f'Source path: "{src_path}"')
            print(f'Source hash ({hash_type}): "{hash_src}"')
            print(f'Destination path: "{dst_path}"')
            print(f'Destination hash ({hash_type}): "{hash_dst}"')
            print(f'Filesize: {adjust_filesize(filesize)}')
            print(f'Average speed: {get_transfer_speed(filesize, start_time)}/s')
            print(f'Total transfer time: {datetime.now() - start_time}')

        hash_tuple = (src_path, hash_dst, filesize)
        return hash_tuple, dst_path, filesize

def copy_dir(src_path, dst_path, xxHash_switch, buffersize):
    start_time = datetime.now()
    print('--------------------------------------------')
    dst_path = os.path.join(dst_path, os.path.basename(src_path))
    while os.path.exists(dst_path):
        dst_path = os.path.join(
            os.path.dirname(dst_path),
            f'co.py_{os.path.basename(dst_path)}'
        )
    os.mkdir(dst_path)

    hash_list = []
    total_files_transferred = 0
    total_size = 0
    for root, dirs, files in os.walk(src_path):
        clean_root = os.path.relpath(root, src_path)
        clean_root = clean_root[1:] if clean_root.startswith(os.path.sep) else clean_root
        for dir in dirs:
            os.mkdir(os.path.join(dst_path, clean_root, dir))
        
        for filename in [f for f in files if f != '.DS_Store']:
            hash_tuple, _, filesize = copy_file(
                os.path.join(root, filename),
                os.path.join(dst_path, clean_root, filename),
                xxHash_switch,
                buffersize,
                'copy_dir'
            )
            hash_list.append(hash_tuple)
            total_files_transferred += 1
            total_size += filesize

    print(' ' * 200, end="\r", flush=True)
    print('Copying: done!')
    print(f'Source path: "{src_path}"')
    print(f'Destination path: "{dst_path}"')
    print(f'Total size: {adjust_filesize(total_size)} ({total_files_transferred} files)')
    print(f'Average speed: {get_transfer_speed(total_size, start_time)}/s')
    print(f'Total transfer time: {datetime.now() - start_time}')
    print('............................................')

    return hash_list, dst_path, total_size

def dump_manifest(hash_list, xxHash_switch, dst, parent=False, legacy_format=False):
    hash_list.sort()
    hash_type = 'xxHash-128' if xxHash_switch else 'md5'
    if legacy_format:

        manifest = {
            '_DATETIME': datetime.now().strftime('%Y-%m-%d.%H:%M'),
            '_HASH_TYPE': hash_type,
            '_HASHCODES': {}
        }

        for hash in hash_list:
            key = hash[0].split(parent)[-1] if parent else os.path.basename(hash[0])
            manifest['_HASHCODES'][key] = hash[1]

        if parent:
            manifest['_LENGTH'] = len(hash_list)
            manifest['_PARENT_FOLDER'] = os.path.basename(parent)

        with open(f'{dst}_{hash_type}.json', 'w') as json_manifest:
            json_manifest.write(json.dumps(manifest, indent=4))
    
    else:
        with open(f'{dst}__HASHCODES.csv', 'w', newline='', encoding='utf-8') as csv_manifest:
            manifest = csv.writer(csv_manifest)
            
            manifest.writerow([
                f'#CREATOR::co.py-{VERSION}',
                '', '', ''
            ])
            manifest.writerow([
                f'#LENGTH::{len(hash_list)}',
                '', '', ''
            ])
            manifest.writerow([
                f'#DATETIME::{datetime.now().strftime("%Y-%m-%d.%H:%M")}',
                '', '', ''
            ])
            manifest.writerow(['Filename', 'Size (bytes)', 'md5', 'xxHash-128'])

            if parent:
                for f in hash_list:
                    path = Path(f[0]).relative_to(Path(parent).parent)
                    manifest.writerow([
                        f'{path}'.replace('\\', '/'),
                        f'{f[2]}',
                        f'{f[1]}' if not xxHash_switch else '',
                        f'{f[1]}' if xxHash_switch else ''
                    ])
            else:
                path = Path(hash_list[0][0])
                manifest.writerow([
                    f'{path.name}',
                    f'{hash_list[0][2]}',
                    f'{hash_list[0][1]}' if not xxHash_switch else '',
                    f'{hash_list[0][1]}' if xxHash_switch else ''
                ])

### ### ### ###
def co_py(args, src):
    if os.path.isfile(src):
        print('--------------------------------------------')
        hash_tuple, manifest_dst, _ = copy_file(src, args.d, args.x, buffersize)
        if args.m:
            dump_manifest([hash_tuple], args.x, manifest_dst, legacy_format=args.l)
        print('............................................')

    elif os.path.isdir(src):
        
        hash_list, manifest_dst, _ = copy_dir(src, args.d, args.x, buffersize)
        if args.m:
            dump_manifest(hash_list, args.x, manifest_dst, src, legacy_format=args.l)
        
### ### ### ###
if __name__ == "__main__":
    args = parser.parse_args()
    buffersize = (64 * 1024**2) if args.hib else (16 * 1024)

    if os.path.exists(args.s) and os.path.isdir(args.d):
        if args.r and os.path.isdir(args.s):
            root, dirs, files = next(os.walk(args.s))
            candidates = dirs + files

            for candidate in candidates:
                co_py(args, os.path.join(args.s, candidate))

        elif args.r: print('If you use the option -r the source path must be a folder, silly!')
        
        else: co_py(args, args.s)

    else: print("Something's wrong with your source and/or destination path")

    
