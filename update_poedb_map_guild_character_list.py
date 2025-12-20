import argparse
import csv
from html.parser import HTMLParser
from pathlib import Path
import urllib.request


DEFAULT_URL = "https://poedb.tw/us/Maps#MapsItem"
DEFAULT_OUTPUT = "poedb-map-guild-character-list.csv"


class PoedbMapParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.last_map_name = None
        self.capture_map_name = False
        self.awaiting_guild_char = False
        self.capture_guild_char = False
        self.map_to_char = {}
        self.conflicts = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a":
            class_attr = attrs_dict.get("class", "")
            if "itemclass_map" in class_attr and "Map" in class_attr:
                # The anchor text that follows is the map name.
                self.capture_map_name = True
        elif tag == "span" and self.awaiting_guild_char:
            class_attr = attrs_dict.get("class", "")
            if "colourDefault" in class_attr:
                self.capture_guild_char = True

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return

        if self.capture_map_name:
            self.last_map_name = text
            self.capture_map_name = False
            return

        if text == "Guild Tag Editor:":
            self.awaiting_guild_char = True
            return

        if self.capture_guild_char:
            guild_char = text
            self.capture_guild_char = False
            self.awaiting_guild_char = False

            if self.last_map_name:
                existing = self.map_to_char.get(self.last_map_name)
                if existing and existing != guild_char:
                    self.conflicts.append(
                        (self.last_map_name, existing, guild_char)
                    )
                else:
                    self.map_to_char[self.last_map_name] = guild_char

    def handle_endtag(self, tag):
        if tag == "span" and self.capture_guild_char:
            self.capture_guild_char = False
        if tag == "a" and self.capture_map_name:
            self.capture_map_name = False


def fetch_html(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (GuildTagHelper/1.0)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_maps(html_text):
    parser = PoedbMapParser()
    parser.feed(html_text)
    return parser.map_to_char, parser.conflicts


def write_csv(output_path, map_to_char):
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Map", "Guild tag character"])
        for map_name in sorted(map_to_char.keys()):
            writer.writerow([map_name, map_to_char[map_name]])


def main():
    parser = argparse.ArgumentParser(
        description="Generate a map-to-guild-character CSV from PoEDB.",
    )
    parser.add_argument(
        "--input-html",
        help="Optional path to a saved PoEDB Maps HTML page.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT}).",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"PoEDB Maps URL (default: {DEFAULT_URL}).",
    )
    args = parser.parse_args()

    if args.input_html:
        html_text = Path(args.input_html).read_text(encoding="utf-8", errors="replace")
    else:
        html_text = fetch_html(args.url)

    map_to_char, conflicts = parse_maps(html_text)

    if not map_to_char:
        raise SystemExit("No map entries found. The page structure may have changed.")

    output_path = Path(args.output)
    write_csv(output_path, map_to_char)

    print(f"Wrote {len(map_to_char)} map entries to {output_path}")
    if conflicts:
        print("Conflicts detected (same map with different characters):")
        for map_name, existing, new_value in conflicts:
            print(f"- {map_name}: {existing} vs {new_value}")


if __name__ == "__main__":
    main()
