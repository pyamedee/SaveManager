# -*- coding:Utf-8 -*-

from glob import iglob
import os
from main import read_configs

def _changing(value, change_type):
    cfg = read_configs()

    for path in iglob(cfg['Main']['ds_path'] + '\\' + cfg['Main']['saves_dir'] + '\\*.sl2'):
        path = os.path.normpath(path)
        split_path = path.split('\\')
        
        if change_type == 'adding':
            split_path[-1] = value + split_path[-1]
        else:
            if split_path[-1].startswith(value):
                split_path[-1] = split_path[-1][len(value):]
        new_path = '\\'.join(split_path)
        
        os.rename(path, new_path)

def adding(prefix):
    _changing(prefix, 'adding')

def removing(value):
    _changing(prefix, 'removing')

if __name__ == "__main__":
    prefix = input('prefix : ')
    add_or_remove = input('add or remove : ')
    if add_or_remove == 'add':
        adding(prefix)
    elif add_or_remove == 'remove':
        removing(prefix)

    input('done.')
