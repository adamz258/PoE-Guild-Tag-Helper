import csv
import string
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

MAX_TAG_LENGTH = 6
MIN_TAG_LENGTH = 1
DATA_FILE_NAME = "poedb-map-guild-character-list.csv"
NO_CHARACTER_MARKER = "\u2014"


def load_guild_tag_data(csv_path):
    """Load map-to-character data from the CSV file with simple validation."""
    character_to_maps = {}
    invalid_rows = 0
    invalid_entries = 0

    if not csv_path.exists():
        raise FileNotFoundError(f"Data file not found: {csv_path.name}")

    # utf-8-sig handles a UTF-8 BOM if the editor adds one.
    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader, None)

        if header is None:
            raise ValueError("Data file is empty.")

        for row_index, row in enumerate(reader, start=2):
            if len(row) < 2:
                continue

            map_name = row[0].strip()
            tag_fields = [field.strip() for field in row[1:] if field.strip()]

            if not map_name:
                invalid_rows += 1
                continue

            if not tag_fields:
                continue

            for tag_char in tag_fields:
                if tag_char == NO_CHARACTER_MARKER:
                    # The em dash means the map does not grant a guild tag character.
                    continue

                if len(tag_char) != 1:
                    invalid_entries += 1
                    continue

                character_to_maps.setdefault(tag_char, set()).add(map_name)

    # Sort map lists so the UI is predictable and easy to scan.
    character_to_maps = {char: sorted(maps) for char, maps in character_to_maps.items()}

    warnings = []
    if invalid_rows:
        warnings.append(f"{invalid_rows} row(s) are missing a map name.")
    if invalid_entries:
        warnings.append(
            f"Ignored {invalid_entries} tag value(s) that were not single characters."
        )

    return character_to_maps, warnings


def build_sorted_characters(character_to_maps):
    """Sort ASCII letters and digits first, then any symbols."""
    ascii_digits = set(string.digits)
    ascii_letters = set(string.ascii_letters)

    def sort_key(character):
        if character in ascii_letters:
            return (0, character.lower(), character)
        if character in ascii_digits:
            return (1, int(character))
        return (2, ord(character))

    return sorted(character_to_maps.keys(), key=sort_key)


def populate_character_tree(tree, sorted_characters, character_to_maps):
    for character in sorted_characters:
        map_list = ", ".join(character_to_maps.get(character, []))
        tree.insert("", "end", values=(character, map_list))


def update_tag_results(tag_text, character_to_maps, results_listbox, status_var, count_var):
    results_listbox.delete(0, tk.END)
    count_var.set(f"{len(tag_text)}/{MAX_TAG_LENGTH}")

    if not tag_text:
        status_var.set("Enter 1-6 characters to see required maps.")
        return

    if len(tag_text) < MIN_TAG_LENGTH:
        status_var.set(f"Tag must be at least {MIN_TAG_LENGTH} character.")
        return

    def resolve_character_maps(character):
        maps = character_to_maps.get(character)
        if maps:
            return maps

        if len(character) == 1 and character.isalpha():
            lower_char = character.lower()
            upper_char = character.upper()

            if lower_char != character:
                maps = character_to_maps.get(lower_char)
                if maps:
                    return maps

            if upper_char != character:
                maps = character_to_maps.get(upper_char)
                if maps:
                    return maps

        return None

    missing_chars = []
    for index, character in enumerate(tag_text, start=1):
        maps = resolve_character_maps(character)
        if not maps:
            results_listbox.insert(tk.END, f"{index}. {character} -> No map found")
            missing_chars.append(character)
            continue

        map_list = ", ".join(maps)
        results_listbox.insert(tk.END, f"{index}. {character} -> {map_list}")

    if missing_chars:
        unique_missing = ", ".join(sorted(set(missing_chars)))
        status_var.set(f"Unknown character(s): {unique_missing}")
    else:
        status_var.set("")


def main():
    csv_path = Path(__file__).with_name(DATA_FILE_NAME)

    try:
        character_to_maps, data_warnings = load_guild_tag_data(csv_path)
    except Exception as exc:
        error_root = tk.Tk()
        error_root.withdraw()
        messagebox.showerror("Guild Tag Helper", str(exc))
        error_root.destroy()
        return

    sorted_characters = build_sorted_characters(character_to_maps)

    root = tk.Tk()
    root.title("PoE Guild Tag Map Helper")
    root.minsize(800, 600)

    main_frame = ttk.Frame(root, padding=12)
    main_frame.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(1, weight=1)
    main_frame.rowconfigure(2, weight=2)

    input_frame = ttk.LabelFrame(main_frame, text="Guild Tag")
    input_frame.grid(row=0, column=0, sticky="ew")
    input_frame.columnconfigure(1, weight=1)

    tag_var = tk.StringVar()
    count_var = tk.StringVar(value=f"0/{MAX_TAG_LENGTH}")
    status_var = tk.StringVar()

    ttk.Label(input_frame, text="Tag (1-5 characters):").grid(
        row=0, column=0, sticky="w", padx=(0, 8)
    )
    tag_entry = ttk.Entry(input_frame, textvariable=tag_var)
    tag_entry.grid(row=0, column=1, sticky="ew")
    ttk.Label(input_frame, textvariable=count_var).grid(
        row=0, column=2, sticky="e", padx=(8, 0)
    )

    status_label = tk.Label(input_frame, textvariable=status_var, fg="firebrick")
    status_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))

    results_frame = ttk.LabelFrame(main_frame, text="Maps to Sacrifice")
    results_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
    results_frame.columnconfigure(0, weight=1)
    results_frame.rowconfigure(0, weight=1)

    results_listbox = tk.Listbox(results_frame, height=6)
    results_listbox.grid(row=0, column=0, sticky="nsew")
    results_scroll = ttk.Scrollbar(
        results_frame, orient="vertical", command=results_listbox.yview
    )
    results_scroll.grid(row=0, column=1, sticky="ns")
    results_listbox.configure(yscrollcommand=results_scroll.set)

    characters_frame = ttk.LabelFrame(
        main_frame, text="All Guild Tag Characters (A-Z, 0-9, then symbols)"
    )
    characters_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
    characters_frame.columnconfigure(0, weight=1)
    characters_frame.rowconfigure(0, weight=1)

    tree = ttk.Treeview(
        characters_frame, columns=("character", "maps"), show="headings"
    )
    tree.heading("character", text="Character")
    tree.heading("maps", text="Maps")
    tree.column("character", width=90, anchor="center", stretch=False)
    tree.column("maps", width=600, anchor="w")
    tree.grid(row=0, column=0, sticky="nsew")

    tree_scroll_y = ttk.Scrollbar(characters_frame, orient="vertical", command=tree.yview)
    tree_scroll_y.grid(row=0, column=1, sticky="ns")
    tree_scroll_x = ttk.Scrollbar(
        characters_frame, orient="horizontal", command=tree.xview
    )
    tree_scroll_x.grid(row=1, column=0, sticky="ew")
    tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

    data_warning_var = tk.StringVar()
    if data_warnings:
        data_warning_var.set("Data warning: " + " | ".join(data_warnings))
    data_warning_label = tk.Label(
        main_frame, textvariable=data_warning_var, fg="firebrick"
    )
    data_warning_label.grid(row=3, column=0, sticky="w", pady=(8, 0))

    def on_tag_change(*_):
        tag_text = tag_var.get()

        cleaned_text = tag_text.replace("\n", "").replace("\r", "")
        if cleaned_text != tag_text:
            tag_var.set(cleaned_text)
            return

        if len(tag_text) > MAX_TAG_LENGTH:
            tag_var.set(tag_text[:MAX_TAG_LENGTH])
            return

        update_tag_results(
            tag_text, character_to_maps, results_listbox, status_var, count_var
        )

    tag_var.trace_add("write", on_tag_change)

    populate_character_tree(tree, sorted_characters, character_to_maps)
    update_tag_results("", character_to_maps, results_listbox, status_var, count_var)

    tag_entry.focus()
    root.mainloop()


if __name__ == "__main__":
    main()
