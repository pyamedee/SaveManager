# -*- coding:Utf-8 -*-

import tkinter as tk
from tkinter import ttk
from configparser import ConfigParser
import os
from glob import iglob
from shutil import copyfile


def read_configs():
    cfg = ConfigParser()
    cfg.read('config.ini', encoding='utf8')

    return cfg

class Window(tk.Tk):

    def __init__(self, cfg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<FocusIn>', self.focus2entry)

        self.sorting_type = cfg['Main']['sorting_type']

        self.ds_path = os.path.normpath(cfg['Main']['ds_path'])
        self.saves_path = os.path.normpath(self.ds_path + '\\' + cfg['Main']['saves_dir'])
        if not os.path.exists(self.saves_path):
            os.mkdir(self.saves_path)
        
        self.entry = self.import_button = None

        self.init_widgets()

        self.is_deleting = False
        self.is_renaming = False

    def focus2entry(self, _):
        self.entry.focus_set()

    def sort_buttons(self):
        if self.sorting_type == 'alphabetical':
            self.buttons = dict(sorted(self.buttons.items(), key=lambda pair: pair[0]))

    def init_widgets(self):
        self.buttons = dict()

        i = 0
        suffix = '.sl2'
        for i, path in enumerate(iglob(self.saves_path + '\*' + suffix)):
            i += 1
            path = os.path.normpath(path)
            name = path.split('\\')[-1].replace(suffix, '')
            
            button = ttk.Button(self, text=name, command=self.define_callback(name))
            self.buttons[name] = button
            button.grid(column=0, row=i)

        self.sort_buttons()

        self.txt_var = tk.StringVar(self)
        self.label = tk.Label(self, textvariable=self.txt_var, justify='left', font=('Consolas', 8, 'italic'), fg='red')
        self.label.grid(column=0, row=0, columnspan=2)

        self.entry = tk.Entry(self)
        self.entry.grid(column=0, row=i + 2)
        self.entry.bind('<Return>', self.import_save)
        self.entry.bind('<Control-Alt-d>', self.deleting_state)
        self.entry.bind('<F2>', self.activate_renaming_state)

        self.import_button = ttk.Button(self, text='import', command=self.import_save)
        self.import_button.grid(column=1, row=i + 2)

        self.delete_button = ttk.Button(self, text='delete', command=self.deleting_state)
        self.delete_button.grid(column=1, row=i + 3)

        if self.sorting_type != 'default':
            self.reinit_widgets()

    def activate_renaming_state(self, _=None):
        self.is_renaming = True
        self.is_deleting = False
        self.label['fg'] = 'green'
        self.txt_var.set('select a save to rename')

    def rename_save(self, name):
        self.is_renaming = False
        self.txt_var.set('')

        new_name = self.entry.get()
        if new_name:
            try:
                os.rename(self.saves_path + f'\\{name}.sl2', self.saves_path + f'\\{new_name}.sl2')
            except FileExistsError:
                self.label['fg'] = 'red'
                self.txt_var.set('this name already exists')
            else:
                button = self.buttons[name]
                self.buttons.pop(name)
                self.buttons[new_name] = button

                button['text'] = new_name
                button['command'] = self.define_callback(new_name)
                self.reinit_widgets()

            self.entry.delete(0, 'end')
        else:
            self.label['fg'] = 'red'
            self.txt_var.set('this entry should not be empty')

    
    def define_callback(self, name):
        def callback():
            self.activate(name)
        return callback

    def deleting_state(self, _=None):
        self.is_deleting = True
        self.is_renaming = False
        self.label['fg'] = 'red'
        self.txt_var.set('select a save to delete')

    def activate(self, name):
        if self.is_deleting:
            self.delete_save(name)
        elif self.is_renaming:
            self.rename_save(name)
        else:
            copyfile(self.saves_path + f'\\{name}.sl2', self.ds_path + '\\DS30000.sl2')

    def delete_save(self, name):
        self.destroy_button(name)
        self.reinit_widgets()
        os.remove(self.saves_path + f'\\{name}.sl2')
        self.is_deleting = False
        self.txt_var.set('')

    def destroy_button(self, name):
        self.buttons[name].grid_forget()
        self.buttons.pop(name)

    def reinit_widgets(self):
        self.sort_buttons()

        i = 0
        for i, button in enumerate(self.buttons.values()):
            i += 1
            button.grid_forget()
            button.grid(column=0, row=i)


        self.label.grid_forget()
        self.label.grid(column=0, row=0, columnspan=2)

        self.entry.grid_forget()
        self.entry.grid(column=0, row=i + 2)

        self.import_button.grid_forget()
        self.import_button.grid(column=1, row=i + 2)

        self.delete_button.grid_forget()
        self.delete_button.grid(column=1, row=i + 3)

    def new_button(self, name):
        if name in self.buttons:
            self.destroy_button(name)
        self.buttons[name] = ttk.Button(self, text=name, command=self.define_callback(name))
        self.reinit_widgets()

    def import_save(self, _=None):
        self.is_deleting = False
        self.is_renaming = False
        name = self.entry.get()
        if not name:
            self.entry.focus_set()
            self.label['fg'] = 'red'
            self.txt_var.set('this entry should not be empty')
            return

        self.txt_var.set('')
        self._import_save(name)
        self.new_button(name)
        self.entry.select_range(0, 'end')

    def _import_save(self, asname):
        copyfile(self.ds_path + '\\DS30000.sl2', self.saves_path + f'\\{asname}.sl2')

if __name__ == "__main__":
    cfg = read_configs()
    window = Window(cfg)
    window.mainloop()

