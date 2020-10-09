import hashlib
import os
import argparse
from datetime import datetime
import xxhash

parser = argparse.ArgumentParser(
    prog='co-dot-py',
    description='A little cli tool for moving things around'
    )
parser.version = '0.0.2'

parser.add_argument(
    '-s',
    metavar='path/to/source',
    type=str,
    help='Source file'
    )
parser.add_argument(
    '-d',
    metavar='path/to/destination',
    type=str,
    help='Destination file'
    )
parser.add_argument(
    '-x',
    action='store_true',
    help='Select xxHash instead of md5')



def copy_file(src_path, dst_path, x=False):
    with open(src_path, 'rb') as src, open(dst_path, 'wb+') as dst:
        before = datetime.now()

        src_stats = os.stat(src_path)
        src_time = (src_stats.st_atime, src_stats.st_mtime)
        filesize = src_stats.st_size#os.path.getsize(src_path)
        done = 0
        progress_print = '0'

        hash_func, hash_type = [xxhash.xxh64(), 'xxHash'] if x else [hashlib.md5(), 'md5']
        h_src = hash_func
        h_dst = hash_func

        while True:
            chunk_src = src.read(4096)
            chunk_size = len(chunk_src)
            if chunk_src == b'':
                break

            # Update source hash data and write chunk:
            h_src.update(chunk_src)
            dst.write(chunk_src)

            # Read destination and update its hash:
            dst.seek(-chunk_size, 1)
            chunk_dst = dst.read(chunk_size)
            h_dst.update(chunk_dst)

            # # Comparing each chunk on its own - as plain bytes,
            # # and bail out on any error:
            # if ( chunk_src != chunk_dst ):
            #     raise Exception('chunk mismatch')
            # # From the first tests this approach didn't seem to be much faster
            # # than xxHash.

            done += chunk_size
            progress = int((done/filesize) * 100)
            if progress != progress_print:
                progress_print = progress
                print('Copying: ' + str(progress_print)+ '%',end="\r",flush=True)

        # TODO: store hashcode to file
        hash_src = h_src.hexdigest()
        hash_dst = h_dst.hexdigest()

        if ( hash_src != hash_dst ):
            print('src: ' + hash_src)
            print('dst: ' + hash_dst)
            raise Exception('hash mismatch')

        # Copy atime and mtime from src to dst
        os.utime(dst_path, src_time)

        print('Copying: done!')
        print(f'source hash ({hash_type}): {hash_src}')
        print(f'destination hash ({hash_type}): {hash_dst}')
        print('total time: ', datetime.now() - before)


if __name__ == "__main__":
    args = parser.parse_args()
    copy_file(args.s, args.d, args.x)
