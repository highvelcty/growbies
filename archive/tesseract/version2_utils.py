#!/usr/bin/env python3
from pathlib import Path

def write_ground_truth():
    path_to_version_1 = Path('/home/meyer/tmp/level2/version_1')
    path_to_raw_gt = path_to_version_1 / 'corrected_by_hand_scale_mm.csv'
    path_to_mm = path_to_version_1 / 'mm-ground-truth'
    path_to_scale = path_to_version_1 / 'scale-ground-truth'

    with open(path_to_raw_gt, 'r') as inf:
        for line in list(inf.readlines())[1:]:
            filename_no_suffix, scale_gt, mm_gt = line.split(',')
            filename = filename_no_suffix + '.gt.txt'
            path_to_mm_file = path_to_mm / filename
            path_to_scale_file = path_to_scale / filename

            with open(path_to_mm_file, 'w') as outf:
                outf.write(f'{mm_gt}\n')

            with open(path_to_scale_file, 'w') as outf:
                outf.write(f'{scale_gt}\n')

if __name__ == '__main__':
    write_ground_truth()
