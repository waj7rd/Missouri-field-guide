#!/usr/bin/env python3
"""
Restructure master-final13.html:
1. Extract fish (Channel Catfish, Largemouth Bass, Crappie, Ozark Smallmouth Bass) from Fauna
2. Create new Fish tab
3. Alphabetize cards within each species-grid in Flora, Fungi, Fauna, Tracking
4. Alphabetize tree-cards within each tree-grid in Trees
5. Add Fish tab button
Output: master-final14.html
"""

from bs4 import BeautifulSoup, NavigableString
import re

SCRATCHPAD = '/tmp/claude-0/-home-claude/981a2691-61a1-5999-9ec7-8c63ae7a8726/scratchpad'

print("Loading HTML...")
with open(f'{SCRATCHPAD}/master-final13.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
print("Parsed.")

FISH_NAMES = {'Channel Catfish', 'Largemouth Bass', 'Crappie', 'Ozark Smallmouth Bass'}

# ── Helper: get sort key for a card ──────────────────────────────────────────
def card_sort_key(card):
    """Return lowercase name for sorting."""
    h3 = card.find('h3', class_='card-name')
    if h3:
        return h3.get_text().strip().lower()
    p = card.find('p', class_='tree-name')
    if p:
        return p.get_text().strip().lower()
    return ''

# ── Helper: sort cards within a grid ─────────────────────────────────────────
def sort_grid(grid, card_class):
    """Sort cards of class `card_class` within `grid` in-place, alphabetically."""
    cards = grid.find_all('div', class_=card_class)
    if len(cards) <= 1:
        return
    # Get their sort keys
    sorted_cards = sorted(cards, key=card_sort_key)
    # Re-insert in sorted order
    for card in sorted_cards:
        card.extract()
    for card in sorted_cards:
        grid.append(card)

# ─────────────────────────────────────────────────────────────────────────────
# 1. FLORA: sort Edible Plants grid and Dangerous Plants grid
# ─────────────────────────────────────────────────────────────────────────────
print("Sorting Flora...")
flora = soup.find('section', id='tab-flora')
for grid in flora.find_all('div', class_='species-grid'):
    sort_grid(grid, 'card')

# ─────────────────────────────────────────────────────────────────────────────
# 2. FUNGI: sort Prized Edible and Deadly & Dangerous grids
# ─────────────────────────────────────────────────────────────────────────────
print("Sorting Fungi...")
fungi = soup.find('section', id='tab-fungi')
for grid in fungi.find_all('div', class_='species-grid'):
    sort_grid(grid, 'card')

# ─────────────────────────────────────────────────────────────────────────────
# 3. FAUNA: extract fish, sort remaining cards
# ─────────────────────────────────────────────────────────────────────────────
print("Processing Fauna (extracting fish, sorting)...")
fauna = soup.find('section', id='tab-fauna')

fish_cards = []
for grid in fauna.find_all('div', class_='species-grid'):
    for card in grid.find_all('div', class_='card'):
        h3 = card.find('h3', class_='card-name')
        if h3 and h3.get_text().strip() in FISH_NAMES:
            fish_cards.append(card.extract())  # remove from fauna
    sort_grid(grid, 'card')

# Also sort the Notable Wildlife tree-grid in fauna
notable_grids = fauna.find_all('div', class_='tree-grid')
for g in notable_grids:
    sort_grid(g, 'tree-card')

print(f"  Extracted {len(fish_cards)} fish cards: {[c.find('h3', class_='card-name').get_text() for c in fish_cards]}")

# Update the species count in the "Edible Wildlife" section-head
edible_head = fauna.find('div', class_='section-head', string=lambda t: t and 'Edible Wildlife' in t)
if edible_head:
    # Count remaining cards
    edible_grid = edible_head.find_next_sibling('div', class_='species-grid')
    if edible_grid:
        count = len(edible_grid.find_all('div', class_='card'))
        # Update the text
        text_node = edible_head.find(string=re.compile(r'\d+ species'))
        if text_node:
            text_node.replace_with(re.sub(r'\d+ species', f'{count} species', str(text_node)))

# ─────────────────────────────────────────────────────────────────────────────
# 4. TREES: sort within each tree-grid (Oaks, Hickories, Maples, Distinctive)
# ─────────────────────────────────────────────────────────────────────────────
print("Sorting Trees...")
trees = soup.find('section', id='tab-trees')
for grid in trees.find_all('div', class_='tree-grid'):
    sort_grid(grid, 'tree-card')

# ─────────────────────────────────────────────────────────────────────────────
# 5. TRACKING: sort species-grids (not the reference tree-grids)
# ─────────────────────────────────────────────────────────────────────────────
print("Sorting Tracking...")
tracking = soup.find('section', id='tab-tracking')
for grid in tracking.find_all('div', class_='species-grid'):
    sort_grid(grid, 'card')

# ─────────────────────────────────────────────────────────────────────────────
# 6. Build new FISH tab section
# ─────────────────────────────────────────────────────────────────────────────
print("Building Fish tab...")

# Sort fish cards alphabetically
fish_cards.sort(key=card_sort_key)

fish_intro = (
    "Missouri offers outstanding freshwater fishing across its 17,000 miles of streams, "
    "over 100 major lakes, and the Mississippi and Missouri rivers. From trophy-sized channel "
    "catfish in the big rivers to smallmouth bass in crystal-clear Ozark streams, the state's "
    "aquatic habitats support some of the finest sport fishing in the Midwest."
)

# Build the new section HTML
fish_section = soup.new_tag('section', attrs={'class': 'tab-panel', 'id': 'tab-fish'})

intro_p = soup.new_tag('p', attrs={'class': 'panel-intro'})
intro_p.string = fish_intro
fish_section.append(intro_p)

# Section head
fish_head = soup.new_tag('div', attrs={'class': 'section-head'})
head_span = soup.new_tag('span')
head_span.string = 'Missouri Sport Fish'
fish_head.append(head_span)
count_span = soup.new_tag('span', attrs={'class': 'count-badge'})
count_span.string = f'{len(fish_cards)} species'
fish_head.append(count_span)
fish_section.append(fish_head)

# Fish species grid
fish_grid = soup.new_tag('div', attrs={'class': 'species-grid'})
for card in fish_cards:
    fish_grid.append(card)
fish_section.append(fish_grid)

# Insert the fish section after tab-tracking (or before tab-danger)
tab_tracking = soup.find('section', id='tab-tracking')
tab_tracking.insert_after(fish_section)

# ─────────────────────────────────────────────────────────────────────────────
# 7. Add "Fish" tab button in the tab bar
# ─────────────────────────────────────────────────────────────────────────────
print("Adding Fish tab button...")
tab_buttons = soup.find_all('button', class_='tab-btn')
# Find the Tracking button and insert Fish after Fauna
fauna_btn = None
tracking_btn = None
for btn in tab_buttons:
    if btn.get_text().strip() == 'Fauna':
        fauna_btn = btn
    if btn.get_text().strip() == 'Tracking':
        tracking_btn = btn

# Insert Fish button after Fauna
if fauna_btn:
    fish_btn = soup.new_tag('button', attrs={
        'class': 'tab-btn',
        'onclick': "showTab('fish', this)"
    })
    fish_btn.string = 'Fish'
    fauna_btn.insert_after(fish_btn)
    print("  Fish button inserted after Fauna button.")

# ─────────────────────────────────────────────────────────────────────────────
# 8. Save
# ─────────────────────────────────────────────────────────────────────────────
print("Writing output...")
out = f'{SCRATCHPAD}/master-final14.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(str(soup))

import os
size = os.path.getsize(out) / 1024 / 1024
print(f"Saved: {out} ({size:.2f} MB)")

# Verify
with open(out, 'r') as f:
    check = BeautifulSoup(f.read(), 'html.parser')
fish_sec = check.find('section', id='tab-fish')
fish_cards_check = fish_sec.find_all('div', class_='card') if fish_sec else []
print(f"Verification: Fish tab has {len(fish_cards_check)} cards")
fish_names_check = [c.find('h3', class_='card-name').get_text() for c in fish_cards_check]
print(f"  Fish: {fish_names_check}")

# Check fauna no longer has fish
fauna_check = check.find('section', id='tab-fauna')
fauna_names = [c.find('h3', class_='card-name').get_text() for c in fauna_check.find_all('div', class_='card') if c.find('h3', class_='card-name')]
fish_still_in_fauna = [n for n in fauna_names if n in FISH_NAMES]
print(f"  Fish still in fauna: {fish_still_in_fauna} (should be empty)")
print("Done!")
