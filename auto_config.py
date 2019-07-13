# -*- coding:Utf-8 -*-

import os
from configparser import ConfigParser
import tkinter as tk
from tkinter.filedialog import askdirectory

def main():
    
    response = input('are you sure that you want to auto-configure this program ?\n[Y]es / [N]o\n').lower()
    
    if response == 'y' or response == 'yes':

        darksouls3 = os.path.normpath(os.environ['appdata'] + '\\DarkSoulsIII')
        dir_list = os.listdir(darksouls3 + '\\')

        for i, path in enumerate(dir_list):
            if path.endswith('.xml'):
                dir_list.pop(i)

        if len(dir_list) == 1:
            directory = os.path.join(darksouls3, dir_list[0])
        else:
            directory = askdirectory(initialdir=darksouls3, title='Please select the save file directory')

        cfg = ConfigParser()
        cfg['Main'] = {
            'ds_path': directory,
            'profile': 'save_manager.profile',
            'sorting_type': 'alphabetical',
            'automatically_renumber': 'true'
        }

        with open('config.ini', 'w', encoding='utf8') as configfile:
            cfg.write(configfile)

        return input('Done.\n')
        
    elif response != 'no' and response != 'n':
        print('Response not understood, interpreted as "No".')
    return input('Press Enter to quit.')

if __name__ == "__main__":
    main()
