#!/usr/bin/env python3

import subprocess
import sys
import re
from resource_vimeditor import *


def main():
    math = False
    dark = False
    if "--math" in sys.argv:
        math = True
    if "--dark" in sys.argv:
        dark = True
    if len(sys.argv) > 1:
        argv = sys.argv[1]
    else:
        return
    with open(re.match("(.*)\.md",sys.argv[1]).group(1)+".html", "w") as f:
        f.write(multi_markdown(argv, math, dark))


"""
if __name__ == "__main__":
    main()
"""



import sys
import os
import signal
import threading
import time
from select import select
import re
import json

on_linux = not ("win" in sys.platform)
if on_linux:
    import fcntl
    import termios
    import tty
else:
    import ctypes
    import msvcrt


class Actions:
    # mouse_pos=mouse_pos,             click_state=click_state, clean_key=clean_key             ,input_save=input_save
    # Pos mouse type: (x, y), up or down            , key du type: escape ou mouse_..., key du type: \033[..
    dico_actions = {}
    @classmethod
    def set_action(cls):
        cls.dico_actions = {
            "z": cls.avancer,
            "mouse_left_click": cls.left_click
        }

    @classmethod
    def avancer(cls, **kwargs):
        Draw.x += 1
        print("avancer")

    @classmethod
    def left_click(cls, **kwargs):
        if cls.pos_in_square(kwargs["mouse_pos"], 15, 15, 20, 20):
            print("click inside 15,15,20,20")
        if cls.pos_in_circle(kwargs["mouse_pos"], 20, 50, 10):
            print("click circle 20,50")

    @classmethod
    def pos_in_square(cls, mouse_pos: tuple[int, int], x1: int, y1: int, x2: int, y2: int) -> bool:
        # Verifies si mouse_pos(tuple: (int, int)) est dans le rectangle x1, y1, x2, y2
        return x1 <= mouse_pos[0] < x2 and y1 <= mouse_pos[0] < y2

    @classmethod
    def pos_in_circle(cls, mouse_pos: tuple[int, int], x1: int, y1: int, rayon: int) -> bool:
        return (x1 - mouse_pos[0]) ** 2 + (y1 - mouse_pos[1]) ** 2 < rayon ** 2

    @classmethod
    def pos_in_pos(cls, mouse_pos: tuple[int, int], x1: int, y1: int) -> bool:
        return (x1 == mouse_pos[0]) and (y1 == mouse_pos[1])


class Key:
    mouse_pos = None
    list = None
    stopping: bool = False
    started: bool = False
    reader: threading.Thread

    @classmethod
    def start(cls):
        cls.stopping = False
        if on_linux:
            cls.reader = threading.Thread(target=cls._get_key)
        else:
            cls.reader = threading.Thread(target=cls._win_get_key)
        cls.reader.start()
        cls.started = True

    @classmethod
    def stop(cls):
        if cls.started and cls.reader.is_alive():
            cls.stopping = True
            try:
                cls.reader.join()
            except RuntimeError:
                pass

    @classmethod
    def last(cls) -> str:
        if cls.list:
            return cls.list.pop()
        else:
            return ""

    @classmethod
    def get(cls) -> str:
        if cls.list:
            return cls.list.pop(0)
        else:
            return ""

    @classmethod
    def get_mouse(cls):
        return cls.mouse_pos

    @classmethod
    def has_key(cls) -> bool:
        return bool(cls.list)

    @classmethod
    def clear(cls):
        cls.list = []

    @classmethod
    def _get_key(cls):
        input_key = ""
        mouse_pos = None
        while not cls.stopping:
            with Raw(sys.stdin):
                if exit_event.is_set():
                    break
                if not select([sys.stdin], [], [], 0.1)[0]:
                    continue
                input_key += sys.stdin.read(1)
                if input_key == "\033":
                    with Nonblocking(sys.stdin):
                        input_key += sys.stdin.read(20)
                        if input_key.startswith("\033[<"):
                            _ = sys.stdin.read(1000)
                click_state = ""
                if input_key == "\033":
                    clean_key = "escape"
                elif not re.search("\x1b\[<[0-9]{1,2};", input_key) is None:
                    # With some terminals it possible to drag out of terminal, they setup negative number, do careful with that: can ["urxvt"], dont update out ["kitty"], update but not negative out of size ["xterm"]
                    escape_element = re.search("\x1b\[<[0-9]{1,2};", input_key).group(0)
                    if escape_element in mouse_state.keys() and \
                            not re.search("\x1b\[<[0-9]{1,2};-?[0-9]+;-?[0-9]+[mM]", input_key) is None:
                        regex = re.search('\x1b\[<[0-9]{1,2};(-?[0-9]+);(-?[0-9]+)([mM])', input_key)
                        mouse_pos = (int(regex.group(1)), int(regex.group(2)))
                        click_state = {"m": "up", "M": "down"}[regex.group(3)]
                    clean_key = mouse_state[escape_element]
                elif input_key == "\\":
                    clean_key = "\\"
                else:
                    clean_key = input_key
                input_save = input_key
                input_key = ""

            if clean_key in Actions.dico_actions.keys():
                if mouse_pos is not None:  # Si c'est une action souris
                    Actions.dico_actions[clean_key](mouse_pos=mouse_pos, click_state=click_state,
                                                    clean_key=clean_key, input_save=input_save)
                else:
                    Actions.dico_actions[clean_key](clean_key=clean_key, input_save=input_save)
            if debug:
                print(f"{clean_key=},\t {mouse_pos=},\t {click_state=},\t {input_save=}")
        clean_quit()

    @classmethod
    def _win_get_key(cls):

        def getch():
            n = ord(ctypes.c_char(msvcrt.getch()).value)
            try:
                c = chr(n)
            except:
                c = '\0'
            return n, c

        def getkey():
            n, c = getch()
            # 0xE0 is 'grey' keys.  change this if you don't like it, but I don't care what color the key is.  IMHO it just confuses the end-user if they need to know.
            if n == 0 or n == 0xE0:
                n, c = getch()
                return "key%x" % n
            return c

        while not cls.stopping:
            if exit_event.is_set():
                break
            key = getkey()
            input_save = key
            if key in escape.keys():
                key = escape[key]
            if key == "\x03":
                sigint_quit(0, None)
            if key in Actions.dico_actions.keys():
                Actions.dico_actions[key](clean_key=key, input_save=input_save)
            if debug:
                print(f"{key=}, {input_save=}")


class Draw:
    x: int = 0

    @classmethod
    def _do_draw(cls):
        while not cls.stopping:
            if exit_event.is_set():
                break
            # SET CODE HERE: ne pas metre de code bloquant: code qui nécessite une action de l'utilisateur
            print("Hello")
            time.sleep(1)

    # ---------------------------------------
    stopping: bool = False
    started: bool = False
    reader: threading.Thread

    @classmethod
    def start(cls):
        cls.stopping = False
        cls.reader = threading.Thread(target=cls._do_draw)
        cls.reader.start()
        cls.started = True

    @classmethod
    def stop(cls):
        if cls.started and cls.reader.is_alive():
            cls.stopping = True
            try:
                cls.reader.join()
            except RuntimeError:
                pass


def sigint_quit(s, f):
    exit_event.set()


def clean_quit(errcode: int = 0):
    exit_event.set()
    print(show_cursor, mouse_off, mouse_direct_off)  # normal_screen
    print("Fin du programme")
    Key.stop()
    Draw.stop()
    raise SystemExit(errcode)


# config
mouse = True

class Info():
    def __init__(self, folder, match=".*"):
        for root, directories, files in os.walk(folder, topdown=False):
            for name in files:
                if re.search(match, name):
                    print(os.path.join(root, name))


def main():
    # https://blog.miguelgrinberg.com/post/how-to-kill-a-python-thread
    global exit_event
    exit_event = threading.Event()

    if on_linux:
        # Signals Events
        signal.signal(signal.SIGINT, sigint_quit)
    # Define Initial Actions:
    Actions.set_action()
    if on_linux:  # No mouse terminal on windows :(
        # Set config
        if mouse:
            print(mouse_on)

    # Start Program
    def run():
        Key.start()
        Draw.start()

    run()


if __name__ == "__main__":
    if "--debug" in sys.argv:
        debug = True
    else:
        debug = False

    # main()
    Info(sys.argv[1])
