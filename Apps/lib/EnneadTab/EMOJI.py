#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Get emojis from the emoji library."""

import io
import random
import DOCUMENTATION

def get_all_emojis():
    """Get all emojis from the emoji library.

    Returns:
        list: List of emojis. Returns empty list if there's an error reading the emoji file.
    """
    with io.open(DOCUMENTATION.get_text_path_by_name('_emoji_text.txt'), "r", encoding = "utf-8") as f:
        try:
            lines = f.readlines()
        except:
            return []
    return [x.replace("\n", "") for x  in lines if x != "\n"]


def pick_emoji_text():
    """Pick an emoji text from the displayed list and copy it to the clipboard.
    """
    lines = get_all_emojis()
    from pyrevit import forms
    sel = forms.SelectFromList.show(lines, select_multiple = False, title = "Go wild")
    if not sel:
        return

    forms.ask_for_string(default = sel,
                        prompt = 'Copy below text to anywhere, maybe SheetName or Schedule',
                        title = 'pick_emoji_text')


def random_emoji():
    """Pick a random emoji.
    
    Returns:
        str: A random emoji character, or empty string if no emojis are available.
    """
    lines = get_all_emojis()
    
    if not lines:
        return ""
        
    random.shuffle(lines)
    return lines[0].replace("\n", "")
    