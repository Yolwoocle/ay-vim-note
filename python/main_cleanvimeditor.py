#!/usr/bin/env python
# https://stackoverflow.com/questions/13207678/whats-the-simplest-way-of-detecting-keyboard-input-in-a-script-from-the-terminal

import os
import subprocess
import time
import re
import signal
import sys
import threading
from select import select

on_linux = "win" not in sys.platform
if on_linux:
	import tty
	import fcntl
	import termios

	
	show_os_infos = True
	backlight_folder = "intel_backlight"  # for find this, do ls /sys/class/backlight
else:
	show_os_infos = False
	import ctypes
	import msvcrt

def split_line(ligne):
	liste = []
	width = Infos.sp_dico[2**5].width 
	if len(ligne) > width:
		liste += [ligne[:width]] + split_line(ligne[width:])
	else:
		liste += [ligne]
	return liste
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
	# Changer le regex si supérieur a la key \033[<100;: passer le {1,2} à {1,3}ou+
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
	# mouse_scroll..
	"\033[<66;": "mouse_scroll_left",
	"\033[<67;": "mouse_scroll_right",
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
	# mouse_pos=mouse_pos,	click_state=click_state, clean_key=clean_key			 ,input_save=input_save
	# Pos mouse type: (x, y), up or down			 , key du type: escape ou mouse_..., key du type: \033[..
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
			"E": cls.export_all,
			"g": cls.colapse,
			"\x1b[3;2~": cls.delete,  # Shift+Backspace
			"q": cls.exit,
			# "n": Infos.change_brightness,
			"\x1b[A": cls.arrow,
			"k": cls.arrow,
			"\x1b[B": cls.arrow,
			"j": cls.arrow,
			"\x1b[C": cls.arrow,
			"l": cls.arrow,
			"\x1b[D": cls.arrow,
			"h": cls.arrow,
			"\n": cls.open_vim,
			"\x1bOQ": cls.rename,  # F2
			"M": cls.new_doc,
			"I": cls.new_doc,
			"C": cls.new_doc,
			"F": cls.new_doc
		}

	@classmethod
	def new_doc(cls, new_doc=None, **kwargs):
		key = kwargs["clean_key"]
		name = {"M": "Matière", "I": "Intercalaire", "C": f"Cours in {Infos.cours_index} TODO", "F": f"Cours.file in {Infos.cours_index} TODO"}[key]
		# On autorise les point si on choisit les extention
		new_doc_regex = "[^A-Za-z0-9_à-öÀ-Ö]" if not key=="F" else "[^A-Za-z0-9_à-öÀ-Ö.]"
		if new_doc is None:
			new_doc = re.sub(new_doc_regex, "", Infos.write_message("Nouveau " + name, True))
		if new_doc == "Intro":
			raise FileExistsError("Imposible de nomer un fichier/dossier 'Intro'")
		if key == "M":
			if new_doc in Infos.data_path.keys():
				raise FileExistsError(f"'{new_doc}' already exists")
			os.mkdir(Infos.path + "/notes/" + new_doc)
			os.mkdir(Infos.path + "/notes/" + new_doc + "/0.Intro")
		elif key == "I":
			# Crée le dossier 0.Infos et recload comman avec l'argumet new_doc
			if len(Infos.data_path[Infos.matiere_index].keys()) == 0:  
				os.mkdir(Infos.path + "/notes/" + Infos.matiere_index + "/0.Intro")
				Infos.load_data()
				cls.new_doc(new_doc=new_doc, clean_key="I")
				return
			if new_doc in [re.sub("^[0-9.]+", "", i) for i in Infos.data_path[Infos.matiere_index].keys()]:
				raise FileExistsError(f"'{new_doc}' already exists in {Infos.matiere_index}")
			os.mkdir(Infos.path + "/notes/" + Infos.matiere_index + "/" + str(
				len(Infos.data_path[Infos.matiere_index].keys())) + "." + new_doc)
		elif key == "C" or key == "F":
			if Infos.inter_index is None:
				inter_dico = Infos.data_path[Infos.matiere_index][Infos.cours_index]
				inter_name = Infos.cours_index
			else:
				inter_dico = Infos.data_path[Infos.matiere_index][Infos.inter_index]
				inter_name = Infos.inter_index
			nb_file_in_inter = len(inter_dico[1:])  # [1:] est pour enlever le bool au debut qui montre le visible
			match = re.match("^[0-9]*", inter_name)
			if match is not None:
				inter_number = match.group(0)
			gen_path = Infos.generate_path()
			# TODO verifier si il exsiste le chemin exsiste
			if key=="C":
				if gen_path[3]:
					with open(gen_path[4]+"/"+str(inter_number)+"."+str(nb_file_in_inter)+"."+new_doc+".md", "w") as f:
						f.write("# "+new_doc)
			else:  # key = F
				if gen_path[3]:
					with open(gen_path[4]+"/"+str(inter_number)+"."+str(nb_file_in_inter)+"."+new_doc, "w") as f:
						f.write("")
		else:
			raise NotImplementedError("Vous êtes pas censé avoir une autre key qui M,I,C pour lancer new_doc")
		Infos.load_data()
		Infos.reload()

	@classmethod
	def rename(cls, **_):
		gen_path = Infos.generate_path()
		if not (gen_path[1] or gen_path[2]):
			return "Vous pouvez pas rename un fichier non indexer"
		# file_name = gen_path[0].split("/")[-1]
		match = re.search("(.+)/([0-9.]+)\\.(.+)", gen_path[0])
		if match is not None:
			new_name = Infos.write_message(f"Rename {match.group(3)}", True)
			# raise Exception(f"{gen_path[0]} to {match.group(1)+'/'+match.group(2)+'.'+new_name}")
			new_path = match.group(1) + '/' + match.group(2) + '.' + new_name
			os.rename(gen_path[0], new_path)
			Infos.cours_index = match.group(2) + '.' + new_name
			Infos.load_data()
			Infos.box_app(1)

	@classmethod
	def colapse(cls, **_):
		gen_path = Infos.generate_path()
		if gen_path[1]:  # C'est un Fichier
			matiere_index = Infos.data_path[Infos.matiere_index]
			matiere_index[Infos.inter_index][0] = not matiere_index[Infos.inter_index][0]
			Infos.cours_index = Infos.inter_index
		elif gen_path[2]:  # C'est un Dossier
			matiere_index = Infos.data_path[Infos.matiere_index]
			matiere_index[Infos.cours_index][0] = not matiere_index[Infos.cours_index][0]
		else:
			pass
		Infos.box_app(1)
		Infos.write_message(
			f"Box : {str(Infos.data_path) + str(Infos.cours_index) + str(Infos.inter_index)}")
		pass

	@classmethod
	def open_vim(cls, **_):
		gen_path = Infos.generate_path()
		if gen_path[1]:
			Infos.vim_is_launched = True
			os.system(Infos.editor + " " + gen_path[0])
			Infos.vim_is_launched = False
			Infos.reload()

	@classmethod
	def arrow(cls, **kwargs):
		key = kwargs["clean_key"]
		action = None
		if key == "\x1b[A" or key == "k":
			action = "Up"
		if key == "\x1b[B" or key == "j":
			action = "Down"
		if key == "\x1b[D" or key == "h":
			action = "Left"
			Infos.change_current_page(False)
		if key == "\x1b[C" or key == "l":
			action = "Right"
			Infos.change_current_page()
		if Infos.current_page == 0:  # Sur la Page Matiere
			matieres = list(Infos.data_path.keys())
			current_matiere_index = matieres.index(Infos.matiere_index)
			if action == "Up":
				Infos.matiere_index = matieres[current_matiere_index - 1]
			if action == "Down":
				Infos.matiere_index = matieres[(current_matiere_index + 1) % len(matieres)]
			Infos.box_app(0)
		if Infos.current_page == 1:  # Sur la Page Cours
			if action in ("Up", "Down"):
				if len(Infos.tmp_list) != 0:
					new_index = ""
					item_index = -1
					for index, i in enumerate(Infos.tmp_list):
						if re.search("\x1b\\[33m", i) is not None:
							item_index = index
							break
					if action == "Up":
						new_index = (item_index - 1) % len(Infos.tmp_list)
					if action == "Down":
						new_index = (item_index + 1) % len(Infos.tmp_list)
					Infos.cours_index = re.sub(f"^({Infos.icons['folder_open']}\\s|{Infos.icons['folder_close']}\\s|\\s\\s[-{Infos.icons['no_file']}{Infos.all_file_type}]\\s)", "", Infos.tmp_list[new_index], 1)
			Infos.box_app(1)
			Infos.box_app(5)

	@classmethod
	def export_all(cls, **kwargs):
		all_matiere_path = []
		for matiere in Infos.data_path.keys():
			html_file = '<meta charset="UTF-8">'
			# tmp_data_matiere = {}
			for inter in Infos.data_path[matiere].keys():
				html_file += f"<h1>{inter}</h1>\n<details>\n"
				# tmp_data_matiere[inter] = {}
				for cours in Infos.data_path[matiere][inter][1:]:
					html_file += f"<p><a href=\"{matiere}/{inter}/{cours}.html\">{cours}</a></p>\n"
					file_data = cls.create_html_file(matiere, inter, cours)
					# tmp_data_matiere[inter][cours] = ["# TOC", "## TOCTOC", "#QUIEST"] # Make TOC
				html_file += "</details>\n"
			with open(Infos.path+"/html/"+matiere+".html", "w") as f:
				"""
				html_file = ""
				for inter in tmp_data_matiere.keys():
					html_file +=
				"""
				f.write(str(html_file))
			all_matiere_path += [(Infos.path+"/html/"+matiere+".html", matiere)]

		with open(Infos.path+"/index.html", "w") as f:
			index_data = '<meta charset="UTF-8">'
			for matiere_path, matiere in all_matiere_path:
				index_data += f"<h1><a href=\"{matiere_path}\">{matiere}</a></h1>"
			f.write(index_data)
	"""
cls.toc_data = []
for i in cls.file_data.split("\n"):
	tmp_match = re.match("(#{1,6})\\s(.+)", i)
	if tmp_match is not None:
		cls.toc_data += [(len(tmp_match.group(1)), tmp_match.group(2))]
	"""
	

	@classmethod
	def export(cls, where_export=None, **kwargs):
		return
			
	@classmethod
	def create_matiere_html(cls, matiere):
		if not os.path.isfile(Infos.path+"/notes/"+matiere):
			raise FileNotFoundError("DirNotFound")

	@classmethod
	def create_html_file(cls, matiere, inter, cours):
		gen_path = Infos.generate_path()
		if not os.path.isfile(Infos.path+"/notes/"+matiere+"/"+inter+"/"+cours):# Si c'est un fichier export dans html
			raise FileNotFoundError("ThisNotFound")
		# Si le dossier n'exsitste pas tu le crée
		if not os.path.isdir(Infos.path + "/html/" + matiere+"/"+inter): 
			os.makedirs(Infos.path + "/html/" + matiere+"/"+inter)
		if not os.path.isdir(Infos.path + "/html/" + matiere+"/"+inter):
			raise FileNotFoundError("Le dossier html/matiere n'exsiste pas et n'est pas créable")
		else:
			html_inter_path = (Infos.path + "/html/" + matiere+"/"+inter)
		with open(html_inter_path+"/"+cours+".html", "w") as f:
			f.write(multi_markdown(Infos.path+"/notes/"+matiere+"/"+inter+"/"+cours , True, True))
		

	@classmethod
	def delete(cls, **kwargs):
		pass

	@classmethod
	def exit(cls, **_):
		Infos.sig_quit(None, None)

	@classmethod
	def change_args(cls, **kwargs):
		change_data = Infos.dico_name_id[kwargs["clean_key"]]
		# Infos.sp_alpha
		if Infos.sp_alpha & 2 ** change_data != 0:
			Infos.sp_alpha -= 2 ** change_data
		else:
			Infos.sp_alpha += 2 ** change_data
		Infos.change_current_page(verifie=True)
		Infos.reload()

	@classmethod
	def change_opts(cls, **kwargs):
		change_data = Infos.dico_opts_id[kwargs["clean_key"]]
		if Infos.opts_alpha & 2 ** change_data != 0:
			Infos.opts_alpha -= 2 ** change_data
		else:
			Infos.opts_alpha += 2 ** change_data
			Infos.box_app(change_data)
		Infos.info_footer()

	@classmethod
	def left_click(cls, **kwargs):
		if cls.pos_in_square(kwargs["mouse_pos"], 15, 15, 20, 20):
			print("click inside 15,15,20,20")
		if cls.pos_in_circle(kwargs["mouse_pos"], 20, 50, 10):
			print("click circle 20,50")

	@classmethod
	def pos_in_square(cls, mouse_pos: tuple[int, int], x1: int, y1: int, x2: int, y2: int):
		# Verifies si mouse_pos(tuple: (int, int)) est dans le rectangle x1, y1, x2, y2
		return x1 <= mouse_pos[0] < x2 and y1 <= mouse_pos[0] < y2

	@classmethod
	def pos_in_circle(cls, mouse_pos, x1, y1, rayon):
		return (x1 - mouse_pos[0]) ** 2 + (y1 - mouse_pos[1]) ** 2 < rayon ** 2

	@classmethod
	def pos_in_pos(cls, mouse_pos, x1, y1):
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
				print("Warning: RuntimeError, pas de quoi être affolé")

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
			if Infos.vim_is_launched:
				continue
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
				elif not re.search("\x1b\\[<[0-9]{1,2};", input_key) is None:
					# With some terminals is possible to drag out of terminal, they set a negative number, do careful with that: can ["urxvt"], don't update out ["kitty"], update but not negative out of size ["xterm"]
					escape_element = re.search("\x1b\\[<[0-9]{1,2};", input_key).group(0)
					if escape_element in mouse_state.keys() and \
							not re.search("\x1b\\[<[0-9]{1,2};-?[0-9]+;-?[0-9]+[mM]", input_key) is None:
						regex = re.search('\x1b\\[<[0-9]{1,2};(-?[0-9]+);(-?[0-9]+)([mM])', input_key)
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
					Actions.dico_actions[clean_key](mouse_pos=mouse_pos, click_state=click_state, clean_key=clean_key,
													input_save=input_save)
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
				Infos.sig_quit(0, None)
			if key in Actions.dico_actions.keys():
				Actions.dico_actions[key](clean_key=key, input_save=input_save)
			if debug:
				print(f"{key=}, {input_save=}")


class Draw:
	x: int = 0

	@classmethod
	def _do_draw(cls):
		return # It's useless for now
		while not cls.stopping:
			time.sleep(5)
			if exit_event.is_set():
				break
			if Infos.vim_is_launched:
				pass
			else:
				pass
			# Infos.write_message(f"Box : {str(Infos.data_path) + '	'}")

	# SET23		 print(mouse_on) CODE HERE: ne pas metre de code bloquant: code qui nécessite une action de l'utilisateur

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

HIDE_CURSOR = "\033[?25l"  # * Hide terminal cursor
SHOW_CURSOR = "\033[?25h"  # * Show terminal cursor
ALT_SCREEN = "\033[?1049h"  # * Switch to alternate screen
NORMAL_SCREEN = "\033[?1049l"  # * Switch to normal screen
CLEAR = "\033[2J\033[0;0f"  # * Clear screen and set cursor to position 0,0
MOUSE_ON = "\033[?1002h\033[?1015h\033[?1006h"  # * Enable reporting of mouse position on click and release
MOUSE_OFF = "\033[?1002l"  # * Disable mouse reporting
MOUSE_DIRECT_ON = "\033[?1003h"  # * Enable reporting of mouse position at any movement
MOUSE_DIRECT_OFF = "\033[?1003l"  # * Disable direct mouse reporting


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

	def get_box_info(self):
		return self.width

	def __repr__(self):
		if self.visible:
			return f"<\033[33m{self.name}, {self.x}:{self.y}, {self.width}x{self.height}\033[0m>"
		return f"<\033[31m{self.name}, {self.x}:{self.y}, {self.width}x{self.height}\033[0m>"


class Infos:
	vim_is_launched = False
	size = os.get_terminal_size()
	min_size = (30, 20)
	sp_alpha = 1 + 2 + 4 + 8 + 16  # 1 = M, 2=C, 4=T, 8=I, 16=A, 32=V
	#		  0 1 2 3 4  5
	opts_alpha = 1 + 2 + 4  # 1 = math, 2=Dark, 4=css
	current_page = 0
	path = None
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
	data_path = {}
	matiere_index = "Nsi"  # TODO
	inter_index = "0.Intro"
	cours_index = "0.0.Intro"
	tmp_list = []
	toc_position = 0
	toc_data = []  # Liste de tuples (1-6, "Titre")
	infos_data = {"Mots": None, "Char": None, "Line": None, "Type": "File"}
	file_data = ""
	editor = "vim"  # Choisir un editeur qui se lance avec le terminal
	nerd_fonts = True 
	if nerd_fonts:
		ext_file_icons = {
			".md": "\uf48a"
		}
		all_file_type = "".join(ext_file_icons.values())
	else:
		ext_file_icons = {}
		all_file_type = ""
	icons = {
		"folder_close": "\uf07b" if nerd_fonts else ">",
		"folder_open": "\uf07c" if nerd_fonts else "v",
		"no_file": "\ue612" if nerd_fonts else "-",
	}

	@classmethod
	def change_current_page(cls, positive=True, verifie=False):
		if verifie and cls.sp_alpha & 2 ** cls.current_page != 0:  # Si la page sclectioner est visible
			return
		if cls.sp_alpha & 2 ** 5 != 0 and cls.current_page != 5:  # Si la page 5 est visible et que elle n'est selectioner
			if positive and cls.current_page == 0:
				cls.current_page += 1
			elif not positive and cls.current_page == 1:
				cls.current_page -= 1
			else:
				cls.current_page = 5
		else:
			if positive:
				for i in [(i + cls.current_page) % 5 for i in range(1, 6)]:
					if cls.sp_alpha & 2 ** i != 0:
						cls.current_page = i
						break
			else:
				for i in [(i + cls.current_page) % 5 for i in range(4, -1, -1)]:
					if cls.sp_alpha & 2 ** i != 0:
						cls.current_page = i
						break
		cls.show_name()

	@classmethod
	def actulise_os_infos(cls, key):
		if key == "battery":
			for i in ("capacity", "status", "type"):
				with open("/sys/class/power_supply/BAT0/" + i, "r") as f:
					cls.os_infos[key][i] = f.read().strip()
			print(cls.os_infos)
		elif key == "luminosity":
			for i in ("actual_brightness", "brightness", "max_brightness"):
				with open("/sys/class/backlight/" + backlight_folder + "/brightness", "r") as f:
					cls.os_infos[key][i] = f.read().strip()
			cls.os_infos[key]["luminosity"] = int(cls.os_infos[key]['brightness']) / int(
				cls.os_infos[key]['max_brightness'])
			print(cls.os_infos)

	@classmethod
	def change_brightness(cls, add=True, **_):
		# Is perm of root, donc ca marche pas
		try:
			with open("/sys/class/backlight/" + backlight_folder + "/brightness", "w") as f:
				pass
		except PermissionError:
			print(f"\033[1:{cls.size[1]}H")
			os.system("sudo chmod u+w /sys/class/backlight/" + backlight_folder + "/brightness")
		cls.actulise_os_infos("luminosity")

	# Is call at every time terminal is resized
	@classmethod
	def sig_resize_term(cls, _=None, __=None):
		if cls.vim_is_launched:
			cls.size = os.get_terminal_size()
		else:
			cls.reload()

	@classmethod
	def sig_quit(cls, _, __):
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
	# cls.clear()
	# exit(0)

	@classmethod
	def generate_path(cls):
		# Return le chemin, si c'est un fichier, si c'est un dossier, si c'est un folder
		if cls.inter_index is None:
			path = cls.path + "/notes/" + cls.matiere_index + "/" + cls.cours_index
			inter = cls.path + "/notes/" + cls.matiere_index + "/" + cls.cours_index
		else:
			path = cls.path + "/notes/" + cls.matiere_index + "/" + str(cls.inter_index) + "/" + cls.cours_index
			inter = cls.path + "/notes/" + cls.matiere_index + "/" + str(cls.inter_index) 
		is_file, is_dir = os.path.isfile(path), os.path.isdir(path), 
		return path, is_file, is_dir, (is_file or is_dir), inter

	@classmethod
	def generate_infos(cls, toc=True, infos=True, visual=True):
		gen_path = cls.generate_path()
		path = gen_path[0]
		if gen_path[1]:
			with open(path, "r") as f:
				cls.file_data = f.read()
			if toc:
				cls.toc_data = []
				for i in cls.file_data.split("\n"):
					tmp_match = re.match("(#{1,6})\\s(.+)", i)
					if tmp_match is not None:
						cls.toc_data += [(len(tmp_match.group(1)), tmp_match.group(2))]

			if infos:
				cls.infos_data = {"Path": cls.matiere_index + "/" + str(cls.inter_index) + "/" + cls.cours_index,
								  "Name": cls.cours_index, "Mots": len(cls.file_data.split()),
								  "Char": len(cls.file_data), "Line": len(re.findall("\n", cls.file_data)),
								  "Type": "File"}
			if visual:
				pass
		elif gen_path[2]:
			if toc:
				cls.toc_data = "Folder"
			if infos:
				cls.infos_data = {"Path": cls.matiere_index + "/" + cls.cours_index,
								  "Fold": Infos.data_path[Infos.matiere_index][Infos.cours_index][0],
								  "Name": cls.cours_index, "Type": "Folder"}
		else:
			if toc:
				cls.toc_data = "Undefined"
			cls.infos_data = {"Type": "Undefined"}

	@classmethod
	def reload(cls):
		cls.size = os.get_terminal_size()
		cls.clear()
		cls.footer()
		cls.view()

	@classmethod
	def footer(cls):
		print(f"\033[{cls.size[1] - 1};1H\033[47m{' ' * int(cls.size[0])}\033[0m")
		cls.info_footer()

	@classmethod
	def info_footer(cls):
		alpha_repr = ""
		for i in range(6):
			if cls.sp_alpha & 2 ** i != 0:
				alpha_repr += cls.sp_dico[2 ** i].initial
			else:
				alpha_repr += "-"
		sys.stdout.write(f"\033[{cls.size[1] - 1};{3}H\033[47m\033[30m{alpha_repr}\033[0m")
		print("\033[1;1H")
		cls.info_opts()

	@classmethod
	def info_opts(cls):
		alpha_repr = ""
		for i in cls.dico_opts_id.keys():
			if cls.opts_alpha & 2 ** cls.dico_opts_id[i] != 0:
				alpha_repr += i
			else:
				alpha_repr += "-"
		sys.stdout.write(f"\033[{cls.size[1] - 1};{12}H\033[47m\033[30m{alpha_repr}\033[0m")
		print("\033[1;1H")
		if show_os_infos:
			cls.actulise_os_infos("battery")
			cls.actulise_os_infos("luminosity")

	@classmethod
	def set_data(cls, p_id, x, y, width, height):  # TODO
		cls.sp_dico[p_id].x = x
		cls.sp_dico[p_id].y = y
		cls.sp_dico[p_id].width = width
		cls.sp_dico[p_id].height = height

	@classmethod
	def load_data(cls):
		path_n = cls.path + "/notes"
		data_path = [os.path.join(path_n, f).split("/")[-1] for f in sorted(os.listdir(path_n)) if
					 os.path.isdir(os.path.join(path_n, f))]  # Pours toutes les matiere
		for i in data_path:
			path_i = cls.path + "/notes/" + i
			cours_path = [os.path.join(path_i, f).split("/")[-1] for f in sorted(os.listdir(path_i)) if
						  os.path.isdir(os.path.join(path_i, f))]  # Pour touts les intercalaire de cours
			cls.data_path[i] = {k: [True] + [os.path.join(path_i + "/" + k, f).split("/")[-1] for f in
											 sorted(os.listdir(path_i + "/" + k)) if
											 os.path.isfile(os.path.join(path_i + "/" + k, f))] for k in cours_path}

	@classmethod
	def box_app(cls, a_id):  # Error to fix
		def verifie_page(p_id):
			if Infos.sp_alpha & 2 ** 5 != 0 and 2 <= p_id <= 4:
				return False
			return a_id == p_id and Infos.sp_alpha & 2 ** p_id != 0

		if verifie_page(0):  # Liste touts les fichiers dans le $PATH
			for index, i in enumerate(cls.data_path.keys()):
				color = ("\033[33m" if i == cls.matiere_index else "")
				sys.stdout.write(color + f"\033[{index + 4};{3 + cls.sp_dico[1].x}H- {i}\033[0m")
			cls.box_app(1)
		elif verifie_page(1):
			tmp_box = cls.sp_dico[2]
			for i in range(tmp_box.y, tmp_box.height + tmp_box.y - 5):  # Clear Box
				sys.stdout.write(f"\033[{i + 3};{tmp_box.x + 3}H{' ' * (tmp_box.width - 4)}")
			cls.tmp_list = []
			cls.inter_index = None
			for i in cls.data_path[cls.matiere_index].keys():
				visible_inter = cls.data_path[cls.matiere_index][i][0]
				if visible_inter:
					tmp_comp_list = []
					for j in cls.data_path[cls.matiere_index][i][1:]:
						if j == cls.cours_index:
							color = "\033[33m"
							cls.inter_index = i
						else:
							color = ""
						match = re.search("\.[A-Za-z0-9_à-öÀ-Ö]+$",j)
						if match is None:
							before = cls.icons['no_file']
						else:
							if match.group(0) in cls.ext_file_icons.keys():
								before = cls.ext_file_icons[match.group(0)]
							else:
								before = cls.icons['no_file'] 
						tmp_comp_list += ["  "+before+" "+ color + j]
					cls.tmp_list += [Infos.icons['folder_open'] + " " + ("\033[33m" if i == cls.cours_index else "") + i] + tmp_comp_list
				else:
					cls.tmp_list += [Infos.icons['folder_close'] + " " + ("\033[33m" if i == cls.cours_index else "") + i]
			if len(cls.tmp_list) != 0:
				for index, i in enumerate(cls.tmp_list):
					sys.stdout.write(f"\033[{index + 4};{3 + cls.sp_dico[2].x}H{i}\033[0m")
				cls.generate_infos()
			else:
				sys.stdout.write(f"\033[{4};{3 + cls.sp_dico[2].x}HFichier vide")
				cls.toc_data = "Empty"
			cls.box_app(2)
			cls.box_app(3)
		elif verifie_page(2):
			# TODO clean Box
			index = 0
			tmp_box = cls.sp_dico[2 ** 2]
			for i in range(tmp_box.y, tmp_box.height + tmp_box.y - 4):  # Clear Box
				sys.stdout.write(f"\033[{i + 3};{tmp_box.x + 3}H{' ' * (tmp_box.width - 3)}")
			if len(cls.toc_data) == 0:
				sys.stdout.write(f"\033[{tmp_box.y + 3};{tmp_box.x + 2}HPas de titre")
			elif cls.toc_data == "Folder":
				sys.stdout.write(f"\033[{tmp_box.y + 3};{tmp_box.x + 2}HFeature: Toc of folder")
			elif cls.toc_data == "Undefined":
				sys.stdout.write(f"\033[{tmp_box.y + 3};{tmp_box.x + 2}HRien est selectionée")
			elif cls.toc_data == "Empty":
				sys.stdout.write(f"\033[{tmp_box.y + 3};{tmp_box.x + 2}HFichier vide")
			else:
				for hx, value in cls.toc_data:
					sys.stdout.write(f"\033[{tmp_box.y + 3 + index};{tmp_box.x + 2}H{hx * '  ' + '- '}{value}")
					index += 1

		elif verifie_page(3):
			# TODO clean Box
			index = 0
			tmp_box = cls.sp_dico[2 ** 3]
			for i in range(tmp_box.y, tmp_box.height + tmp_box.y - 4):  # Clear Box
				sys.stdout.write(f"\033[{i + 3};{tmp_box.x + 3}H{' ' * (tmp_box.width - 3)}")
			for key, value in cls.infos_data.items():
				sys.stdout.write(f"\033[{tmp_box.y + 3 + index};{tmp_box.x + 4}H\033[33m{key}\033[0m {value}")
				index += 1
		elif verifie_page(4):  # Attribute
			pass
		elif verifie_page(5):
			tmp_box = cls.sp_dico[2 ** 5]
			for i in range(tmp_box.y, tmp_box.height + tmp_box.y-2):  # Clear Box
				sys.stdout.write(f"\033[{i};{tmp_box.x}H{' ' * (tmp_box.width+1)}")
			if cls.generate_path()[1]:  # si se n'est pas un fichier on annule
				index = 0
				file_data = []
				for i in cls.file_data.split("\n"):
					file_data += split_line(i)
				for i in range(tmp_box.y, tmp_box.height + tmp_box.y-2):  # Clear Box
					sys.stdout.write(f"\033[{i};{tmp_box.x}H{' ' * (tmp_box.width+1)}")
				for value in file_data:
					sys.stdout.write(f"\033[{tmp_box.y + index};{tmp_box.x}H{value}")
					index += 1
		print("\033[1;1H")

	@classmethod
	def show_name(cls):
		for i in range(0, 5):  # On n’affiche pas le nom de La box 5 pour avoir plus de place
			c_box = cls.sp_dico[2 ** i]
			selected = "\033[1;33;3;7m" if cls.current_page == i else ""
			if cls.sp_alpha & 2 ** i != 0:  # Si elle est visible
				if i == 2 or i == 3 or i == 4:
					if cls.sp_alpha & 2 ** 5 == 0:  # Si elle est visible
						sys.stdout.write(f"\033[{c_box.y + 1};{c_box.x + 2}H{selected}{c_box.name}\033[0m")
				else:
					sys.stdout.write(f"\033[{c_box.y + 1};{c_box.x + 2}H{selected}{c_box.name}\033[0m")
		print("\033[1;1H")

	@classmethod
	def view(cls):
		# ------------------ vsp and hsp
		vertical_windows = 0  # | |
		horizontal_windows = 0  # -_
		for i in range(0, 2):  # Si box 0 ou 1 est visible
			if cls.sp_alpha & 2 ** i != 0:
				vertical_windows += 1

		if cls.sp_alpha / 3 > 1.0:  # Si une des box [2-5] ext visible
			vertical_windows += 1
			if cls.sp_alpha & 2 ** 5:  # Si box 5 est visible
				horizontal_windows = 1
			else:
				for i in range(2, 5):
					if cls.sp_alpha & 2 ** i:  # Si box [2-4] est visible
						horizontal_windows += 1
		# ------------------ Taille des Box
		hsp = 0
		vsp = 0
		for i in range(0, 6):  # Pour toutes les box
			if cls.sp_alpha & 2 ** i != 0:  # Si elle est visible
				if i == 0 or i == 1 or i == 5:  # Si elle est verticale
					width = cls.size[0] // (vertical_windows if vertical_windows != 0 else 1)
					height = cls.size[1]
					cls.set_data(2 ** i, cls.size[0] // vertical_windows * vsp + 1, 1, width, height)
					vsp += 1
				else:  # Si elle est horizontals
					if cls.sp_alpha & 2 ** 5 == 0:  # Si 5 est visible alors rien
						width = cls.size[0] // (vertical_windows if vertical_windows != 0 else 1)
						height = cls.size[1] // (horizontal_windows if horizontal_windows != 0 else 1)
						cls.set_data(2 ** i, cls.size[0] // vertical_windows * vsp + 1,
									 cls.size[1] // horizontal_windows * hsp + 1, width, height)
					hsp += 1
		# ------------------------ action de la box
		for i in range(0, 6):
			if cls.sp_alpha & 2 ** i != 0:
				cls.box_app(i)

		# ------------------------ show name
		cls.show_name()
		# ------------------------ view
		for border in range(1, vertical_windows):
			for i in range(cls.size[1] - 1):  # Pour tout la hauteur
				sys.stdout.write(f"\033[{i};{cls.size[0] // vertical_windows * border}H\033[47m\033[30m\u2502\033[0m")
		for border in range(1, horizontal_windows):
			# for i in range(cls.size[0] // vertical_windows * (vertical_windows - 1), cls.size[0] + 1):  # For longueur
			# 	sys.stdout.write(f"\033[{cls.size[1] // horizontal_windows * border};{i}H\033[47m\033[30m-\033[0m")
			sys.stdout.write(
				f"\033[{cls.size[1] // horizontal_windows * border};{cls.size[0] // vertical_windows * (vertical_windows - 1)}H\033[47m\033[30m\u251c{'─' * ((cls.size[0] // vertical_windows) - 1)}\033[0m")

		# ------------------------ Message en bas dernière ligne
		print("\033[1;1H")  # Besoin de ça mais il est deja dans le notif

	@classmethod
	def write_message(cls, msg, is_input=False):  # Petit message en bas
		# Faut éviter les couleurs ou escape key
		# Sinon faut refaire le truc
		if is_input:
			sys.stdout.write(f"\033[{cls.size[1]};1H" + (" " * cls.size[0]))
			the_input = input(f"\033[{cls.size[1]};1H" + msg + ":")
			Infos.reload()
			return the_input
		sys.stdout.write(f"\033[{cls.size[1]};1H" + ((msg + (" " * cls.size[0]))[:cls.size[0]]))
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
	if on_linux:  # No mouse terminal on Windows :(
		# Set config
		print(mouse_on)
	Infos.load_data()

	# Start Program
	def run():
		Infos.reload()
		Key.start()
		Draw.start()

	run()


def set_path():
	if "-p" in sys.argv and len(sys.argv) > 1 + sys.argv.index("-p"):
		Infos.path = sys.argv[sys.argv.index("-p") + 1]
		if os.path.isfile(Infos.path):
			raise TypeError("Ceci est un fichier")
		elif os.path.isdir(Infos.path):
			if os.path.isdir(Infos.path + "/notes"):
				return True
			raise Exception("Il faut un fichier '/notes'")
		raise Exception("Il faut choisir un fichier")
	else:
		Infos.path = "/home/ay/Cours2022Git"
		if os.path.isdir(Infos.path):
			if os.path.isdir(Infos.path + "/notes"):
				return True
			raise Exception("Il faut un fichier '/notes'")
		raise Exception("/home/ay/Cours2022Git not found")


def add_mathjax():
	with open("tex-chtml.js", "r") as f:
		return f.read()

def add_css(show = True):
	style = """
body {

}
	"""
	return "<style>\n" + sytle + "\n</style>"

def math(show = True):
	if show:
		return """
\t<script>
\t\tMathJax = {
\t\t\ttex: {
\t\t\t\t inlineMath: [['$', '$'], ['\\\\(', '\\\\)']]
\t\t\t},
\t\t\tsvg: {
\t\t\t\tfontCache: 'global'
\t\t\t}
\t\t};
\t</script>
\t<script id="MathJax-script" async>
\t\t""" + add_mathjax() + """
\t</script>""" 
	else:
		return ""

def dark_mode(show = True):
	if show:
		return """
\t<style>
\t\tbody{
\t\t\tbackground-color: black;
\t\t\tcolor: white;
\t\t}
\t</style>"""
	else:
		return ""

def model(body, show_math, show_dark_mode):
	return """
<!doctype html>
<html lang="fr">
<head>
\t<meta charset="utf-8">
\t<title>Titre de la page</title>
\t<meta http-equiv="X-UA-Compatible" content="IE=edge">
\t<meta name="viewport" content="width=device-width, initial-scale=1.0">
\t\t"""+dark_mode(show_dark_mode)+"""
\t\t"""+math(show_math)+"""
</head>
<body>
"""+body+"""
</body>
</html>
"""
		
def multi_markdown(filename, math, dark):
	result = subprocess.run(("multimarkdown "+filename).split(" "), stdout=subprocess.PIPE)
	return model(result.stdout.decode('utf-8'), math, dark)
if __name__ == '__main__':
	if "--debug" in sys.argv:
		debug = True
	else:
		debug = False
	show_os_infos = False
	if set_path():
		main()
