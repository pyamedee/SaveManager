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
        self.auto_renumber = cfg['Main'].getboolean('automatically_renumber')

        style = ttk.Style()
        style.configure('B.TButton', foreground='black', justify='left')
        style.configure('G.TButton', foreground='black', justify='left', font=('Consolas', 8, 'bold'))

        style.configure('G.TLabel', foreground='#009000', justify='left', font=('Consolas', 8))
        style.configure('R.TLabel', foreground='red', justify='left', font=('Consolas', 8))

        self.reorganisation_focus = ''

        self.ds_path = os.path.normpath(cfg['Main']['ds_path'])
        self.saves_path = os.path.normpath(self.ds_path + '\\' + cfg['Main']['saves_dir'])
        if not os.path.exists(self.saves_path):
            os.mkdir(self.saves_path)
        
        self.entry = self.import_button = self.buttons = self.txt_var = self.label = self.delete_button = None

        self.init_widgets()

        self.state = 'default'

    def focus2entry(self, _):
        self.entry.focus_set()

    def sort_buttons(self):
        if self.sorting_type == 'alphabetical':
            self.buttons = dict(sorted(self.buttons.items(), key=lambda pair: pair[0]))

    def init_widgets(self):
        self.buttons = dict()

        i = 0
        suffix = '.sl2'
        for i, path in enumerate(iglob(self.saves_path + r'\*' + suffix)):
            i += 1
            path = os.path.normpath(path)
            name = path.split('\\')[-1].replace(suffix, '')
            
            button = ttk.Button(self, text=name, command=self.define_callback(name))
            self.buttons[name] = button
            button.grid(column=0, row=i)

        self.sort_buttons()

        self.txt_var = tk.StringVar(self)
        self.label = ttk.Label(self, textvariable=self.txt_var)
        self.label.grid(column=0, row=0, columnspan=2)

        self.entry = tk.Entry(self)
        self.entry.grid(column=0, row=i + 2)
        self.entry.bind('<Return>', self.import_save)
        self.entry.bind('<Control-Alt-d>', self.deleting_state)
        self.entry.bind('<Control-Alt-r>', self.activate_reorganising_state)
        self.entry.bind('<F2>', self.activate_renaming_state)
        self.entry.bind('<Up>', self.move_save_up)
        self.entry.bind('<Down>', self.move_save_down)
        self.entry.bind('<Escape>', self.stop_reorganising)

        self.import_button = ttk.Button(self, text='import', command=self.import_save)
        self.import_button.grid(column=1, row=i + 2)

        self.delete_button = ttk.Button(self, text='delete', command=self.deleting_state)
        self.delete_button.grid(column=1, row=i + 3)

        self.menubar = tk.Menu(self)

        self.menu1 = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Basic Tools', menu=self.menu1)
        self.menu1.add_command(label='Import', command=self.import_save, accelerator='Enter')
        self.menu1.add_command(label='Delete', command=self.deleting_state, accelerator='Ctrl+Alt+d')
        self.menu1.add_command(label='Rename', command=self.activate_renaming_state, accelerator='F2')

        self.menu2 = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Organise', menu=self.menu2)
        self.menu2.add_command(label='Number the saves', command=self.number_the_saves)
        self.menu2.add_command(label='Reverse numbering the saves', command=self.reverse_numbering)
        self.menu2.add_command(label='Renumber the saves', command=self.renumber_the_saves)
        self.menu2.add_command(label='Reorganise', command=self.activate_reorganising_state, accelerator='Ctrl-Alt-r')

        self.configure(menu=self.menubar)

        if self.sorting_type != 'default':
            self.reinit_widgets()

    def number_the_saves(self):
        new_dict = dict()
        length = len(str(len(self.buttons)))
        for i, (key, value) in enumerate(self.buttons.items()):
            i += 1
            button_name = '0' * (length - len(str(i))) + str(i) + ' ' + key
            new_dict[button_name] = value
            value['text'] = button_name
            value['command'] = self.define_callback(button_name)
            os.rename(self.saves_path + f'\\{key}.sl2', self.saves_path + f'\\{button_name}.sl2')

        self.buttons = new_dict
        self.reinit_widgets()

    def renumber_the_saves(self):
        new_dict = dict()
        length = len(str(len(self.buttons)))
        for i, (key, value) in enumerate(self.buttons.items()):
            i += 1
            try:
                n, reversed_key = key.split(' ', 1)
                if not n.isdecimal():
                    reversed_key = key
            except ValueError:
                reversed_key = key

            button_name = '0' * (length - len(str(i))) + str(i) + ' ' + reversed_key
            new_dict[button_name] = value
            value['text'] = button_name
            value['command'] = self.define_callback(button_name)
            os.rename(self.saves_path + f'\\{key}.sl2', self.saves_path + f'\\{button_name}.sl2')

        self.buttons = new_dict
        self.reinit_widgets()

    def reverse_numbering(self):
        new_dict = dict()
        for key, value in self.buttons.items():
            button_name = key.split(' ', 1)[-1]
            while button_name in new_dict:
                button_name += '\''
            new_dict[button_name] = value
            value['text'] = button_name
            value['command'] = self.define_callback(button_name)
            os.rename(self.saves_path + f'\\{key}.sl2', self.saves_path + f'\\{button_name}.sl2')

        self.buttons = new_dict
        self.reinit_widgets()

    def activate_reorganising_state(self, _=None):
        self.state = 'reorganising'
        self.txt_var.set('reorganising')
        self.label['style'] = 'G.TLabel'

    def activate_renaming_state(self, _=None):
        self.stop_reorganising()
        self.state = 'renaming'
        self.label['style'] = 'G.TLabel'
        self.txt_var.set('select a save to rename')

    def rename_save(self, name):
        self.state = 'default'
        self.txt_var.set('')

        new_name = self.entry.get()
        if new_name:
            try:
                os.rename(self.saves_path + f'\\{name}.sl2', self.saves_path + f'\\{new_name}.sl2')
            except FileExistsError:
                self.label['style'] = 'R.TLabel'
                self.txt_var.set('this name already exists')
            else:
                button = self.buttons[name]
                self.buttons.pop(name)
                self.buttons[new_name] = button

                button['text'] = new_name
                button['command'] = self.define_callback(new_name)
                self.reinit_widgets()
                if self.auto_renumber:
                    self.renumber_the_saves()

            self.entry.delete(0, 'end')
        else:
            self.label['style'] = 'R.TLabel'
            self.txt_var.set('this entry should not be empty')

    def define_callback(self, name):
        def callback():
            self.activate(name)
        return callback

    def deleting_state(self, _=None):
        self.stop_reorganising()
        self.state = 'deleting'
        self.label['style'] = 'R.TLabel'
        self.txt_var.set('select a save to delete')

    def activate(self, name):
        if self.state == 'deleting':
            self.delete_save(name)
        elif self.state == 'renaming':
            self.rename_save(name)
        elif self.state == 'reorganising':
            if self.reorganisation_focus:
                self.buttons[self.reorganisation_focus]['style'] = 'B.TButton'
            self.reorganisation_focus = name
            self.focus_message()
        else:
            self.txt_var.set(f'save "{name}" has been loaded')
            self.label['style'] = 'G.TLabel'
            copyfile(self.saves_path + f'\\{name}.sl2', self.ds_path + '\\DS30000.sl2')

    def focus_message(self):
        self.txt_var.set('focus is currently to "' + self.reorganisation_focus + '"')
        self.buttons[self.reorganisation_focus]['style'] = 'G.TButton'

    def move_save_up(self, _=None):
        if self.reorganisation_focus:
            name = self.reorganisation_focus
            str_number, without_number_name = name.split(' ', 1)
            length = len(str_number)
            number = int(str_number)

            new_dict = dict()
            new_name = name
            for i, (key, value) in enumerate(self.buttons.items()):
                i += 1
                if i == number - 1:
                    new_name = '0' * (length - len(str(i))) + str(i) + ' ' + without_number_name
                    os.rename(self.saves_path + f'\\{name}.sl2', self.saves_path + f'\\{new_name}.sl2')

                    new_key = '0' * (length - len(str(number))) + str(number) + ' ' + key.split(' ', 1)[-1]
                    os.rename(self.saves_path + f'\\{key}.sl2', self.saves_path + f'\\{new_key}.sl2')
                    new_dict[new_key] = value
                    value['text'] = new_key
                    value['command'] = self.define_callback(new_key)

                elif i == number:
                    new_dict[new_name] = value
                    value['text'] = new_name
                    value['command'] = self.define_callback(new_name)
                else:
                    new_dict[key] = value
            self.reorganisation_focus = new_name
            self.buttons = new_dict
            self.focus_message()
            self.reinit_widgets()

    def move_save_down(self, _=None):
        if self.reorganisation_focus:
            name = self.reorganisation_focus
            str_number, without_number_name = name.split(' ', 1)
            length = len(str_number)
            number = int(str_number)

            new_dict = dict()
            new_name = name
            for i, (key, value) in enumerate(self.buttons.items()):
                i += 1
                if i == number + 1:
                    new_name = '0' * (length - len(str(i))) + str(i) + ' ' + without_number_name
                    os.rename(self.saves_path + f'\\{name}.sl2', self.saves_path + f'\\{new_name}.sl2')

                    new_key = '0' * (length - len(str(number))) + str(number) + ' ' + key.split(' ', 1)[-1]
                    os.rename(self.saves_path + f'\\{key}.sl2', self.saves_path + f'\\{new_key}.sl2')
                    new_dict[new_key] = value
                    value['text'] = new_key
                    value['command'] = self.define_callback(new_key)
                elif number == i:
                    pass
                else:
                    new_dict[key] = value

            new_dict[new_name] = self.buttons[name]
            self.buttons[name]['text'] = new_name
            self.buttons[name]['command'] = self.define_callback(new_name)

            self.reorganisation_focus = new_name
            self.buttons = new_dict
            self.focus_message()
            self.reinit_widgets()

    def stop_reorganising(self, _=None):
        if self.reorganisation_focus:
            self.buttons[self.reorganisation_focus]['style'] = 'B.TButton'
            self.reorganisation_focus = ''
            self.state = 'default'
            self.txt_var.set('')
        if self.state == 'reorganising':
            self.state = 'default'
            self.txt_var.set('')

    def delete_save(self, name):
        self.destroy_button(name)
        self.reinit_widgets()
        os.remove(self.saves_path + f'\\{name}.sl2')
        self.state = 'default'
        self.txt_var.set('')

        if self.auto_renumber:
            self.renumber_the_saves()

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
        self.stop_reorganising()
        self.state = 'default'
        name = self.entry.get()
        if not name:
            self.entry.focus_set()
            self.label['style'] = 'R.TLabel'
            self.txt_var.set('this entry should not be empty')
            return

        self.txt_var.set('')
        self._import_save(name)
        self.new_button(name)
        self.entry.select_range(0, 'end')

        if self.auto_renumber:
            self.renumber_the_saves()

    def _import_save(self, asname):
        copyfile(self.ds_path + '\\DS30000.sl2', self.saves_path + f'\\{asname}.sl2')


if __name__ == "__main__":
    cfg = read_configs()
    window = Window(cfg)
    window.mainloop()

