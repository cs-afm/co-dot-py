import hashlib
import os
import sys
import argparse
import xxhash # (this library can be installed with "pip install xxhash"/"pip3 install xxhash")
from datetime import datetime

src_path, dst_path = sys.argv[1:3]
parser = argparse.ArgumentParser(
    prog='co-dot-py',
    description='multiplatform as-fast-as-we-can file transfer script'
    )
parser.version = '0.0.1'

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
    with open(src_path, 'rb') as src, open(dst_path, 'wb+') as dst: # Here we need to open the destination file in 'wb+' mode to be able to read it as well
        before = datetime.now()

        filesize = os.path.getsize(src_path)
        done = 0
        progress_print = '0'

        hash_func, hash_type = [xxhash.xxh64(), 'xxHash'] if x else [hashlib.md5(), 'md5']
        h_src = hash_func
        h_dst = hash_func

        while True:
            chunk_src = src.read(4096)
            chunk_size = len(chunk_src) # This can be less than 4 KiB, at the end of the file, right?
            if chunk_src == b'':
                break

            # Update source hash data and write chunk:
            h_src.update(chunk_src)
            dst.write(chunk_src)

            # Read destination here already, instead of an extra loop:
            dst.seek(-chunk_size, 1) # We need to move the file handle back to the position where it was before writing the last chunk of dst
            chunk_dst = dst.read(chunk_size)
            h_dst.update(chunk_dst)

            # Comparing each chunk on its own - as plain bytes,
            # and bail out on any error:
            # if ( chunk_src != chunk_dst ):
            #     raise Exception('chunk mismatch')

            done += chunk_size
            progress = int((done/filesize) * 100)
            if progress != progress_print:
                progress_print = progress
                print('Copying: ' + str(progress_print)+ '%',end="\r",flush=True)

        # The hashcodes ready here could be stored to or read from a file for (later) comparison.
        hash_src = h_src.hexdigest()
        hash_dst = h_dst.hexdigest()

        if ( hash_src != hash_dst ):
            print('src: ' + hash_src)
            print('dst: ' + hash_dst)
            raise Exception('hash mismatch')
        
        print('Copying: done!')
        print(f'source hash ({hash_type}): {hash_src}')
        print(f'destination hash ({hash_type}): {hash_dst}')
        print('total time: ', datetime.now() - before)


if __name__ == "__main__":
    args = parser.parse_args()
    copy_file(args.s, args.d, args.x)