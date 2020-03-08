# -*- coding:Utf-8 -*-

import os
import tkinter as tk
import tkinter.font
from configparser import ConfigParser
from glob import iglob
from shutil import copyfile, rmtree
from tkinter import ttk
from tkinter.messagebox import askokcancel


def read_configs():
    cfg = ConfigParser()
    cfg.read('config.ini', encoding='utf8')

    return cfg


class App(tk.Tk):

    def __init__(self, cfg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.cfg = cfg
        self.current_profile = None
        self.change_profile_menu = None

        self.game = cfg['Main']['game']

        self.title('Save Manager ' + self.game)
        self.iconbitmap(r'.\icon.ico')

        default_font = tk.font.Font(
            family='Consolas',
            size=8
        )

        self.font1 = default_font

        style = ttk.Style()
        ttk.Style().configure('B.TButton', foreground='black', justify='left', font=default_font)
        ttk.Style().configure('FOCUS.TButton', foreground='#100000', justify='left', font=('Consolas', 8, 'bold italic'))
        self.car_width = self.font1.measure(' ')

        ttk.Style().configure('G.TLabel', foreground='#009000', justify='left', font=('Consolas', 9, 'italic'))
        ttk.Style().configure('R.TLabel', foreground='red', justify='left', font=('Consolas', 9, 'italic'))

    def destroy_profile(self):
        self.unbind('<FocusIn>')
        self.current_profile.destroy()
        self.current_profile = None

        self.create_change_profile_menu()
        self.bind('<FocusIn>', self.change_profile_menu.focus2entry)

    def create_profile_window(self):
        self.unbind('<FocusIn>')
        self.current_profile = self.Profile(self, self.cfg)
        self.bind('<FocusIn>', self.current_profile.focus2entry)

    def create_change_profile_menu(self):
        self.change_profile_menu = self.ChangeProfileMenu(self, self.cfg)

    def change_to_profile(self, name):
        self.cfg['Main']['profile'] = name
        with open('config.ini', 'w', encoding='utf8') as configfile:
            self.cfg.write(configfile)

        self.change_profile_menu.destroy()
        self.change_profile_menu = None

        self.create_profile_window()

    def remove_former_profiles(self):
        response = askokcancel('Clean former profiles', 'Are you sure you want to delete the backups of deleted profiles?')
        if response:
            for former_profile_path in iglob(self.cfg['Main']['ds_path'] + '\\*.formerprofile'):
                rmtree(former_profile_path)


    class ChangeProfileMenu(tk.Frame):
        def __init__(self, root, cfg, *args, **kwargs):
            super().__init__(root, *args, **kwargs)
            self.pack(fill='both', expand=True)

            self.state = 'default'
            self.root = root

            self.profiles = dict()

            game = self.root.game
            if game == 'ds1':
                self.ds_path = os.path.normpath(cfg['Main']['ds1_path'])
            elif game == 'ds3':
                self.ds_path = os.path.normpath(cfg['Main']['ds3_path'])

            for i, profile_path in enumerate(iglob(self.ds_path + '\\*.profile')):
                i += 1
                profile_name = profile_path.split('\\')[-1]
                profile_name = profile_name.replace('.profile', '')
                button = ttk.Button(self, command=self.define_callback(profile_name), text=profile_name, style='B.TButton')
                button.grid(row=i, column=0, sticky='w')
                self.profiles[profile_name] = button

            self.entry = tk.Entry(self, width=28)
            self.entry.grid(row=i + 1, column=0)
            self.entry.focus_set()
            self.entry.bind('<Return>', self.new_profile)
            self.entry.bind('<F2>', self.activate_renaming_state)
            self.entry.bind('<Control-w>', self.activate_deleting_state)

            self.adjust()

        def focus2entry(self, _=None):
            self.entry.focus_set()

        def activate_renaming_state(self, _=None):
            self.state = 'renaming'

        def activate_deleting_state(self, _=None):
            self.state = 'deleting'

        def new_profile(self, _=None):
            name = self.entry.get()
            if name:
                self.activate(name)

        def adjust(self):
            ref = 0
            car_width = 0
            measuring = dict()
            for key, value in self.profiles.items():
                style = value['style']
                font = self.root.font1
                measure = font.measure(key)
                ref = max(measure, ref)
                measuring[key] = measure

            for key, button in self.profiles.items():
                button['text'] = key + ((ref - measuring[key]) // self.root.car_width + 1) * ' '

        def define_callback(self, name):
            def callback():
                return self.activate(name)
            return callback

        def activate(self, name):
            if self.state == 'default':
                self.change_to_profile(name)
            elif self.state == 'renaming':
                self.state = 'default'
                new_name = self.entry.get()
                if new_name:
                    button = self.profiles[name]
                    button['text'] = new_name
                    button['command'] = self.define_callback(new_name)
                    os.rename(self.ds_path + '\\' + name + '.profile', self.ds_path + '\\' + new_name + '.profile')
                    self.profiles.pop(name)
                    self.profiles[new_name] = button
                    self.adjust()
                    self.entry.delete(0, 'end')
            elif self.state == 'deleting':
                self.state = 'default'
                self.profiles.pop(name)

                didit = False
                to_add = ''
                while not didit:
                    try:
                        os.rename(self.ds_path + f'\\{name}.profile', self.ds_path + f'\\{name}{to_add}.formerprofile')
                    except FileExistsError:
                        to_add += "'"
                    else:
                        didit = True
                self.reinit_widgets()

        def change_to_profile(self, name):
            self.root.change_to_profile(name + '.profile')

        def reinit_widgets(self):
            for i, (key, value) in enumerate(self.profiles.items()):
                i += 1
                value.grid_forget()
                value.grid(row=i, column=0, sticky='w')

            self.entry.grid_forget()
            self.entry.grid(row=i + 1, column=0)

    class Profile(tk.Frame):

        def __init__(self, root, cfg, *args, **kwargs):
            super().__init__(root, *args, **kwargs)
            self.pack(fill='both', expand=True)

            self.root = root

            game = self.root.game
            self.game = game
            self.base_save_name = {'ds1': 'DRAKS0005', 'ds3': 'DS30000'}[game]

            self.sorting_type = cfg['Main']['sorting_type']
            self.auto_renumber = cfg['Main'].getboolean('automatically_renumber')

            self.reorganization_focus = ''
            
            if game == 'ds1':
                self.ds_path = os.path.normpath(cfg['Main']['ds1_path'])
            elif game == 'ds3':
                self.ds_path = os.path.normpath(cfg['Main']['ds3_path'])

            self.saves_path = os.path.normpath(self.ds_path + '\\' + cfg['Main']['profile'])
            if not os.path.exists(self.saves_path):
                os.mkdir(self.saves_path)
            
            self.entry = self.import_button = self.buttons = self.txt_var = self.label = self.delete_button = None

            self.init_widgets()

            self.state = 'default'

        def focus2entry(self, _=None):
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
                
                button = ttk.Button(self, text=name, command=self.define_callback(name), style='B.TButton')
                self.buttons[name] = button
                button.grid(column=0, row=i, sticky='w')

            self.sort_buttons()

            self.txt_var = tk.StringVar(self)
            self.label = ttk.Label(self, textvariable=self.txt_var)
            self.label.grid(column=0, row=0, columnspan=2)

            self.entry = tk.Entry(self, width=28)
            self.entry.grid(column=0, row=i + 2)
            self.entry.bind('<Return>', self.import_save)
            self.entry.bind('<Control-w>', self.deleting_state)
            self.entry.bind('<Control-Alt-r>', self.activate_reorganising_state)
            self.entry.bind('<F2>', self.activate_renaming_state)
            self.entry.bind('<Up>', self.move_save_up)
            self.entry.bind('<Down>', self.move_save_down)
            self.entry.bind('<Escape>', self.stop_reorganising)
            self.entry.bind('<Delete>', self.destroy_)
            
            self.focus2entry()

            self.import_button = ttk.Button(self, text='import', command=self.import_save)
            self.import_button.grid(column=1, row=i + 2)

            self.delete_button = ttk.Button(self, text='delete', command=self.deleting_state)
            self.delete_button.grid(column=1, row=i + 3)

            self.menubar = tk.Menu(self)

            self.menu1 = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label='Basic Tools', menu=self.menu1)
            self.menu1.add_command(label='Import', command=self.import_save, accelerator='Enter')
            self.menu1.add_command(label='Delete', command=self.deleting_state, accelerator='Ctrl+w')
            self.menu1.add_command(label='Rename', command=self.activate_renaming_state, accelerator='F2')
            self.game_switching_menu = tk.Menu(self.menu1, tearoff=0)
            self.menu1.add_cascade(label='Switch the game', menu=self.game_switching_menu)
            if self.game == 'ds3':
                self.game_switching_menu.add_command(label='Dark souls 1', command=lambda: self.switch_to('ds1'))
            elif self.game == 'ds1':
                self.game_switching_menu.add_command(label='Dark souls 3', command=lambda: self.switch_to('ds3'))

            self.menu2 = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label='Organise', menu=self.menu2)
            self.menu2.add_command(label='Number the saves', command=self.number_the_saves)
            self.menu2.add_command(label='Reverse numbering the saves', command=self.reverse_numbering)
            self.menu2.add_command(label='Renumber the saves', command=self.renumber_the_saves)
            self.menu2.add_command(label='Reorganise', command=self.activate_reorganising_state, accelerator='Ctrl-Alt-r')

            self.menu3 = tk.Menu(self.menubar, tearoff=0)
            self.menubar.add_cascade(label='Profile', menu=self.menu3)
            self.menu3.add_command(label='Change profile', command=self.destroy_, accelerator='Delete')
            self.menu3.add_command(label='Clean former profiles', command=self.root.remove_former_profiles)

            self.root.configure(menu=self.menubar)

            if self.sorting_type != 'default':
                self.reinit_widgets()

        def destroy_(self, _=None):
            self.root.destroy_profile()

        def number_the_saves(self):
            new_dict = dict()
            length = len(str(len(self.buttons)))
            for i, (key, value) in enumerate(self.buttons.items()):
                i += 1
                button_name = '{:0>{}} '.format(i, length) + key
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
                button_name = '{:0>{}} '.format(i, length) + reversed_key
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

        def adjust(self):
            ref = 0
            car_width = 0
            measuring = dict()
            for key, value in self.buttons.items():
                style = value['style']
                font = self.root.font1
                measure = font.measure(key)
                ref = max(measure, ref)
                measuring[key] = measure
            return measuring, ref

        def rename_save(self, name):
            self.state = 'default'
            self.txt_var.set('')

            new_name = self.entry.get()
            if new_name:
                try:
                    n, _ = name.split(' ', 1)
                    if not n.isdecimal():
                        raise ValueError
                except ValueError:
                    pass
                else:
                    new_name = n + ' ' + new_name
                
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
                    if self.auto_renumber:
                        self.sort_buttons()
                        self.renumber_the_saves()
                    else:
                        self.reinit_widgets()

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
                if self.reorganization_focus:
                    self.buttons[self.reorganization_focus]['style'] = 'B.TButton'
                self.reorganization_focus = name
                self.focus_message()
            else:
                self.txt_var.set(f'save "{name}" has been loaded')
                self.label['style'] = 'G.TLabel'
                copyfile(self.saves_path + f'\\{name}.sl2', self.ds_path + '\\' + self.base_save_name + '.sl2')

        def focus_message(self):
            self.txt_var.set('focus is currently to "' + self.reorganization_focus + '"')
            self.buttons[self.reorganization_focus]['style'] = 'FOCUS.TButton'

        def _move_save(self, indicator):
            if self.reorganization_focus:
                new_dict = dict()

                name = self.reorganization_focus
                str_number, without_number_name = name.split(' ', 1)
                number = int(str_number)
                new_number = number + indicator
                new_str_number = '{:0>{}}'.format(new_number, len(str_number))

                if len(self.buttons) + 1 > new_number > 0 :
                    for key, value in self.buttons.items():

                        str_number2, without_number_name2 = key.split(' ', 1)
                        if str_number2 == new_str_number:
                            new_name = f'{str_number2} {without_number_name}'
                            new_name2 = f'{str_number} {without_number_name2}'

                            new_dict[new_name] = self.buttons[name]
                            self.buttons[name]['command'] = self.define_callback(new_name)
                            self.buttons[name]['text'] = new_name
                            os.rename(self.saves_path + f'\\{name}.sl2', self.saves_path + f'\\{new_name}.sl2')

                            new_dict[new_name2] = value
                            value['command'] = self.define_callback(new_name2)
                            value['text'] = new_name2
                            os.rename(self.saves_path + f'\\{key}.sl2', self.saves_path + f'\\{new_name2}.sl2')

                        elif str_number2 != str_number:
                            new_dict[key] = value

                    self.reorganization_focus = new_name
                    self.buttons = new_dict
                    self.focus_message()
                    self.reinit_widgets()

        def move_save_up(self, _=None):
            self._move_save(-1)

        def move_save_down(self, _=None):
            self._move_save(1)

        def stop_reorganising(self, _=None):
            self.state = 'default'
            self.txt_var.set('')
            if self.reorganization_focus:
                self.buttons[self.reorganization_focus]['style'] = 'B.TButton'
                self.reorganization_focus = ''
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
            measuring, ref = self.adjust()

            i = 0
            for i, (key, button) in enumerate(self.buttons.items()):
                i += 1
                button['text'] = key + ((ref - measuring[key]) // self.root.car_width + 1) * ' '

                button.grid_forget()
                button.grid(column=0, row=i, sticky='w')

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
            self.buttons[name] = ttk.Button(self, text=name, command=self.define_callback(name), style='B.TButton')

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
            else:
                self.reinit_widgets()

        def _import_save(self, asname):
            copyfile(self.ds_path + '\\' + self.base_save_name + '.sl2', self.saves_path + f'\\{asname}.sl2')
        
        def switch_to(self, game):
            cfg = self.root.cfg
            cfg['Main']['game'] = game
            cfg['Main']['profile'] = 'no profile'
            with open('config.ini', 'w', encoding='utf8') as configfile:
                cfg.write(configfile)
            os.system('launcher.cmd')
            self.root.destroy()

if __name__ == "__main__":
    cfg = read_configs()
    root = App(cfg)
    if cfg['Main']['profile'] != 'no profile':
        root.create_profile_window()
    else:
        root.create_change_profile_menu()
    root.mainloop()
