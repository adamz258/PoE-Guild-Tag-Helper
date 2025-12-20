# PoE-Guild-Character-Parser
A simple app that allows users to type a case insensitive 1-6 character guild tag, to get back a list of the maps required to match character. Mapping is stored in a CSV that is built from PoEDB's Map page.
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
