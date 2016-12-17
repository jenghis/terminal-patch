#!/usr/bin/env python

"""Patch Terminal.app to stop color adjustments."""

import argparse
import binascii
import os
import plistlib
import re
import subprocess

# Precomputed offsets by version
PATCH_OFFSETS = {'2.6.1': 191876, '2.7.1': 201475}

def get_version_info(path):
    """Returns a string containing the Terminal.app version"""
    plist_path = os.path.join(path, 'Contents/Info.plist')
    plist = plistlib.readPlist(plist_path)
    return plist['CFBundleShortVersionString']

def find_method_offset(path):
    """Finds the start of the method in the binary code."""
    command = 'otool -ov "{}"'.format(path)
    output = subprocess.check_output(command, shell=True)
    method = 'adjustedColorWithRed:green:blue:alpha:withBackgroundColor:force:'
    pattern = '{}(.*?)imp 0x1(0*)([0-9a-f]*)'.format(method)
    match = re.search(pattern, output, re.DOTALL)
    offset = '0x{}'.format(match.group(3))
    return int(offset, 16)

def find_patch_offset(path, method_offset):
    """Finds where to start writing the patch bytes."""
    bin_file = open(path, 'rb')
    bin_file.seek(method_offset)
    bin_data = bin_file.read(128)  # Should be in the first 128 bytes
    bin_file.close()
    hex_data = binascii.hexlify(bin_data)
    pattern = '4d85ff'  # Comparison op preceding conditional jump
    match = re.search(pattern, hex_data)
    return method_offset + (match.end() / 2)  # Two hex digits per byte

def apply_patch(path, offset):
    """Replaces the bytes at the offset with the patch bytes."""
    patch = '90e9'  # Change to unconditional jump
    patch_bytes = binascii.unhexlify(patch)
    bin_file = open(path, 'r+b')
    bin_file.seek(offset)
    bin_file.write(patch_bytes)
    bin_file.close()

def patch(path):
    """Compute the offset then patch the file."""
    version = get_version_info(path)
    bin_path = os.path.join(path, 'Contents/MacOS/Terminal')
    if version in PATCH_OFFSETS:
        patch_offset = PATCH_OFFSETS[version]
    else:
        method_offset = find_method_offset(bin_path)
        patch_offset = find_patch_offset(bin_path, method_offset)
    apply_patch(bin_path, patch_offset)
    print "Success!"

def check_path(path):
    """Check that the path is valid."""
    system_path = '/Applications/Utilities/Terminal.app'
    if os.path.samefile(path, system_path):
        print 'warning: SIP must be disabled to patch the system Terminal.app'
    bin_path = os.path.join(path, 'Contents/MacOS/Terminal')
    if not os.path.isfile(bin_path):
        raise IOError('invalid path to Terminal.app')

def main():
    parser = argparse.ArgumentParser()
    parser.description = 'Patch Terminal.app to stop color adjustments'
    parser.add_argument('path', help='Path to Terminal.app')
    args = parser.parse_args()
    path = args.path
    check_path(path)
    patch(path)

if __name__ == '__main__':
    main()
