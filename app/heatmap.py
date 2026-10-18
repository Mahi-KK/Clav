LAYOUT = [
    [("`", "`", "~", 1), ("1", "1", "!", 1), ("2", "2", "@", 1),
     ("3", "3", "#", 1), ("4", "4", "$", 1), ("5", "5", "%", 1),
     ("6", "6", "^", 1), ("7", "7", "&", 1), ("8", "8", "*", 1),
     ("9", "9", "(", 1), ("0", "0", ")", 1), ("-", "-", "_", 1),
     ("=", "=", "+", 1), ("Backspace", "Backspace", "", 2)],
    [("Tab", "Tab", "", 1.5), ("q", "Q", "", 1), ("w", "W", "", 1),
     ("e", "E", "", 1), ("r", "R", "", 1), ("t", "T", "", 1),
     ("y", "Y", "", 1), ("u", "U", "", 1), ("i", "I", "", 1),
     ("o", "O", "", 1), ("p", "P", "", 1), ("[", "[", "{", 1),
     ("]", "]", "}", 1), ("\\", "\\", "|", 1.5)],
    [("CapsLock", "Caps", "", 1.75), ("a", "A", "", 1), ("s", "S", "", 1),
     ("d", "D", "", 1), ("f", "F", "", 1), ("g", "G", "", 1),
     ("h", "H", "", 1), ("j", "J", "", 1), ("k", "K", "", 1),
     ("l", "L", "", 1), (";", ";", ":", 1), ("'", "'", '"', 1),
     ("Enter", "Enter", "", 2.25)],
    [("ShiftLeft", "Shift", "", 2.25), ("z", "Z", "", 1), ("x", "X", "", 1),
     ("c", "C", "", 1), ("v", "V", "", 1), ("b", "B", "", 1),
     ("n", "N", "", 1), ("m", "M", "", 1), (",", ",", "<", 1),
     (".", ".", ">", 1), ("/", "/", "?", 1), ("ShiftRight", "Shift", "", 2.75)],
    [("Space", "Space", "", 6.25)],
]

LABELS = {key_id: label for row in LAYOUT for key_id, label, _, _ in row}

SHIFTED = {
    "~": "`", "!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6",
    "&": "7", "*": "8", "(": "9", ")": "0", "_": "-", "+": "=", "{": "[",
    "}": "]", "|": "\\", ":": ";", '"': "'", "<": ",", ">": ".", "?": "/",
}

SPECIAL = {" ": "Space", "\n": "Enter", "\t": "Tab"}

UNSHIFTED = {key_id for row in LAYOUT for key_id, label, _, _ in row
             if len(key_id) == 1}

FINGERS = {
    "left_pinky": ["`", "1", "q", "a", "z", "Tab", "CapsLock", "ShiftLeft"],
    "left_ring": ["2", "w", "s", "x"],
    "left_middle": ["3", "e", "d", "c"],
    "left_index": ["4", "5", "r", "t", "f", "g", "v", "b"],
    "right_index": ["6", "7", "y", "u", "h", "j", "n", "m"],
    "right_middle": ["8", "i", "k", ","],
    "right_ring": ["9", "o", "l", "."],
    "right_pinky": ["0", "-", "=", "p", "[", "]", "\\", ";", "'", "/",
                    "Enter", "Backspace", "ShiftRight"],
    "thumbs": ["Space"],
}

FINGER_OF = {key: finger for finger, keys in FINGERS.items() for key in keys}

HOME_ROW = {"a", "s", "d", "f", "g", "h", "j", "k", "l", ";"}

TOP_N = 5


def key_for(char):
    if char in SPECIAL:
        return SPECIAL[char], False
    if char in SHIFTED:
        return SHIFTED[char], True
    lower = char.lower()
    if lower in UNSHIFTED and len(char) == 1:
        return lower, char != lower
    return None


def shift_key_for(key_id):
    return "ShiftRight" if FINGER_OF[key_id].startswith("left") else "ShiftLeft"


def _pct(part, whole):
    return round(100 * part / whole, 1) if whole else 0.0


def analyze(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    counts = {}
    shift_presses = 0
    unmapped = 0

    for char in text:
        mapped = key_for(char)
        if mapped is None:
            unmapped += 1
            continue
        key_id, needs_shift = mapped
        counts[key_id] = counts.get(key_id, 0) + 1
        if needs_shift:
            shift = shift_key_for(key_id)
            counts[shift] = counts.get(shift, 0) + 1
            shift_presses += 1

    keystrokes = sum(counts.values())
    peak = max((n for key_id, n in counts.items() if key_id != "Space"),
               default=counts.get("Space", 0))

    fingers = {finger: 0 for finger in FINGERS}
    for key_id, n in counts.items():
        fingers[FINGER_OF[key_id]] += n

    left = sum(n for f, n in fingers.items() if f.startswith("left"))
    right = sum(n for f, n in fingers.items() if f.startswith("right"))
    hand_total = left + right
    home = sum(n for key_id, n in counts.items() if key_id in HOME_ROW)

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    top_keys = [{"key": key_id, "label": LABELS[key_id], "count": n}
                for key_id, n in ranked[:TOP_N]]

    return {
        "characters": len(text),
        "keystrokes": keystrokes,
        "counts": counts,
        "intensity": {key_id: round(min(n / peak, 1.0), 3)
                      for key_id, n in counts.items()},
        "top_keys": top_keys,
        "fingers": fingers,
        "hands": {"left": _pct(left, hand_total), "right": _pct(right, hand_total)},
        "home_row": _pct(home, hand_total),
        "shift_presses": shift_presses,
        "unmapped": unmapped,
    }
