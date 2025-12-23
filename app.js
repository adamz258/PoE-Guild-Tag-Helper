const DATA_FILE = "poedb-map-guild-character-list.csv";
const MAX_TAG_LENGTH = 6;
const NO_CHARACTER_MARKER = "\u2014";

const tagInput = document.getElementById("tagInput");
const resultsList = document.getElementById("resultsList");
const statusMessage = document.getElementById("statusMessage");
const charCount = document.getElementById("charCount");
const characterCount = document.getElementById("characterCount");
const characterTableBody = document.getElementById("characterTableBody");

const state = {
  charToMaps: new Map(),
  sortedChars: [],
};

function parseCsv(text) {
  // Basic CSV parser that handles quotes and commas without external libraries.
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const nextChar = text[i + 1];

    if (inQuotes) {
      if (char === '"' && nextChar === '"') {
        field += '"';
        i += 1;
      } else if (char === '"') {
        inQuotes = false;
      } else {
        field += char;
      }
      continue;
    }

    if (char === '"') {
      inQuotes = true;
      continue;
    }

    if (char === ",") {
      row.push(field);
      field = "";
      continue;
    }

    if (char === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
      continue;
    }

    if (char === "\r") {
      continue;
    }

    field += char;
  }

  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }

  return rows;
}

function addMapToCharacter(mapName, tagChar) {
  if (!state.charToMaps.has(tagChar)) {
    state.charToMaps.set(tagChar, new Set());
  }
  state.charToMaps.get(tagChar).add(mapName);
}

function buildSortedCharacters() {
  const asciiLetters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const asciiDigits = "0123456789";

  const sortKey = (character) => {
    if (asciiLetters.includes(character)) {
      return [0, character.toLowerCase(), character];
    }
    if (asciiDigits.includes(character)) {
      return [1, Number(character)];
    }
    return [2, character.codePointAt(0)];
  };

  state.sortedChars = Array.from(state.charToMaps.keys()).sort((a, b) => {
    const keyA = sortKey(a);
    const keyB = sortKey(b);

    for (let i = 0; i < keyA.length; i += 1) {
      if (keyA[i] < keyB[i]) return -1;
      if (keyA[i] > keyB[i]) return 1;
    }
    return 0;
  });
}

function renderCharacterTable() {
  characterTableBody.innerHTML = "";
  const fragment = document.createDocumentFragment();

  state.sortedChars.forEach((character) => {
    const maps = Array.from(state.charToMaps.get(character) || []).sort();
    const row = document.createElement("tr");

    const charCell = document.createElement("td");
    charCell.textContent = character;

    const mapsCell = document.createElement("td");
    mapsCell.textContent = maps.join(", ");

    row.appendChild(charCell);
    row.appendChild(mapsCell);
    fragment.appendChild(row);
  });

  characterTableBody.appendChild(fragment);
  characterCount.textContent = `${state.sortedChars.length} characters`;
}

function appendCharacterToTag(character) {
  if (!character) {
    return;
  }

  const currentTag = Array.from(tagInput.value);
  if (currentTag.length >= MAX_TAG_LENGTH) {
    return;
  }

  currentTag.push(character);
  tagInput.value = currentTag.join("");
  updateTagResults();
  tagInput.focus();
}

function resolveCharacterMaps(character) {
  if (state.charToMaps.has(character)) {
    return state.charToMaps.get(character);
  }

  if (character.length === 1 && /[A-Za-z]/.test(character)) {
    const lowerChar = character.toLowerCase();
    const upperChar = character.toUpperCase();

    if (lowerChar !== character && state.charToMaps.has(lowerChar)) {
      return state.charToMaps.get(lowerChar);
    }

    if (upperChar !== character && state.charToMaps.has(upperChar)) {
      return state.charToMaps.get(upperChar);
    }
  }

  return null;
}

function updateTagResults() {
  let tagText = tagInput.value;
  const characters = Array.from(tagText);

  if (characters.length > MAX_TAG_LENGTH) {
    tagText = characters.slice(0, MAX_TAG_LENGTH).join("");
    tagInput.value = tagText;
  }

  const limitedCharacters = Array.from(tagText);
  charCount.textContent = `${limitedCharacters.length}/${MAX_TAG_LENGTH}`;
  resultsList.innerHTML = "";
  statusMessage.textContent = "";

  if (!tagText) {
    statusMessage.textContent = "Enter 1-6 characters to see required maps.";
    return;
  }

  const missingCharacters = new Set();
  limitedCharacters.forEach((character) => {
    const maps = resolveCharacterMaps(character);
    const listItem = document.createElement("li");

    if (!maps) {
      listItem.textContent = `${character} → No map found`;
      listItem.classList.add("missing");
      missingCharacters.add(character);
    } else {
      listItem.textContent = `${character} → ${Array.from(maps).join(", ")}`;
    }

    resultsList.appendChild(listItem);
  });

  if (missingCharacters.size > 0) {
    statusMessage.textContent = `Unknown character(s): ${Array.from(missingCharacters).sort().join(", ")}`;
  }
}

function loadData() {
  fetch(DATA_FILE)
    .then((response) => response.text())
    .then((text) => {
      const rows = parseCsv(text);
      rows.shift();

      rows.forEach((row) => {
        if (!row || row.length === 0) {
          return;
        }

        const mapName = (row[0] || "").trim();
        if (!mapName) {
          return;
        }

        const tagFields = row
          .slice(1)
          .map((field) => field.trim())
          .filter(Boolean);

        if (tagFields.length === 0) {
          return;
        }

        tagFields.forEach((tagChar) => {
          if (tagChar === NO_CHARACTER_MARKER) {
            return;
          }
          if (tagChar.length !== 1) {
            return;
          }
          addMapToCharacter(mapName, tagChar);
        });
      });

      buildSortedCharacters();
      renderCharacterTable();
      updateTagResults();
    })
    .catch(() => {
      statusMessage.textContent =
        "Unable to load the map data file. Make sure the CSV is in the same folder.";
    });
}

tagInput.addEventListener("input", updateTagResults);

characterTableBody.addEventListener("dblclick", (event) => {
  const target = event.target instanceof Element ? event.target : event.target.parentElement;
  if (!target) {
    return;
  }

  const row = target.closest("tr");
  if (!row || !characterTableBody.contains(row)) {
    return;
  }

  const characterCell = row.querySelector("td");
  if (!characterCell) {
    return;
  }

  appendCharacterToTag(characterCell.textContent.trim());
});

loadData();
