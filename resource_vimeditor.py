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
