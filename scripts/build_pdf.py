#!/usr/bin/env python3
"""Missouri Field Guide â compact PDF builder v3
Layout goals:
  - Multiple items per page (flow-based, no forced PageBreak per item)
  - Smaller fonts, tighter spacing
  - Image 1.6" max, text alongside
  - Section dividers still full-page but compact
  - Fish section added between Wildlife & Animals and Animal Tracking
"""

import json, base64, io, sys
from pathlib import Path
from collections import OrderedDict

SCRATCHPAD = Path('/tmp/claude-0/-home-claude/981a2691-61a1-5999-9ec7-8c63ae7a8726/scratchpad')
REPO = Path(__file__).parent.parent  # missouri-field-guide/

# ââ load rich content ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
exec(open(REPO / 'scripts/rich_content.py').read())
exec(open(REPO / 'scripts/rich_content_fauna.py').read())
exec(open(REPO / 'scripts/rich_content_trees_tracking.py').read())

MASTER = {}
MASTER.update(RICH)
MASTER.update(RICH_FAUNA)
MASTER.update(RICH_TREES)
MASTER.update(RICH_TRACKING)
MASTER.update(RICH_EXTRA)

ALIAS = {
    'White-tailed Deer': 'White-tailed Deer (Tracking)',
    'Coyote':            'Coyote (Tracking)',
    'Red Fox':           'Red Fox (Tracking)',
    'Bobcat':            'Bobcat (Tracking)',
    'American Beaver':   'American Beaver (Tracking)',
    'American Black Bear': 'American Black Bear (Tracking)',
    'River Otter':       'River Otter (Tracking)',
    'Striped Skunk':     'Striped Skunk (Tracking)',
    'Muskrat':           'Muskrat (Tracking)',
    'Shumard Oak':       'Red Oak / Shumard Oak',
    'Shagbark Hickory':  'Shellbark Hickory',
    'Persimmon':         'Persimmon (Tree)',
    'Snapping Turtle (Table)': 'Snapping Turtle',
}

INLINE_RICH = {
    'True Morel vs. False Morel': {
        'description': (
            "Missouri's most-prized edible fungus â the true morel (Morchella spp.) â has several dangerous "
            "look-alikes, chief among them the False Morel (Gyromitra esculenta). A true morel has a hollow "
            "cap and stem continuous from top to bottom; cut it lengthwise and you see a single uninterrupted "
            "air space. The cap is fully attached to the stem at the base with a pitted, honeycomb-like "
            "surface rather than wrinkled, brain-like folds. True morels fruit MarchâMay in Missouri."
        ),
        'utility': (
            "False morels (Gyromitra) contain gyromitrin, which metabolizes to monomethylhydrazine â toxic "
            "even after cooking or drying. Never eat a 'morel' without slicing it top-to-bottom first."
        ),
        'facts': [
            "True morel: hollow top-to-bottom; false morel: cottony/chambered interior",
            "False morel cap: reddish-brown, wrinkled/brain-like â NOT a honeycomb",
            "True morel cap is fully fused to stem; false morel cap may hang free",
            "Gyromitrin toxin survives cooking â false morels are never safe to eat",
            "Poison Control: 1-800-222-1222",
        ]
    },
    'Wild Grape vs. Moonseed': {
        'description': (
            "Wild grape (Vitis spp.) vines produce edible fruit, but Canada Moonseed (Menispermum canadense) "
            "produces highly toxic dark berries that look similar. Key: grape leaves toothed/lobed; moonseed "
            "leaves shield-shaped with petiole near center of leaf underside. Grape bark shreds in strips; "
            "moonseed bark smooth."
        ),
        'utility': (
            "Wild grapes are edible fresh, as jelly, juice, wine, or dried. Moonseed berries contain "
            "dauricine alkaloids causing cardiac/neurological toxicity â potentially life-threatening."
        ),
        'facts': [
            "Moonseed seed is crescent-shaped; grape seed is oval/pear-shaped",
            "Grape tendril curls from nodes; moonseed has no true tendrils",
            "Moonseed leaf petiole attaches near leaf center (peltate)",
            "Cross-section a berry and examine seed shape if uncertain",
        ]
    },
    'Wild Onion vs. Death Camas': {
        'description': (
            "Wild onion (Allium canadense) and Death Camas (Anticlea elegans) both emerge in spring with "
            "grass-like leaves from a bulb. The definitive test: crush any part and smell. Wild onion "
            "always smells like onion â Death Camas has no onion smell whatsoever."
        ),
        'utility': (
            "Wild onion is edible â bulb, leaves, and flowers. Death Camas contains zygacine and steroidal "
            "alkaloids causing cardiovascular and nervous system failure. Never harvest without the smell test."
        ),
        'facts': [
            "Onion smell = safe; NO onion smell = do not eat",
            "Death Camas flowers: creamy white with 6 petals and a V-shaped gland",
            "Zygacine alkaloids are cardiotoxic â no antidote; treatment is supportive only",
        ]
    },
    "Chanterelle vs. Jack-o'-Lantern": {
        'description': (
            "The Golden Chanterelle (Cantharellus cibarius) resembles the Jack-o'-Lantern (Omphalotus "
            "olearius). Both are bright orange-yellow and funnel-shaped. Critical difference: chanterelles "
            "have forking, blunt-edged ridges (not true gills) that run partway down the stem. "
            "Jack-o'-Lanterns have true, knife-blade-thin sharp gills."
        ),
        'utility': (
            "Chanterelles are prized for fruity, apricot-like aroma â highly valuable. Jack-o'-Lanterns "
            "grow in clusters at tree bases; chanterelles grow singly on the forest floor. Jack-o'-Lanterns "
            "glow faintly blue-green in darkness â check them in a dark room."
        ),
        'facts': [
            "Chanterelle: blunt forked ridges; Jack-o'-Lantern: sharp true gills",
            "Jack-o'-Lanterns glow in the dark â diagnostic feature",
            "Jack-o'-Lantern flesh is orange throughout; chanterelle flesh is solid white inside",
        ]
    },
}

MASTER.update(INLINE_RICH)

# ââ load items and add fish ââââââââââââââââââââââââââââââââââââââââââââââââââ
items = json.load(open(REPO / 'data/items_full.json'))
print(f"Items from JSON: {len(items)}")

# Fish items to extract from Wildlife & Animals and place in Fish section
FISH_NAMES = {
    'Channel Catfish', 'Largemouth Bass', 'Crappie', 'Ozark Smallmouth Bass',
    'Bluegill', 'Walleye', 'Flathead Catfish', 'Blue Catfish',
    'White Bass', 'Paddlefish', 'Rainbow Trout', 'Alligator Gar',
}

fish_items = []
non_fish_items = []
for item in items:
    if item['name'] in FISH_NAMES:
        fish_items.append(item)
    else:
        non_fish_items.append(item)

print(f"Fish items: {[i['name'] for i in fish_items]}")

# Rich content for fish (from RICH_FAUNA which is in MASTER)
# They should already be in MASTER via RICH_FAUNA

# ââ reportlab setup ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

W, H = letter  # 8.5 x 11

SECTION_COLORS = {
    'Wildflowers & Plants':  colors.HexColor('#2d6a4f'),
    'Fungi & Mushrooms':     colors.HexColor('#7b4f2e'),
    'Wildlife & Animals':    colors.HexColor('#1a4971'),
    'Fish':                  colors.HexColor('#0a4f6e'),
    'Animal Tracking':       colors.HexColor('#4a3728'),
    'Trees':                 colors.HexColor('#2c5f2e'),
    'Danger Zone':           colors.HexColor('#8b1a1a'),
}

def section_color(section):
    for k, v in SECTION_COLORS.items():
        if k in section:
            return v
    return colors.HexColor('#444444')

styles = getSampleStyleSheet()

# Compact styles â smaller fonts, tighter leading/spacing
style_body = ParagraphStyle('Body',
    parent=styles['Normal'],
    fontSize=8.5, leading=11.5, spaceAfter=4, spaceBefore=0)

style_utility = ParagraphStyle('Utility',
    parent=styles['Normal'],
    fontSize=8.5, leading=11.5, spaceAfter=4, spaceBefore=2,
    textColor=colors.HexColor('#1a3a1a'))

style_fact_header = ParagraphStyle('FactHdr',
    parent=styles['Normal'],
    fontSize=8.5, leading=10, spaceBefore=4, spaceAfter=2,
    textColor=colors.HexColor('#333333'), fontName='Helvetica-Bold')

style_fact = ParagraphStyle('Fact',
    parent=styles['Normal'],
    fontSize=8, leading=10.5, spaceAfter=1.5,
    leftIndent=10, firstLineIndent=-10)

style_divider_title = ParagraphStyle('DivTitle',
    parent=styles['Heading1'],
    fontSize=28, leading=32, textColor=colors.white, alignment=TA_CENTER)

style_divider_sub = ParagraphStyle('DivSub',
    parent=styles['Normal'],
    fontSize=12, textColor=colors.HexColor('#dddddd'), alignment=TA_CENTER)

def b64_to_image(b64_str, max_w=1.6*inch, max_h=1.6*inch):
    try:
        if b64_str and b64_str.startswith('data:'):
            header, data = b64_str.split(',', 1)
            img_bytes = base64.b64decode(data)
            buf = io.BytesIO(img_bytes)
            img = Image(buf)
            iw, ih = img.drawWidth, img.drawHeight
            scale = min(max_w / iw, max_h / ih, 1.0)
            img.drawWidth = iw * scale
            img.drawHeight = ih * scale
            return img
    except:
        pass
    return None

def make_cover():
    story = []
    story.append(Spacer(1, 2.0*inch))
    cover_title = ParagraphStyle('CoverTitle',
        parent=styles['Normal'],
        fontSize=36, leading=42, textColor=colors.HexColor('#1a3d1a'),
        alignment=TA_CENTER, fontName='Helvetica-Bold')
    cover_sub = ParagraphStyle('CoverSub',
        parent=styles['Normal'],
        fontSize=14, leading=18, textColor=colors.HexColor('#2d6a4f'), alignment=TA_CENTER)
    cover_note = ParagraphStyle('CoverNote',
        parent=styles['Normal'],
        fontSize=10, leading=13, textColor=colors.HexColor('#555555'), alignment=TA_CENTER)
    story.append(Paragraph("Missouri Field Guide", cover_title))
    story.append(Spacer(1, 0.25*inch))
    story.append(Paragraph(
        "Edible Plants Â· Fungi Â· Wildlife Â· Fish Â· Animal Tracking Â· Trees Â· Danger Zone",
        cover_sub))
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width='60%', thickness=2,
        color=colors.HexColor('#1a3d1a'), hAlign='CENTER'))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "A comprehensive field reference for Missouri's outdoors â<br/>"
        "identification, ecology, edibility, utility, and safety", cover_note))
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph("2024 Edition", cover_note))
    story.append(PageBreak())
    return story

def make_section_divider(section_name, count):
    sc = section_color(section_name)
    story = []
    story.append(Spacer(1, 1.5*inch))
    div_title = ParagraphStyle('DT', parent=styles['Normal'],
        fontSize=28, leading=32, textColor=sc, alignment=TA_CENTER, fontName='Helvetica-Bold')
    div_sub = ParagraphStyle('DS', parent=styles['Normal'],
        fontSize=11, textColor=colors.HexColor('#555555'), alignment=TA_CENTER)
    story.append(Paragraph(section_name, div_title))
    story.append(Spacer(1, 0.15*inch))
    story.append(HRFlowable(width='50%', thickness=2, color=sc, hAlign='CENTER'))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(f"{count} entries", div_sub))
    story.append(PageBreak())
    return story

def make_item_block(item):
    """Compact item block â no forced PageBreak, wrapped in KeepTogether."""
    name = item['name']
    section = item['section']
    key = ALIAS.get(name, name)
    rich = MASTER.get(key, {})
    sc = section_color(section)

    inner = []

    # ââ compact header bar ââ
    header_text = (
        f"<font size=7 color='#dddddd'>{section}</font>  "
        f"<font size=13 color='white'><b>{name}</b></font>"
    )
    hdr_style = ParagraphStyle('Hdr', parent=styles['Normal'], fontSize=13, leading=16,
        textColor=colors.white)
    hdr_para = Paragraph(header_text, hdr_style)
    hdr_table = Table([[hdr_para]], colWidths=[W - 1.5*inch])
    hdr_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), sc),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    inner.append(hdr_table)
    inner.append(Spacer(1, 0.06*inch))

    # ââ image(s) + description ââ
    img_obj  = b64_to_image(item.get('img_b64', ''),  max_w=1.2*inch, max_h=1.2*inch)
    img_obj2 = b64_to_image(item.get('img_b64_2', ''), max_w=1.2*inch, max_h=1.2*inch)
    desc_text = rich.get('description') or item.get('description') or ''
    desc_para = Paragraph(desc_text, style_body)

    if img_obj and img_obj2:
        # Two photos side by side, description to the right
        img_col_w = 1.3*inch
        gap = 0.08*inch
        desc_w = W - 1.5*inch - 2*img_col_w - 2*gap
        content_table = Table(
            [[img_obj, img_obj2, desc_para]],
            colWidths=[img_col_w, img_col_w, desc_w]
        )
        content_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING',   (0,0), (0,-1), 0),
            ('RIGHTPADDING',  (0,0), (0,-1), int(gap)),
            ('LEFTPADDING',   (1,0), (1,-1), 0),
            ('RIGHTPADDING',  (1,0), (1,-1), int(gap)),
            ('LEFTPADDING',   (2,0), (2,-1), 4),
            ('TOPPADDING',    (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        inner.append(content_table)
    elif img_obj:
        content_table = Table(
            [[img_obj, desc_para]],
            colWidths=[1.45*inch, W - 1.5*inch - 1.45*inch - 0.15*inch]
        )
        content_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING',   (0,0), (0,-1), 0),
            ('RIGHTPADDING',  (0,0), (0,-1), 8),
            ('LEFTPADDING',   (1,0), (1,-1), 4),
            ('TOPPADDING',    (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        inner.append(content_table)
    else:
        inner.append(desc_para)

    # ââ utility ââ
    utility = rich.get('utility', '')
    if utility:
        util_hdr = ParagraphStyle('UH', parent=styles['Normal'],
            fontSize=8.5, fontName='Helvetica-Bold', textColor=sc, spaceBefore=3, spaceAfter=1)
        inner.append(Paragraph("â¶ Utility & Value", util_hdr))
        inner.append(Paragraph(utility, style_utility))

    # ââ key facts ââ
    facts = rich.get('facts') or item.get('facts') or []
    if facts:
        inner.append(Paragraph("Key Facts", style_fact_header))
        inner.append(HRFlowable(width='100%', thickness=0.4,
            color=colors.HexColor('#bbbbbb'), spaceAfter=1))
        for f in facts:
            inner.append(Paragraph(f"â¢ {f}", style_fact))

    # Light separator between items on the same page
    inner.append(Spacer(1, 0.08*inch))
    inner.append(HRFlowable(width='100%', thickness=0.3,
        color=colors.HexColor('#dddddd'), spaceAfter=0))
    inner.append(Spacer(1, 0.10*inch))

    # Wrap in KeepTogether so an item doesn't split across pages mid-header
    return KeepTogether(inner)


# ââ assemble document ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
out_path = SCRATCHPAD / 'Missouri_Field_Guide_v5.pdf'
doc = SimpleDocTemplate(
    str(out_path),
    pagesize=letter,
    leftMargin=0.65*inch,
    rightMargin=0.65*inch,
    topMargin=0.5*inch,
    bottomMargin=0.5*inch,
)

story = []
story.extend(make_cover())

# Section order with Fish inserted after Wildlife & Animals
sections_order = [
    'Wildflowers & Plants',
    'Fungi & Mushrooms',
    'Wildlife & Animals',
    'Fish',
    'Animal Tracking',
    'Trees',
    'Danger Zone',
]

by_section = OrderedDict()
for s in sections_order:
    by_section[s] = []

for item in non_fish_items:
    placed = False
    for s in sections_order:
        if s in item['section']:
            by_section[s].append(item)
            placed = True
            break
    if not placed:
        by_section.setdefault(item['section'], []).append(item)

# Add fish items (they were tagged as Wildlife & Animals in the JSON)
for item in fish_items:
    by_section['Fish'].append(item)

# Sort all sections alphabetically
for s in by_section:
    by_section[s].sort(key=lambda x: x['name'].lower())

for section_name, section_items in by_section.items():
    if not section_items:
        continue
    story.extend(make_section_divider(section_name, len(section_items)))
    for item in section_items:
        story.append(make_item_block(item))

print("Building PDF v5...")
doc.build(story)
size_mb = out_path.stat().st_size / 1024 / 1024
print(f"Done! {out_path} â {size_mb:.2f} MB")
