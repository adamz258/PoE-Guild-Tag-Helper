# PoE-Guild-Tag-Helper
A simple app that allows users to type a case insensitive string of 1-6 characters, to use as a guild tag. The app will return a list of the maps required to match each character. The mapping of maps to characters is stored in a CSV that is built from PoEDB's Map page.

# Web App Link
https://adamz-8113.github.io/PoE-Guild-Tag-Helper/

# CSV Update (PoEDB)
Run the updater script to regenerate the map-to-character CSV from PoEDB:

```
python update_poedb_map_guild_character_list.py
```

If you saved the PoEDB page locally, pass the HTML file instead:

```
python update_poedb_map_guild_character_list.py --input-html poedb_maps.html
```

The script overwrites `poedb-map-guild-character-list.csv` and only includes maps
that have a listed Guild Tag Editor character.

![Guild Tag Helper UI](screenshots/parser-gui.png)
