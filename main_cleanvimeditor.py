#!/usr/bin/env python
# https://stackoverflow.com/questions/13207678/whats-the-simplest-way-of-detecting-keyboard-input-in-a-script-from-the-terminal

import re
import os
import sys
import time
import math
import signal
import threading
from select import select

on_linux = not ("win" in sys.platform)
if on_linux:
	import tty
	import fcntl
	import termios
	show_os_infos = True
	backlight_folder = "intel_backlight"  # for find this do ls /sys/class/backlight
	
else:
	show_os_infos = False 
	import ctypes
	import msvcrt

if on_linux:
	escape = {
		"\n": "enter",
		("\x7f", "\x08"): "backspace",
		("[A", "OA"): "up",
		("[B", "OB"): "down",
		("[D", "OD"): "left",
		("[C", "OC"): "right",
		"[2~": "insert",
		"[3~": "delete",
		"[H": "home",
		"[F": "end",
		"[5~": "page_up",
		"[6~": "page_down",
		"\t": "tab",
		"[Z": "shift_tab",
		"OP": "f1",
		"OQ": "f2",
		"OR": "f3",
		"OS": "f4",
		"[15": "f5",
		"[17": "f6",
		"[18": "f7",
		"[19": "f8",
		"[20": "f9",
		"[21": "f10",
		"[23": "f11",
		"[24": "f12"
	}
else:
	escape = {
		# lazy(flemme) do ctrl key
		"\r": "\n",
		"\x1b": "escape",
		"key3b": "f1",
		"key3c": "f2",
		"key3d": "f3",
		"key3e": "f4",
		"key3f": "f5",
		"key40": "f6",
		"key41": "f7",
		"key42": "f8",
		"key43": "f9",
		"key44": "f10",
		"key86": "f12",
		"key47": "\x1B[7~",
		"key4f": "\x1B[8~",
		"key52": "\x1B[2~",
		"key53": "\x1B[3~",
		"\x08": "\x7f",
		"key48": "\x1b[A",
		"key50": "\x1b[B",
		"key4d": "\x1b[C",
		"key4b": "\x1b[D",
	}

mouse_state = {
	# Changer le regex si supérieur a la key  \033[<100;: passer le {1,2} à {1,3}ou+
	# mouse_.._click
	"\033[<0;": "mouse_left_click",
	"\033[<1;": "mouse_middle_click",
	"\033[<2;": "mouse_right_click",
	# mouse_..alt_click
	"\033[<8;": "mouse_left_alt_click",
	"\033[<9;": "mouse_left_alt_click",
	"\033[<10;": "mouse_left_alt_click",
	# mouse_..ctrl_click
	"\033[<16;": "mouse_left_ctrl_click",
	"\033[<17;": "mouse_middle_ctrl_click",
	"\033[<18;": "mouse_right_ctrl_click",
	# mouse_..altctrl_click
	"\033[<24;": "mouse_left_ctrlalt_click",
	"\033[<25;": "mouse_middle_ctrlalt_click",
	"\033[<26;": "mouse_right_ctrlalt_click",
	# mouse_drag_.._click
	"\033[<32;": "mouse_drag_left_click",
	"\033[<33;": "mouse_drag_middle_click",
	"\033[<34;": "mouse_drad_right_click",
	# mouse_drag_..alt_click
	"\033[<40;": "mouse_left_alt_click",
	"\033[<41;": "mouse_left_alt_click",
	"\033[<42;": "mouse_left_alt_click",
	# mouse_drag_..ctrl_click
	"\033[<48;": "mouse_left_ctrl_click",
	"\033[<49;": "mouse_middle_ctrl_click",
	"\033[<50;": "mouse_right_ctrl_click",
	# mouse_drag_..ctrlalt_click
	"\033[<56;": "mouse_left_ctrlalt_click",
	"\033[<57;": "mouse_middle_ctrlalt_click",
	"\033[<58;": "mouse_right_ctrlalt_click",
	# mouse_scroll..
	"\033[<64;": "mouse_scroll_up",
	"\033[<65;": "mouse_scroll_down",
	# mouse_scroll_alt..
	"\033[<72;": "mouse_scroll_alt_up",
	"\033[<73;": "mouse_scroll_alt_down",
	# mouse_scroll_ctrl..
	"\033[<80;": "mouse_scroll_ctrl_up",
	"\033[<81;": "mouse_scroll_ctrl_down",
	# mouse_scroll_ctrlalt..
	"\033[<88;": "mouse_scroll_ctrl_up",
	"\033[<89;": "mouse_scroll_ctrl_down",
}

hide_cursor = "\033[?25l"  # * Hide terminal cursor
show_cursor = "\033[?25h"  # * Show terminal cursor
alt_screen = "\033[?1049h"  # * Switch to alternate screen
normal_screen = "\033[?1049l"  # * Switch to normal screen
clear = "\033[2J\033[0;0f"  # * Clear screen and set cursor to position 0,0
mouse_on = "\033[?1002h\033[?1015h\033[?1006h"  # * Enable reporting of mouse position on click and release
mouse_off = "\033[?1002l"  # * Disable mouse reporting
mouse_direct_on = "\033[?1003h"  # * Enable reporting of mouse position at any movement
mouse_direct_off = "\033[?1003l"  # * Disable direct mouse reporting


class Actions:
	# mouse_pos=mouse_pos,			 click_state=click_state, clean_key=clean_key			 ,input_save=input_save
	# Pos mouse type: (x, y), up or down			, key du type: escape ou mouse_..., key du type: \033[..
	dico_actions = {}

	@classmethod
	def set_action(cls):
		cls.dico_actions = {
			"m": cls.change_args,
			"c": cls.change_args,
			"t": cls.change_args,
			"i": cls.change_args,
			"a": cls.change_args,
			"v": cls.change_args,
			"s": cls.change_opts,
			"d": cls.change_opts,
			"f": cls.change_opts,
			"e": cls.export,
			"backspace": cls.delete,
			"q": cls.exit,
			"n": Infos.change_brightness,
		}

	@classmethod
	def export(cls, **kwargs):
		pass

	@classmethod
	def delete(cls, **kwargs):
		pass

	@classmethod
	def exit(cls, **kwargs):
		Infos.sig_quit(None, None)

	@classmethod
	def change_args(cls, **kwargs):
		change_data = Infos.dico_name_id[kwargs["clean_key"]]
		# Infos.sp_alpha 
		if Infos.sp_alpha & 2**change_data != 0:
			Infos.sp_alpha -= 2**change_data
		else:
			Infos.sp_alpha += 2**change_data
		Infos.reload()

	@classmethod
	def change_opts(cls, **kwargs):
		change_data = Infos.dico_opts_id[kwargs["clean_key"]]
		if Infos.opts_alpha & 2**change_data != 0:
			Infos.opts_alpha -= 2**change_data
		else:
			Infos.opts_alpha += 2**change_data
		Infos.info_footer()

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
		Infos.sig_quit(None, None)

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


if on_linux:
	class Raw(object):
		def __init__(self, stream):
			self.stream = stream
			self.fd = self.stream.fileno()

		def __enter__(self):
			self.original_stty = termios.tcgetattr(self.stream)
			tty.setcbreak(self.stream)

		def __exit__(self, type_, value, traceback):
			termios.tcsetattr(self.stream, termios.TCSANOW, self.original_stty)


	class Nonblocking(object):
		"""Set nonblocking mode for device"""

		def __init__(self, stream):
			self.stream = stream
			self.fd = self.stream.fileno()

		def __enter__(self):
			self.orig_fl = fcntl.fcntl(self.fd, fcntl.F_GETFL)
			fcntl.fcntl(self.fd, fcntl.F_SETFL, self.orig_fl | os.O_NONBLOCK)

		def __exit__(self, *args):
			fcntl.fcntl(self.fd, fcntl.F_SETFL, self.orig_fl)

hide_cursor = "\033[?25l"  # * Hide terminal cursor
show_cursor = "\033[?25h"  # * Show terminal cursor
alt_screen = "\033[?1049h"  # * Switch to alternate screen
normal_screen = "\033[?1049l"  # * Switch to normal screen
clear = "\033[2J\033[0;0f"  # * Clear screen and set cursor to position 0,0
mouse_on = "\033[?1002h\033[?1015h\033[?1006h"  # * Enable reporting of mouse position on click and release
mouse_off = "\033[?1002l"  # * Disable mouse reporting
mouse_direct_on = "\033[?1003h"  # * Enable reporting of mouse position at any movement
mouse_direct_off = "\033[?1003l"  # * Disable direct mouse reporting


class Box:
	def __init__(self, initial, name, width=30, height=20, min_width=30, min_height=30, max_width=100, max_height=100):
		self.initial = initial 
		self.name = name 
		self.x = 0
		self.y = 0
		self.width = width
		self.height = height
		self.min_width = min_width
		self.min_height = min_height
		self.max_width = max_width
		self.max_height = max_height
		self.visible = True
	def get_box_info():
		return (self.width)
	def __repr__(self):
		if self.visible:
			return f"<\033[33m{self.name}, {self.x}:{self.y}, {self.width}x{self.height}\033[0m>"
		return f"<\033[31m{self.name}, {self.x}:{self.y}, {self.width}x{self.height}\033[0m>"
		

class Infos:
	size = os.get_terminal_size()
	min_size = (30, 20)
	sp_alpha = 1+2+8+16 # 1 = M, 2=C, 4=T, 8=I, 16=A, 32=V
	#		  0 1 2 3 4  5
	opts_alpha = 1+2+4  # 1 = math, 2=Dark, 4=css

	sp_dico = {
		1: Box("M", "Matière"), 
		2: Box("C", "Cours"),
		4: Box("T", "Toc"), 
		8: Box("I", "Infos"), 
		16: Box("A", "Attributes"),
		32: Box("V", "Visual")
	}
	Mode = "Normal"
	dico_name_id = {
		"m": 0,
		"c": 1,
		"t": 2,
		"i": 3,
		"a": 4,
		"v": 5
	}
	dico_opts_id = {
		"s": 0,
		"d": 1,
		"f": 2
	}
	os_infos = {
		"battery": {},
		"sound": None,
		"luminosity": {},
	}
	@classmethod
	def actulise_os_infos(cls, key):
		if key=="battery":
			for i in ("capacity", "status", "type"):
				with open("/sys/class/power_supply/BAT0/"+i, "r") as f:
					cls.os_infos[key][i] = f.read().strip()
			print(cls.os_infos)
		elif key=="luminosity":
			for i in ("actual_brightness", "brightness", "max_brightness"):
				with open("/sys/class/backlight/"+backlight_folder+"/brightness", "r") as f:
					cls.os_infos[key][i] = f.read().strip()
			cls.os_infos[key]["luminosity"] = int(cls.os_infos[key]['brightness'])/int(cls.os_infos[key]['max_brightness'])
			print(cls.os_infos)
			
	@classmethod
	def change_brightness(cls, add=True, **_):
		# Is perm of root, donc ca marche pas
		try:
			with open("/sys/class/backlight/"+backlight_folder+"/brightness", "w") as f:
				pass
		except PermissionError:
			print(f"\033[1:{cls.size[1]}H")
			os.system("sudo chmod u+w /sys/class/backlight/"+backlight_folder+"/brightness")
		cls.actulise_os_infos("luminosity")

	# Is call at every time terminal is resized
	@classmethod
	def sig_resize_term(cls, s=None, f=None):
		cls.reload()

	@classmethod
	def sig_quit(cls, s, f):
		cls.clear()
		exit_event.set()
		print(show_cursor, mouse_off, mouse_direct_off)  # normal_screen
		print("Fin du programme vim editor")
		Key.stop()
		Draw.stop()
		try:
			exit(0)
		except:
			pass
		# raise SystemExit(0)
		#cls.clear()
		#exit(0)

	@classmethod
	def reload(cls):
		cls.size = os.get_terminal_size()
		cls.clear()
		cls.footer()
		cls.view()

	@classmethod
	def footer(cls):
		print(f"\033[{cls.size[1]-1};1H\033[47m{' '*int(cls.size[0])}\033[0m")
		cls.info_footer()

	@classmethod
	def info_footer(cls):
		alpha_repr = ""
		for i in range(6):
			if cls.sp_alpha & 2**i != 0:
				alpha_repr += cls.sp_dico[2**i].initial
			else:
				alpha_repr += "-"
		sys.stdout.write(f"\033[{cls.size[1]-1};{3}H\033[47m\033[30m{alpha_repr}\033[0m")
		print("\033[1;1H")

		cls.info_opts()

	@classmethod
	def info_opts(cls):
		alpha_repr = ""
		for i in cls.dico_opts_id.keys():
			if cls.opts_alpha & 2**cls.dico_opts_id[i] != 0:
				alpha_repr += i 
			else:
				alpha_repr += "-"
		sys.stdout.write(f"\033[{cls.size[1]-1};{12}H\033[47m\033[30m{alpha_repr}\033[0m")
		print("\033[1;1H")
		if show_os_infos: 
			cls.actulise_os_infos("battery")
			cls.actulise_os_infos("luminosity")

	@classmethod
	def set_data(cls,id , x,y,width, height): # TODO
		cls.sp_dico[id].x = x
		cls.sp_dico[id].y = y
		cls.sp_dico[id].width = width
		cls.sp_dico[id].height = height 

	@classmethod
	def box_app(cls, id):
		if id==0:
			pass
		elif id==1:
		    pass
		elif id==2:
		    pass
		elif id==3:
		    pass
		elif id==4:
		    pass
		elif id==5:
		    pass

	@classmethod
	def view(cls):
		# ------------------ vsp and hsp
		vertical_windows = 0  #  | | 
		horizontal_windows = 0  # -_
		for i in range(0,2):  # Si box 0 ou 1 est visible 
			if cls.sp_alpha & 2**i != 0:
				vertical_windows += 1

		if cls.sp_alpha/3 > 1.0:  # Si une des box [2-5] ext visible
			vertical_windows +=1
			if cls.sp_alpha & 2**5:  # Si box 5 est visible
				horizontal_windows = 1
			else:
				for i in range(2, 5):
					if cls.sp_alpha & 2**i:  # Si box [2-4] est visible
						horizontal_windows += 1
		# ------------------ Taille des Box
		hsp = 0
		vsp = 0
		for i in range(0,6):  # Pour toutes les box
			if cls.sp_alpha & 2**i != 0: #  Si elle est visible
				if i==0 or i==1 or i==5: # Si elle est verticale
						width = cls.size[0]//(vertical_windows if vertical_windows != 0 else 1)
						height = cls.size[1]
						cls.set_data(2**i,cls.size[0]//vertical_windows*vsp+1,1,width, height)
						vsp += 1
				else : #  Si elle est hozizonsaatallle
						if cls.sp_alpha & 2**5 == 0: #  Si 5 est visible alors rien 
								width = cls.size[0]//(vertical_windows if vertical_windows != 0 else 1)
								height = cls.size[1]//(horizontal_windows if horizontal_windows != 0 else 1)
								cls.set_data(2**i,cls.size[0]//vertical_windows*vsp+1,cls.size[1]//horizontal_windows*hsp+1,width, height)
						hsp+=1
		# ------------------------ show name
		for i in range(0, 5): # On affiche pas le nom de La box 5 pour avoir plus de place
			if cls.sp_alpha & 2**i != 0: #  Si elle est visible
				if (i==2 or i==3 or i==4):
					if cls.sp_alpha & 2**5 == 0: #  Si elle est visible
						c_box = cls.sp_dico[2**i]
						sys.stdout.write(f"\033[{c_box.y+1};{c_box.x+2}H{c_box.name}")
				else:
					c_box = cls.sp_dico[2**i]
					sys.stdout.write(f"\033[{c_box.y+1};{c_box.x+2}H{c_box.name}")
		print("\033[1;1H")
		# ------------------------ action de la box 
		for i in range(0, 6):
		    cls.box_app(i)
			
		# ------------------------ view 
		for border in range(1,vertical_windows):
			for i in range(cls.size[1]-1): # Pour tout la hauteur
				sys.stdout.write(f"\033[{i};{cls.size[0]//vertical_windows*border}H\033[47m\033[30m|\033[0m")
		for border in range(1,horizontal_windows):
			for i in range(cls.size[0]//vertical_windows*(vertical_windows-1)+1,cls.size[0]+1): # For longeur
				sys.stdout.write(f"\033[{cls.size[1]//horizontal_windows*border};{i}H\033[47m\033[30m-\033[0m")
		# ------------------------ Message en bas derni}re ligne
		sys.stdout.write(f"\033[{cls.size[1]};1HBox : {str(cls.sp_dico)}")
		print("\033[1;1H")

	@classmethod
	def clear(cls):
		sys.stdout.write("\033[2J\033[1;1H")

def main():
	global exit_event
	exit_event = threading.Event()

	if on_linux:
		# Signals Events
		signal.signal(signal.SIGINT, Infos.sig_quit)
		# SIGNAL Resize terminal
		signal.signal(signal.SIGWINCH, Infos.sig_resize_term)
	# Define Initial Actions:
	Actions.set_action()
	if on_linux:  # No mouse terminal on windows :(
		# Set config
		print(mouse_on)

	# Start Program
	def run():
		Infos.reload()
		Key.start()
		Draw.start()

	run()

if __name__ == '__main__':
	if "--debug" in sys.argv:
		debug = True
	else:
		debug = False
	main()
