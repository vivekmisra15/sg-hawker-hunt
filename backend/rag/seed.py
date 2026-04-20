"""
One-time seed script for the ChromaDB hawker knowledge base.
Run from backend/: python3 -m rag.seed
"""
import os
import sys

# Ensure backend/ is on path when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rag.vector_store import VectorStore

STALLS = [
    # ── Chicken Rice ──────────────────────────────────────────────────────────
    {
        "id": "tian_tian_chicken_rice",
        "text": (
            "Tian Tian Hainanese Chicken Rice at Maxwell Food Centre stall #01-10. "
            "Famous for silky poached chicken with intensely fragrant rice cooked in chicken fat and pandan. "
            "Michelin Bib Gourmand 2025. Consistently ranked Singapore's best chicken rice. "
            "Expect queues of 20-40 minutes at lunch. Best visited before 11:30am or after 2pm. "
            "Cash only. Price S$5-7 per plate."
        ),
        "metadata": {
            "centre_name": "Maxwell Food Centre",
            "stall_name": "Tian Tian Hainanese Chicken Rice",
            "cuisine": "chicken rice",
            "region": "central",
            "tags": ["chicken rice", "hainanese", "poached chicken", "michelin", "maxwell"],
            "is_michelin": True,
            "is_halal": False,
            "best_time": "Before 11:30am or after 2pm",
            "avoid_time": "12pm-2pm (huge queues)",
            "price_range": "S$5-7",
        },
    },
    # ── Laksa ─────────────────────────────────────────────────────────────────
    {
        "id": "katong_laksa_east_coast",
        "text": (
            "328 Katong Laksa at East Coast Road. "
            "Thick spicy coconut milk broth with plump shrimp, cockles, and fish cake. "
            "Signature feature: noodles are cut short so you eat with just a spoon. "
            "Michelin Bib Gourmand 2025. Famous worldwide — queues form daily. "
            "Best time: early morning before 10am or weekday afternoons. "
            "Price S$6-9 per bowl."
        ),
        "metadata": {
            "centre_name": "East Coast Road",
            "stall_name": "328 Katong Laksa",
            "cuisine": "laksa",
            "region": "east",
            "tags": ["laksa", "coconut milk", "seafood", "spicy", "michelin", "katong"],
            "is_michelin": True,
            "is_halal": False,
            "best_time": "Before 10am or weekday afternoon",
            "avoid_time": "Weekends 11am-1pm",
            "price_range": "S$6-9",
        },
    },
    {
        "id": "old_airport_road_rojak",
        "text": (
            "Sungei Road Laksa at Jalan Berseh. "
            "Traditional laksa cooked over charcoal fire in an old-school earthen pot. "
            "Michelin Bib Gourmand 2025. Tiny portions, intensely aromatic broth. "
            "Only open until sold out — usually by 11am. "
            "One of Singapore's oldest laksa stalls, operating since the 1960s. "
            "Price S$3-4."
        ),
        "metadata": {
            "centre_name": "Jalan Berseh",
            "stall_name": "Sungei Road Laksa",
            "cuisine": "laksa",
            "region": "central",
            "tags": ["laksa", "charcoal", "traditional", "old school", "michelin", "cheap"],
            "is_michelin": True,
            "is_halal": False,
            "best_time": "Open from 8:30am, sold out by 11am",
            "avoid_time": "After 11am",
            "price_range": "S$3-4",
        },
    },
    {
        "id": "yishun_laksa",
        "text": (
            "Yishun Central Laksa at Yishun Central Food Centre. "
            "Creamy coconut laksa with vermicelli, tau pok, and fresh cockles. "
            "A neighbourhood favourite in the north — much shorter queues than tourist spots. "
            "Open for breakfast and lunch. Good value at S$4-5 per bowl."
        ),
        "metadata": {
            "centre_name": "Yishun Central FC",
            "stall_name": "Yishun Central Laksa",
            "cuisine": "laksa",
            "region": "north",
            "tags": ["laksa", "coconut milk", "north singapore", "yishun", "affordable"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-1pm",
            "avoid_time": "After 2pm — may close",
            "price_range": "S$4-5",
        },
    },
    # ── Char Kway Teow ────────────────────────────────────────────────────────
    {
        "id": "hill_street_char_kway_teow",
        "text": (
            "Hill Street Fried Kway Teow at Chinatown Complex. "
            "Dry-fried flat rice noodles with Chinese sausage, egg, beansprouts, and chilli. "
            "Wok hei (breath of the wok) is exceptional — high-heat charred fragrance. "
            "Michelin Bib Gourmand 2025. Opens only until sold out — usually by 2pm. "
            "Best time: 10am-12pm. Price S$4-6."
        ),
        "metadata": {
            "centre_name": "Chinatown Complex",
            "stall_name": "Hill Street Fried Kway Teow",
            "cuisine": "char kway teow",
            "region": "central",
            "tags": ["char kway teow", "fried noodles", "wok hei", "michelin", "chinatown"],
            "is_michelin": True,
            "is_halal": False,
            "best_time": "10am-12pm, sells out by 2pm",
            "avoid_time": "After 2pm — likely sold out",
            "price_range": "S$4-6",
        },
    },
    {
        "id": "outram_park_fried_kway_teow",
        "text": (
            "Outram Park Fried Kway Teow Mee at Hong Lim Market & Food Centre stall #02-18. "
            "Classic Teochew char kway teow — flat rice noodles fried with cockles, egg, beansprouts, "
            "and Chinese sausage. Strong wok hei, slightly sweet-savoury. "
            "Michelin Bib Gourmand 2025. Queue is usually 20-30 minutes at lunch. "
            "Price S$3-5."
        ),
        "metadata": {
            "centre_name": "Hong Lim Market & Food Centre",
            "stall_name": "Outram Park Fried Kway Teow",
            "cuisine": "char kway teow",
            "region": "central",
            "tags": ["char kway teow", "wok hei", "cockles", "outram", "hong lim", "michelin"],
            "is_michelin": True,
            "is_halal": False,
            "best_time": "11am-2pm",
            "avoid_time": "Weekend peak — very long queues",
            "price_range": "S$3-5",
        },
    },
    {
        "id": "zion_road_char_kway_teow",
        "text": (
            "No. 18 Zion Road Fried Kway Teow at Zion Riverside Food Centre. "
            "Wet-style char kway teow with prawns, cockles, and a luscious dark soy glaze. "
            "Operated by a third-generation hawker family. Significantly shorter queues than CBD outlets. "
            "Recommended by food critics as one of the most underrated char kway teow stalls. "
            "Price S$4-6."
        ),
        "metadata": {
            "centre_name": "Zion Riverside FC",
            "stall_name": "No. 18 Zion Road Fried Kway Teow",
            "cuisine": "char kway teow",
            "region": "central",
            "tags": ["char kway teow", "wok hei", "zion road", "wet style", "central singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-3pm",
            "avoid_time": "After 4pm — may sell out",
            "price_range": "S$4-6",
        },
    },
    # ── Bak Chor Mee ─────────────────────────────────────────────────────────
    {
        "id": "tai_hwa_bak_chor_mee",
        "text": (
            "Tai Hwa Pork Noodle at Crawford Lane. "
            "Minced pork noodles with vinegar-marinated lean pork, liver, and meatballs. "
            "Michelin Star (ONE star) — only hawker stall in Singapore with a Michelin star. "
            "Queues routinely exceed 90 minutes. Go on weekday mornings. "
            "Price S$8-12. Cash only."
        ),
        "metadata": {
            "centre_name": "Hill Street Tai Hwa Pork Noodle",
            "stall_name": "Tai Hwa Pork Noodle",
            "cuisine": "bak chor mee",
            "region": "central",
            "tags": ["bak chor mee", "minced pork noodles", "michelin star", "vinegar", "meatball"],
            "is_michelin": True,
            "is_halal": False,
            "best_time": "Weekday 9am-11am",
            "avoid_time": "Weekends — 90+ min queues",
            "price_range": "S$8-12",
        },
    },
    # ── Bak Kut Teh ──────────────────────────────────────────────────────────
    {
        "id": "song_fa_bak_kut_teh_clementi",
        "text": (
            "Song Fa Bak Kut Teh at Clementi 448 Market & Food Centre, West Singapore. "
            "Peppery Teochew-style pork rib soup with tender ribs in a clear, intensely peppery broth. "
            "One of Singapore's most popular bak kut teh outlets — the west branch is less crowded than CBD. "
            "Pairs well with you tiao (fried dough) dipped into the broth. "
            "Open for breakfast and lunch. Price S$8-14."
        ),
        "metadata": {
            "centre_name": "Clementi 448 Market & Food Centre",
            "stall_name": "Song Fa Bak Kut Teh",
            "cuisine": "bak kut teh",
            "region": "west",
            "tags": ["bak kut teh", "pork rib soup", "teochew", "peppery", "west singapore", "clementi"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-2pm",
            "avoid_time": "After 3pm — may close",
            "price_range": "S$8-14",
        },
    },
    {
        "id": "ng_ah_sio_bak_kut_teh_rangoon",
        "text": (
            "Ng Ah Sio Bak Kut Teh at Rangoon Road, Farrer Park. "
            "Strong peppery pork rib soup — signature dark, deeply spiced broth. "
            "A Central Singapore institution open since 1977. The broth is richer and darker than most. "
            "Popular with early morning crowds and supper diners. "
            "Price S$9-15."
        ),
        "metadata": {
            "centre_name": "Rangoon Road",
            "stall_name": "Ng Ah Sio Bak Kut Teh",
            "cuisine": "bak kut teh",
            "region": "central",
            "tags": ["bak kut teh", "pork rib soup", "peppery", "central singapore", "farrer park", "rangoon"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-10am or 9pm-midnight",
            "avoid_time": "Midday peak",
            "price_range": "S$9-15",
        },
    },
    {
        "id": "founder_bak_kut_teh_rangoon",
        "text": (
            "Founder Bak Kut Teh at Rangoon Road. "
            "Traditional peppery bak kut teh with spare ribs, belly pork, and offal options. "
            "Family-run since 1978 — the pepper level is adjustable and very customisable. "
            "Often cited as one of the best bak kut teh in Singapore. "
            "Price S$9-14."
        ),
        "metadata": {
            "centre_name": "Rangoon Road",
            "stall_name": "Founder Bak Kut Teh",
            "cuisine": "bak kut teh",
            "region": "central",
            "tags": ["bak kut teh", "pork ribs", "peppery", "traditional", "rangoon road"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7:30am-9:30pm",
            "avoid_time": "No particular bad time",
            "price_range": "S$9-14",
        },
    },
    {
        "id": "jurong_east_bak_kut_teh",
        "text": (
            "Jurong East Bak Kut Teh at Jurong East Food Centre. "
            "Herbal-style bak kut teh with a darker, more medicinal broth of dang gui, wolfberries, and garlic. "
            "A west Singapore staple for workers in the Jurong industrial belt. "
            "Good for those who prefer the herbal Hokkien style over the peppery Teochew style. "
            "Price S$8-13."
        ),
        "metadata": {
            "centre_name": "Jurong East FC",
            "stall_name": "Jurong East Bak Kut Teh",
            "cuisine": "bak kut teh",
            "region": "west",
            "tags": ["bak kut teh", "herbal", "hokkien style", "jurong", "west singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-2pm",
            "avoid_time": "After 3pm — may close",
            "price_range": "S$8-13",
        },
    },
    {
        "id": "punggol_bak_kut_teh",
        "text": (
            "Punggol Bak Kut Teh at Punggol Plaza Food Court, North-East Singapore. "
            "Peppery Teochew bak kut teh with fall-off-the-bone ribs and a clear, bold broth. "
            "Popular with Punggol and Sengkang residents — no tourist crowds. "
            "Also serves dry bak kut teh with dark soy and salted vegetables. "
            "Price S$8-13."
        ),
        "metadata": {
            "centre_name": "Punggol Plaza",
            "stall_name": "Punggol Bak Kut Teh",
            "cuisine": "bak kut teh",
            "region": "north_east",
            "tags": ["bak kut teh", "pork rib soup", "teochew", "punggol", "north east singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-2pm",
            "avoid_time": "After 3pm — may close",
            "price_range": "S$8-13",
        },
    },
    # ── Hokkien Mee ──────────────────────────────────────────────────────────
    {
        "id": "newton_hokkien_mee",
        "text": (
            "Hokkien Mee stall at Newton Food Centre. "
            "Wok-fried yellow noodles and rice vermicelli in prawn and pork broth, with sambal belacan. "
            "Rich smoky wok hei flavour. Evenings only. "
            "Best enjoyed late evening with the whole Newton hawker atmosphere. "
            "Price S$6-10."
        ),
        "metadata": {
            "centre_name": "Newton Food Centre",
            "stall_name": "Newton Hokkien Mee",
            "cuisine": "hokkien mee",
            "region": "central",
            "tags": ["hokkien mee", "wok hei", "prawn broth", "evening", "newton"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7pm-10pm",
            "avoid_time": "Daytime — stall not open",
            "price_range": "S$6-10",
        },
    },
    {
        "id": "abc_brickworks_hokkien_mee",
        "text": (
            "Tiong Bahru Yi Sheng Fried Hokkien Prawn Mee at ABC Brickworks Food Centre, Queenstown. "
            "Wok-fried yellow noodles and bee hoon in prawn and lard broth with squid and sambal. "
            "Strong wok hei, generous prawn flavour. One of the best Hokkien mee stalls in west Singapore. "
            "Queue expected at dinner. "
            "Price S$5-10."
        ),
        "metadata": {
            "centre_name": "ABC Brickworks Food Centre",
            "stall_name": "Tiong Bahru Yi Sheng Fried Hokkien Prawn Mee",
            "cuisine": "hokkien mee",
            "region": "west",
            "tags": ["hokkien mee", "wok hei", "prawn", "west singapore", "queenstown", "abc brickworks"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "5pm-9pm",
            "avoid_time": "Daytime — stall opens evenings only",
            "price_range": "S$5-10",
        },
    },
    {
        "id": "geylang_hokkien_mee_supper",
        "text": (
            "Geylang Lor 29 Hokkien Mee at Geylang Lorong 29 supper street. "
            "Charcoal-fired Hokkien prawn mee — one of the last stalls still using charcoal for the wok. "
            "The smoky, prawn-rich flavour is unmistakable. Open for supper only from 9pm. "
            "A legendary late-night destination in Singapore's east. Price S$6-12."
        ),
        "metadata": {
            "centre_name": "Geylang Lor 29",
            "stall_name": "Geylang Lor 29 Hokkien Mee",
            "cuisine": "hokkien mee",
            "region": "east",
            "tags": ["hokkien mee", "charcoal", "wok hei", "supper", "late night", "geylang", "east singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "9pm-1am",
            "avoid_time": "Daytime — opens only for supper",
            "price_range": "S$6-12",
        },
    },
    # ── Prawn Noodles ────────────────────────────────────────────────────────
    {
        "id": "tiong_bahru_min_nan_pork_ribs_prawn_noodle",
        "text": (
            "Min Nan Pork Ribs Prawn Noodle at Tiong Bahru Market. "
            "Rich prawn bisque broth with tender braised pork ribs and yellow noodles. "
            "Stall has been operating for over 40 years. One of Tiong Bahru Market's most beloved stalls. "
            "Opens from 7:30am. Queue expected on weekends. "
            "Price S$5-8."
        ),
        "metadata": {
            "centre_name": "Tiong Bahru Market",
            "stall_name": "Min Nan Pork Ribs Prawn Noodle",
            "cuisine": "prawn noodles",
            "region": "central",
            "tags": ["prawn noodles", "pork ribs", "hokkien", "traditional", "tiong bahru"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7:30am-11am on weekdays",
            "avoid_time": "Weekend mornings — long queues",
            "price_range": "S$5-8",
        },
    },
    {
        "id": "whampoa_prawn_noodles",
        "text": (
            "545 Whampoa Prawn Noodles at Whampoa Makan Place. "
            "Prawn noodle soup or dry — rich intense prawn bisque broth, fresh prawns, "
            "pork ribs, and pork slices. One of the most celebrated prawn noodle stalls in Singapore. "
            "Queue 30+ minutes on weekends. "
            "Price S$6-12."
        ),
        "metadata": {
            "centre_name": "Whampoa Makan Place",
            "stall_name": "545 Whampoa Prawn Noodles",
            "cuisine": "prawn noodles",
            "region": "central",
            "tags": ["prawn noodles", "hae mee", "pork ribs", "whampoa", "intense broth"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "8am-1pm",
            "avoid_time": "Weekends — extremely long queue",
            "price_range": "S$6-12",
        },
    },
    {
        "id": "amk_628_prawn_noodles",
        "text": (
            "Ang Mo Kio 628 Market Prawn Noodles at AMK 628 Market & Food Centre. "
            "Dark dry-style prawn noodles with sambal belacan, and a separate prawn broth soup on the side. "
            "Neighbourhood gem in the north — consistently shorter queues than city-centre prawn noodle stalls. "
            "Popular with AMK residents for breakfast and lunch. Price S$5-8."
        ),
        "metadata": {
            "centre_name": "AMK 628 Market & FC",
            "stall_name": "AMK 628 Prawn Noodles",
            "cuisine": "prawn noodles",
            "region": "north",
            "tags": ["prawn noodles", "hae mee", "ang mo kio", "north singapore", "dry style"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-1pm",
            "avoid_time": "After 2pm — may sell out",
            "price_range": "S$5-8",
        },
    },
    {
        "id": "jurong_west_fish_soup",
        "text": (
            "Jurong West Market Fish Soup at Jurong West Street 52 Market & Food Centre. "
            "Clear, sweet fish broth with fresh sliced batang fish, silken tofu, and tomatoes. "
            "Light and healthy — a favourite for those avoiding heavy fried food. "
            "Vegetarian-friendly (fish-free) options sometimes available. "
            "Price S$5-8."
        ),
        "metadata": {
            "centre_name": "Jurong West St 52 Market & FC",
            "stall_name": "Jurong West Market Fish Soup",
            "cuisine": "fish soup",
            "region": "west",
            "tags": ["fish soup", "clear broth", "healthy", "seafood", "jurong west", "west singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-8pm",
            "avoid_time": "No bad time",
            "price_range": "S$5-8",
        },
    },
    # ── Nasi Lemak ────────────────────────────────────────────────────────────
    {
        "id": "hong_lim_nasi_lemak",
        "text": (
            "Mizzy Corner Nasi Lemak at Toa Payoh West Market & Food Centre. "
            "Fragrant coconut rice served with crispy fried chicken, sambal, cucumber, and anchovies. "
            "Halal certified. Famous for their extra-crispy fried chicken and fiery sambal. "
            "Best time: breakfast from 7am. Sells out by 11am most days. "
            "Price S$4-8."
        ),
        "metadata": {
            "centre_name": "Toa Payoh West Market & FC",
            "stall_name": "Mizzy Corner Nasi Lemak",
            "cuisine": "nasi lemak",
            "region": "central",
            "tags": ["nasi lemak", "coconut rice", "halal", "malay food", "toa payoh"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "7am-10am (breakfast rush)",
            "avoid_time": "After 11am — may sell out",
            "price_range": "S$4-8",
        },
    },
    {
        "id": "adam_road_nasi_lemak",
        "text": (
            "Selera Rasa Nasi Lemak at Adam Road Food Centre stall #02-02. "
            "Michelin Bib Gourmand 2025. Coconut rice with fried chicken wing, sambal, and otah. "
            "Halal certified. One of Singapore's most famous nasi lemak stalls — the chicken wings are exceptional. "
            "Opens daily from 7am. Long queues on weekend mornings. Price S$5-9."
        ),
        "metadata": {
            "centre_name": "Adam Road Food Centre",
            "stall_name": "Selera Rasa Nasi Lemak",
            "cuisine": "nasi lemak",
            "region": "central",
            "tags": ["nasi lemak", "coconut rice", "halal", "malay food", "michelin", "adam road", "chicken wing"],
            "is_michelin": True,
            "is_halal": True,
            "best_time": "7am-10am on weekdays",
            "avoid_time": "Weekend mornings — very long queue",
            "price_range": "S$5-9",
        },
    },
    {
        "id": "marine_parade_nasi_lemak",
        "text": (
            "Marine Parade Nasi Lemak at Marine Parade Food Centre. "
            "Halal-certified coconut rice set with crispy ikan bilis, peanuts, egg, and spicy sambal. "
            "A beloved breakfast staple for East Singapore residents near Katong. "
            "Very affordable and consistently good. Price S$3-5."
        ),
        "metadata": {
            "centre_name": "Marine Parade FC",
            "stall_name": "Marine Parade Nasi Lemak",
            "cuisine": "nasi lemak",
            "region": "east",
            "tags": ["nasi lemak", "coconut rice", "halal", "malay food", "marine parade", "east singapore", "breakfast"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "7am-11am",
            "avoid_time": "After 12pm — sells out",
            "price_range": "S$3-5",
        },
    },
    # ── Roti Prata ────────────────────────────────────────────────────────────
    {
        "id": "adam_road_roti_prata",
        "text": (
            "Adam Road Prata House at Adam Road Food Centre. "
            "Crispy layered roti prata with dal and fish curry dipping sauces. "
            "Also serves tissue prata, egg prata, and coin prata. "
            "Halal certified. Open 24 hours. Popular after-midnight supper spot. "
            "Price S$1.20-4 per prata."
        ),
        "metadata": {
            "centre_name": "Adam Road Food Centre",
            "stall_name": "Adam Road Prata House",
            "cuisine": "roti prata",
            "region": "central",
            "tags": ["roti prata", "indian", "halal", "supper", "24 hours", "adam road"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "Any time — open 24h",
            "avoid_time": "No bad time",
            "price_range": "S$1.20-4",
        },
    },
    {
        "id": "serangoon_roti_prata",
        "text": (
            "Serangoon Garden Roti Prata at Chomp Chomp Food Centre area. "
            "Fluffy thick prata with a layered, slightly charred exterior and soft interior. "
            "Halal certified. Available with egg, cheese, onion, or plain. "
            "A North-East Singapore institution popular with Serangoon Gardens residents. "
            "Price S$1.50-4.50."
        ),
        "metadata": {
            "centre_name": "Chomp Chomp FC",
            "stall_name": "Serangoon Garden Roti Prata",
            "cuisine": "roti prata",
            "region": "north_east",
            "tags": ["roti prata", "indian", "halal", "serangoon", "north east singapore"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "7am-10pm",
            "avoid_time": "No bad time",
            "price_range": "S$1.50-4.50",
        },
    },
    # ── Satay ─────────────────────────────────────────────────────────────────
    {
        "id": "lau_pa_sat_satay",
        "text": (
            "Satay Street at Lau Pa Sat Festival Market, Boon Tat Street. "
            "Evening satay street with dozens of charcoal-grilled satay stalls. "
            "Chicken, beef, mutton, and prawn satay with peanut sauce and ketupat. "
            "Most stalls halal. Vibrant outdoor atmosphere in the CBD. "
            "Best time: 7pm-11pm. Avoid during rain (outdoor only). "
            "Price S$0.70-1.00 per stick."
        ),
        "metadata": {
            "centre_name": "Lau Pa Sat",
            "stall_name": "Satay Street Lau Pa Sat",
            "cuisine": "satay",
            "region": "central",
            "tags": ["satay", "grilled", "halal", "outdoor", "evening", "CBD", "lau pa sat"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "7pm-10pm",
            "avoid_time": "Rainy evenings (fully outdoor)",
            "price_range": "S$0.70-1.00 per stick",
        },
    },
    {
        "id": "east_coast_lagoon_satay",
        "text": (
            "East Coast Lagoon Food Village Satay at East Coast Lagoon, East Singapore. "
            "Charcoal-grilled satay on skewers — chicken, beef, and mutton with thick peanut dipping sauce. "
            "Halal certified. Outdoor dining beside the sea breeze at East Coast Park. "
            "Evening only; atmospheric and relaxed. Price S$0.80-1.00 per stick."
        ),
        "metadata": {
            "centre_name": "East Coast Lagoon FV",
            "stall_name": "East Coast Lagoon Satay",
            "cuisine": "satay",
            "region": "east",
            "tags": ["satay", "grilled", "halal", "outdoor", "east coast", "east singapore", "evening"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "5pm-10pm",
            "avoid_time": "Rainy evenings (outdoor setting)",
            "price_range": "S$0.80-1.00 per stick",
        },
    },
    # ── Seafood ───────────────────────────────────────────────────────────────
    {
        "id": "alliance_seafood_newton",
        "text": (
            "Alliance Seafood at Newton Food Centre. "
            "Chilli crab, black pepper crab, butter prawns, and BBQ stingray. "
            "One of Newton's most popular seafood stalls — expect tourist prices. "
            "Open evenings only. Best for outdoor dining when weather is clear. "
            "Halal certified by MUIS. Price S$25-60 per dish."
        ),
        "metadata": {
            "centre_name": "Newton Food Centre",
            "stall_name": "Alliance Seafood",
            "cuisine": "seafood",
            "region": "central",
            "tags": ["chilli crab", "seafood", "BBQ", "outdoor", "newton", "halal"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "6pm-9pm on clear evenings",
            "avoid_time": "Rainy nights (outdoor seating)",
            "price_range": "S$25-60",
        },
    },
    {
        "id": "marine_parade_fish_head_curry",
        "text": (
            "Marine Parade Fish Head Curry at Marine Parade Food Centre. "
            "Rich, tangy Indian-style curry with a whole fish head, eggplant, lady finger, and tomatoes. "
            "A Singaporean comfort classic — the curry is aromatic with fenugreek and tamarind. "
            "Best shared between two to three people. Good for a filling dinner. Price S$18-28 per fish head."
        ),
        "metadata": {
            "centre_name": "Marine Parade FC",
            "stall_name": "Marine Parade Fish Head Curry",
            "cuisine": "fish head curry",
            "region": "east",
            "tags": ["fish head curry", "indian", "seafood", "sharing dish", "marine parade", "east singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-8pm",
            "avoid_time": "No bad time",
            "price_range": "S$18-28",
        },
    },
    # ── BBQ Chicken Wings ─────────────────────────────────────────────────────
    {
        "id": "chomp_chomp_bbq_chicken_wing",
        "text": (
            "BBQ Chicken Wings at Chomp Chomp Food Centre, Serangoon Gardens. "
            "Charcoal-grilled chicken wings marinated in a sweet-savoury soy glaze. "
            "A Chomp Chomp institution — the wings are the reason people drive to Serangoon. "
            "Best enjoyed with a cold beer. Open evenings only from 6pm. "
            "Price S$2-3 per wing."
        ),
        "metadata": {
            "centre_name": "Chomp Chomp Food Centre",
            "stall_name": "Chomp Chomp BBQ Chicken Wings",
            "cuisine": "BBQ chicken",
            "region": "north_east",
            "tags": ["BBQ", "chicken wings", "charcoal", "evening", "supper", "serangoon", "chomp chomp"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7pm-10pm",
            "avoid_time": "Rainy nights (outdoor centre)",
            "price_range": "S$2-3 per wing",
        },
    },
    {
        "id": "bedok_85_bbq_wings",
        "text": (
            "Bedok 85 BBQ Chicken Wings at Bedok 85 Fengshan Food Centre. "
            "Charcoal-grilled chicken wings with a sticky, smoky char and tender meat inside. "
            "Part of Bedok 85's famous supper scene — pair with frog porridge or satay bee hoon. "
            "Opens from 6pm, peak crowds from 8pm-midnight. Price S$2-3 per wing."
        ),
        "metadata": {
            "centre_name": "Bedok 85 Fengshan FC",
            "stall_name": "Bedok 85 BBQ Chicken Wings",
            "cuisine": "BBQ chicken",
            "region": "east",
            "tags": ["BBQ", "chicken wings", "charcoal", "supper", "bedok", "east singapore", "late night"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "8pm-midnight (supper)",
            "avoid_time": "Daytime — stall not open",
            "price_range": "S$2-3 per wing",
        },
    },
    {
        "id": "yishun_925_chicken_wings",
        "text": (
            "Yishun 925 Chicken Wings at Yishun Park Hawker Centre. "
            "Crispy deep-fried then charcoal-grilled chicken wings with housemade chilli sauce. "
            "One of the north's most talked-about chicken wing stalls — people travel from other areas to eat here. "
            "Opens for lunch and dinner. Price S$2-3 per wing."
        ),
        "metadata": {
            "centre_name": "Yishun Park Hawker Centre",
            "stall_name": "Yishun 925 Chicken Wings",
            "cuisine": "BBQ chicken",
            "region": "north",
            "tags": ["chicken wings", "charcoal", "crispy", "yishun", "north singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-9pm",
            "avoid_time": "No bad time",
            "price_range": "S$2-3 per wing",
        },
    },
    # ── Claypot Rice ──────────────────────────────────────────────────────────
    {
        "id": "lian_he_ben_ji_claypot_rice",
        "text": (
            "Lian He Ben Ji Claypot Rice at Chinatown Complex Market & Food Centre, stall #02-198/200. "
            "Claypot rice cooked over charcoal with Chinese sausage, waxed duck, and salted fish. "
            "Michelin Bib Gourmand 2025. The scorched rice crust at the bottom is the prized part. "
            "Wait time 30-45 minutes as each pot is made to order. "
            "Price S$8-15."
        ),
        "metadata": {
            "centre_name": "Chinatown Complex Market & Food Centre",
            "stall_name": "Lian He Ben Ji Claypot Rice",
            "cuisine": "claypot rice",
            "region": "central",
            "tags": ["claypot rice", "charcoal", "waxed meat", "chinese sausage", "chinatown", "michelin"],
            "is_michelin": True,
            "is_halal": False,
            "best_time": "5pm-10pm (dinner)",
            "avoid_time": "Lunch — opens for dinner only",
            "price_range": "S$8-15",
        },
    },
    # ── Wonton Mee ────────────────────────────────────────────────────────────
    {
        "id": "chinatown_complex_wanton_mee",
        "text": (
            "Hua Kee Hougang Wanton Noodle at Chinatown Complex. "
            "Springy egg noodles in a flavourful char siu pork and wanton soup. "
            "Char siu is caramelised and charred at edges — sweet and savoury. "
            "Opens from 9am. Popular with office crowd at lunch. "
            "Price S$4-6."
        ),
        "metadata": {
            "centre_name": "Chinatown Complex",
            "stall_name": "Hua Kee Hougang Wanton Noodle",
            "cuisine": "wonton mee",
            "region": "central",
            "tags": ["wonton mee", "char siu", "egg noodles", "chinatown", "central singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "9am-1pm",
            "avoid_time": "After 3pm — may be closed",
            "price_range": "S$4-6",
        },
    },
    {
        "id": "tampines_round_wanton_mee",
        "text": (
            "Tampines Round Market Wanton Mee at Tampines Round Market & Food Centre. "
            "Dry wanton noodles tossed in dark soy, chilli, and lard croutons with BBQ pork and dumplings. "
            "A beloved East Singapore breakfast institution — consistently long queues before 9am. "
            "Price S$3.50-5."
        ),
        "metadata": {
            "centre_name": "Tampines Round Market & FC",
            "stall_name": "Tampines Round Market Wanton Mee",
            "cuisine": "wonton mee",
            "region": "east",
            "tags": ["wonton mee", "char siu", "egg noodles", "tampines", "east singapore", "breakfast"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-11am",
            "avoid_time": "After 12pm — sells out",
            "price_range": "S$3.50-5",
        },
    },
    {
        "id": "hougang_105_wanton_mee",
        "text": (
            "Hougang 105 Wanton Noodle at Hougang Avenue 1 Market & Food Centre. "
            "Thin springy noodles with handmade wantons, crispy char siu, and a balanced dark soy sauce. "
            "Family-run stall known for consistently high quality. "
            "Popular with Hougang and Serangoon residents for breakfast. Price S$4-6."
        ),
        "metadata": {
            "centre_name": "Hougang Ave 1 FC",
            "stall_name": "Hougang 105 Wanton Noodle",
            "cuisine": "wonton mee",
            "region": "north_east",
            "tags": ["wonton mee", "char siu", "egg noodles", "hougang", "north east singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-12pm",
            "avoid_time": "After 1pm — may sell out",
            "price_range": "S$4-6",
        },
    },
    {
        "id": "woodlands_wanton_noodles",
        "text": (
            "Woodlands 888 Wanton Noodles at Woodlands 888 Plaza Food Court. "
            "Springy egg noodles with har gao-style dumplings, roasted char siu, and a tangy chilli sauce. "
            "North Singapore's go-to wanton mee — very consistent, good value for Woodlands residents. "
            "Price S$3-5."
        ),
        "metadata": {
            "centre_name": "Woodlands 888 Plaza",
            "stall_name": "Woodlands 888 Wanton Noodles",
            "cuisine": "wonton mee",
            "region": "north",
            "tags": ["wonton mee", "char siu", "dumplings", "woodlands", "north singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-12pm",
            "avoid_time": "After 2pm — may close",
            "price_range": "S$3-5",
        },
    },
    # ── Nasi Padang ───────────────────────────────────────────────────────────
    {
        "id": "geylang_serai_mee_siam",
        "text": (
            "Hajjah Mona Nasi Padang at Geylang Serai Market. "
            "Indonesian-Malay rice with a spread of curries, rendang, sayur lodeh, and ikan bilis. "
            "Halal certified. Generous portions at great value. "
            "Best time: lunch 11am-2pm. "
            "Price S$5-10 depending on dishes selected."
        ),
        "metadata": {
            "centre_name": "Geylang Serai Market",
            "stall_name": "Hajjah Mona Nasi Padang",
            "cuisine": "nasi padang",
            "region": "east",
            "tags": ["nasi padang", "malay food", "halal", "rendang", "rice", "geylang serai"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "11am-2pm",
            "avoid_time": "After 3pm — dishes may run out",
            "price_range": "S$5-10",
        },
    },
    {
        "id": "sengkang_nasi_padang",
        "text": (
            "Sengkang West Market Nasi Padang at Sengkang West Food Centre. "
            "Halal Malay rice with curry chicken, rendang daging, and sambal goreng tempeh. "
            "A neighbourhood staple for Sengkang and Punggol residents — very accessible for north-east families. "
            "Price S$4-9."
        ),
        "metadata": {
            "centre_name": "Sengkang West FC",
            "stall_name": "Sengkang FC Nasi Padang",
            "cuisine": "nasi padang",
            "region": "north_east",
            "tags": ["nasi padang", "malay food", "halal", "rendang", "sengkang", "north east singapore"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "11am-8pm",
            "avoid_time": "After 8pm — dishes run out",
            "price_range": "S$4-9",
        },
    },
    # ── Biryani / Indian ──────────────────────────────────────────────────────
    {
        "id": "tekka_biryani",
        "text": (
            "Bismillah Biryani at Tekka Centre, Little India. "
            "Fragrant basmati rice cooked with whole spices and your choice of mutton, chicken, or fish. "
            "Halal certified. One of Singapore's most famous biryani stalls — Michelin Bib Gourmand 2025. "
            "Meat is marinated overnight and slow-cooked. Queue expected at lunch. Price S$7-12."
        ),
        "metadata": {
            "centre_name": "Tekka Centre",
            "stall_name": "Bismillah Biryani",
            "cuisine": "biryani",
            "region": "central",
            "tags": ["biryani", "indian", "halal", "basmati rice", "little india", "tekka", "michelin"],
            "is_michelin": True,
            "is_halal": True,
            "best_time": "11am-2pm",
            "avoid_time": "After 3pm — may sell out",
            "price_range": "S$7-12",
        },
    },
    {
        "id": "haig_road_mee_siam",
        "text": (
            "Haig Road Market Mee Siam at Haig Road Market & Food Centre. "
            "Tangy, spicy rice vermicelli in a tamarind-prawn paste broth, topped with egg and lime. "
            "Halal certified. A classic Malay breakfast and lunch dish with a sharp, complex flavour. "
            "Very popular with East Singapore's Malay community. Price S$3.50-5."
        ),
        "metadata": {
            "centre_name": "Haig Road Market & FC",
            "stall_name": "Haig Road Market Mee Siam",
            "cuisine": "mee siam",
            "region": "east",
            "tags": ["mee siam", "malay food", "halal", "rice vermicelli", "tangy", "haig road", "east singapore"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "7am-1pm",
            "avoid_time": "After 2pm — may close",
            "price_range": "S$3.50-5",
        },
    },
    {
        "id": "geylang_serai_murtabak",
        "text": (
            "Geylang Serai Murtabak at Geylang Serai Market. "
            "Thick stuffed pancake filled with spiced minced mutton or chicken and egg. "
            "Halal certified. Served with a sweet-sour pickled onion curry dip. "
            "A Ramadan and year-round favourite at Geylang Serai. Price S$7-10."
        ),
        "metadata": {
            "centre_name": "Geylang Serai Market",
            "stall_name": "Geylang Serai Murtabak",
            "cuisine": "murtabak",
            "region": "east",
            "tags": ["murtabak", "malay food", "halal", "stuffed pancake", "geylang serai", "east singapore"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "10am-8pm",
            "avoid_time": "No bad time",
            "price_range": "S$7-10",
        },
    },
    # ── Mee Rebus ─────────────────────────────────────────────────────────────
    {
        "id": "abc_brickworks_mee_rebus",
        "text": (
            "Selera Minang Mee Rebus at ABC Brickworks Food Centre, Queenstown. "
            "Malay-style yellow noodles in a thick, sweet-savoury potato and prawn gravy, "
            "topped with bean sprouts, a boiled egg, fried shallots, and green chilli. "
            "Halal certified. A classic Malay hawker dish. "
            "Price S$3.50-5."
        ),
        "metadata": {
            "centre_name": "ABC Brickworks Food Centre",
            "stall_name": "Selera Minang",
            "cuisine": "mee rebus",
            "region": "west",
            "tags": ["mee rebus", "malay food", "halal", "yellow noodles", "west singapore", "queenstown"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "7am-2pm",
            "avoid_time": "After 3pm — may close",
            "price_range": "S$3.50-5",
        },
    },
    # ── Economy Rice / Cai Fan ────────────────────────────────────────────────
    {
        "id": "buona_vista_economy_rice",
        "text": (
            "Economy Rice at Buona Vista Market & Food Centre. "
            "Cai fan — choose from 20+ dishes over steamed white rice: braised pork, "
            "stir-fried vegetables, tofu, fried egg, and more. "
            "Budget-friendly and filling. Vegetarian options always available. "
            "Open from 7am. Price S$3-5."
        ),
        "metadata": {
            "centre_name": "Buona Vista Market & Food Centre",
            "stall_name": "Buona Vista Economy Rice",
            "cuisine": "economy rice",
            "region": "west",
            "tags": ["economy rice", "cai fan", "vegetarian", "budget", "west singapore", "buona vista"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-2pm",
            "avoid_time": "After 3pm — dishes run out",
            "price_range": "S$3-5",
        },
    },
    {
        "id": "tiong_bahru_char_siu_fan",
        "text": (
            "Tiong Bahru Market Char Siu Fan at Tiong Bahru Market. "
            "Cantonese roast meats over rice — char siu (BBQ pork), sio bak (crispy pork belly), "
            "and roast duck. The char siu has a perfect caramelised crust and tender interior. "
            "A top-rated roast meat stall in the Tiong Bahru area. Price S$5-9."
        ),
        "metadata": {
            "centre_name": "Tiong Bahru Market",
            "stall_name": "Tiong Bahru Market Char Siu Fan",
            "cuisine": "char siu rice",
            "region": "central",
            "tags": ["char siu", "roast meats", "BBQ pork", "sio bak", "tiong bahru", "central singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "10am-2pm",
            "avoid_time": "After 3pm — sells out",
            "price_range": "S$5-9",
        },
    },
    # ── Duck Rice ─────────────────────────────────────────────────────────────
    {
        "id": "lim_kee_duck_rice_clementi",
        "text": (
            "Lim Kee Duck Rice at Clementi 448 Market & Food Centre, West Singapore. "
            "Braised duck rice with tender braised duck, tau kwa, and hard-boiled egg in dark soy broth. "
            "A neighbourhood favourite in West Singapore — queue expected at lunch. "
            "Also serves duck noodles and duck porridge. "
            "Price S$4-7."
        ),
        "metadata": {
            "centre_name": "Clementi 448 Market & Food Centre",
            "stall_name": "Lim Kee Duck Rice",
            "cuisine": "duck rice",
            "region": "west",
            "tags": ["duck rice", "braised duck", "clementi", "west singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-2pm",
            "avoid_time": "After 3pm — may sell out",
            "price_range": "S$4-7",
        },
    },
    {
        "id": "old_airport_roast_meats",
        "text": (
            "Guan Chee Hong Kong Roasted Delight at Old Airport Road Food Centre. "
            "Cantonese roast specialties — crispy soy sauce chicken, char siu, and roast pork. "
            "The soy sauce chicken skin is lacquered to a perfect glossy caramel. "
            "Popular with east Singapore regulars and food hunters making the trip from across the island. "
            "Price S$5-12."
        ),
        "metadata": {
            "centre_name": "Old Airport Road FC",
            "stall_name": "Guan Chee Hong Kong Roasted Delight",
            "cuisine": "roast meats",
            "region": "east",
            "tags": ["soy sauce chicken", "roast meats", "char siu", "cantonese", "old airport road", "east singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "10am-2pm",
            "avoid_time": "After 3pm — may sell out",
            "price_range": "S$5-12",
        },
    },
    # ── Char Siu Rice ─────────────────────────────────────────────────────────
    {
        "id": "abc_brickworks_char_siu_rice",
        "text": (
            "Char Siu Rice stall at ABC Brickworks Food Centre, Queenstown. "
            "Cantonese roast meats — char siu (BBQ pork), roast duck, and sio bak (crispy pork belly). "
            "Served over steamed rice or noodles with a light soy drizzle. "
            "ABC Brickworks is one of the best food centres in the west. "
            "Price S$4-8."
        ),
        "metadata": {
            "centre_name": "ABC Brickworks Food Centre",
            "stall_name": "ABC Brickworks Char Siu Rice",
            "cuisine": "char siu rice",
            "region": "west",
            "tags": ["char siu", "roast meat", "BBQ pork", "sio bak", "queenstown", "west singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "10:30am-2pm",
            "avoid_time": "After 3pm — may sell out",
            "price_range": "S$4-8",
        },
    },
    # ── Vegetarian ────────────────────────────────────────────────────────────
    {
        "id": "kovan_thunder_tea_rice",
        "text": (
            "Kovan Melipot Thunder Tea Rice at Kovan Food Centre, North-East Singapore. "
            "Hakka lei cha — fragrant green tea soup poured over brown rice, tofu, dried shrimp, "
            "peanuts, and five stir-fried vegetables. A wholesome, nutritious vegetarian dish. "
            "Caffeine note: the soup contains green tea. Popular with health-conscious diners. "
            "Price S$5-7."
        ),
        "metadata": {
            "centre_name": "Kovan FC",
            "stall_name": "Kovan Melipot Thunder Tea Rice",
            "cuisine": "thunder tea rice",
            "region": "north_east",
            "tags": ["thunder tea rice", "hakka", "vegetarian", "healthy", "kovan", "north east singapore", "green tea"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-3pm",
            "avoid_time": "After 4pm — may close",
            "price_range": "S$5-7",
        },
    },
    {
        "id": "commonwealth_yong_tau_foo",
        "text": (
            "Commonwealth Crescent Market Yong Tau Foo at Commonwealth Crescent Market. "
            "Choose your own selection of stuffed tofu, fish paste items, vegetables, and noodles "
            "served in a clear broth or dry with sauce. A fully customisable, vegetarian-friendly dish. "
            "Good for those watching calories — light yet filling. Price S$4-7."
        ),
        "metadata": {
            "centre_name": "Commonwealth Crescent Market & FC",
            "stall_name": "Commonwealth Crescent Yong Tau Foo",
            "cuisine": "yong tau foo",
            "region": "west",
            "tags": ["yong tau foo", "vegetarian friendly", "customisable", "tofu", "light", "west singapore", "commonwealth"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-3pm",
            "avoid_time": "After 4pm — items run out",
            "price_range": "S$4-7",
        },
    },
    {
        "id": "newton_yong_tau_foo",
        "text": (
            "Newton Food Centre Yong Tau Foo at Newton FC. "
            "Colourful array of tofu, fish balls, bitter gourd, eggplant, and leafy greens "
            "stuffed with fish paste. Served in clear soup or dry with sweet sauce. "
            "Vegetarian-friendly options available. Light and filling at any time of day. "
            "Price S$5-8."
        ),
        "metadata": {
            "centre_name": "Newton FC",
            "stall_name": "Newton FC Yong Tau Foo",
            "cuisine": "yong tau foo",
            "region": "central",
            "tags": ["yong tau foo", "vegetarian friendly", "tofu", "clear soup", "newton", "light meal"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-8pm",
            "avoid_time": "No bad time",
            "price_range": "S$5-8",
        },
    },
    {
        "id": "siglap_popiah",
        "text": (
            "Siglap Market Fresh Popiah at Siglap Food Centre, East Singapore. "
            "Fresh spring rolls filled with braised bamboo shoot and turnip (jicama), "
            "prawns, egg, bean sprouts, and housemade sweet sauce. "
            "Vegetarian version available without egg and seafood. "
            "A traditional Hokkien street snack. Price S$2-4 per roll."
        ),
        "metadata": {
            "centre_name": "Siglap FC",
            "stall_name": "Siglap Market Fresh Popiah",
            "cuisine": "popiah",
            "region": "east",
            "tags": ["popiah", "spring roll", "vegetarian", "hokkien", "siglap", "east singapore", "traditional"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "10am-4pm",
            "avoid_time": "Evening — stall may close",
            "price_range": "S$2-4 per roll",
        },
    },
    {
        "id": "chinatown_popiah",
        "text": (
            "Chinatown Complex Fresh Popiah at Chinatown Complex Market & Food Centre. "
            "Fresh spring rolls stuffed with braised bangkwang (jicama), crunchy beansprouts, "
            "egg, fried shallots, and a savoury-sweet dark sauce. "
            "Vegetarian version (no egg, no shrimp) available on request. "
            "Classic hawker finger food. Price S$2-3.50 per roll."
        ),
        "metadata": {
            "centre_name": "Chinatown Complex Market & FC",
            "stall_name": "Chinatown Complex Popiah",
            "cuisine": "popiah",
            "region": "central",
            "tags": ["popiah", "spring roll", "vegetarian", "hokkien", "chinatown", "central singapore", "snack"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "10am-3pm",
            "avoid_time": "Evening — stall closes early",
            "price_range": "S$2-3.50",
        },
    },
    {
        "id": "old_airport_road_carrot_cake",
        "text": (
            "Radish Cake (Chai Tow Kway) at Old Airport Road Food Centre. "
            "Pan-fried white or black carrot cake — crispy outside, soft inside. "
            "Black version uses sweet dark soy and is more popular. "
            "Vegetarian-friendly. Opens from 7am. No seafood or meat in the base dish. "
            "Price S$3-5."
        ),
        "metadata": {
            "centre_name": "Old Airport Road Food Centre",
            "stall_name": "Old Airport Road Chai Tow Kway",
            "cuisine": "carrot cake",
            "region": "east",
            "tags": ["carrot cake", "chai tow kway", "vegetarian", "breakfast", "old airport road", "east singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-12pm",
            "avoid_time": "Evening — stall may not open",
            "price_range": "S$3-5",
        },
    },
    {
        "id": "queenstown_carrot_cake",
        "text": (
            "Queenstown Carrot Cake at Queenstown Food Centre. "
            "Crispy chai tow kway — white (no sauce) or black (dark sweet soy) style. "
            "Egg is scrambled through the radish cake for a fluffy, light texture. "
            "Vegetarian-friendly option in the west. Price S$3-5."
        ),
        "metadata": {
            "centre_name": "Queenstown FC",
            "stall_name": "Queenstown Carrot Cake",
            "cuisine": "carrot cake",
            "region": "west",
            "tags": ["carrot cake", "chai tow kway", "vegetarian", "west singapore", "queenstown"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-12pm",
            "avoid_time": "After 2pm — may close",
            "price_range": "S$3-5",
        },
    },
    {
        "id": "maxwell_tau_huay",
        "text": (
            "Maxwell Road Tau Huay at Maxwell Food Centre. "
            "Silken tofu pudding served warm or chilled with ginger syrup or pandan-flavoured sugar. "
            "Vegan and vegetarian. Light, cooling dessert — perfect after a heavy hawker meal. "
            "Very affordable at S$1.50-2.50 per bowl. A quintessential Singapore sweet treat."
        ),
        "metadata": {
            "centre_name": "Maxwell FC",
            "stall_name": "Maxwell Road Tau Huay",
            "cuisine": "tau huay",
            "region": "central",
            "tags": ["tau huay", "tofu pudding", "dessert", "vegan", "vegetarian", "maxwell", "central singapore", "sweet"],
            "is_michelin": False,
            "is_halal": True,
            "best_time": "Any time",
            "avoid_time": "No bad time",
            "price_range": "S$1.50-2.50",
        },
    },
    # ── Porridge / Congee ─────────────────────────────────────────────────────
    {
        "id": "toa_payoh_porridge",
        "text": (
            "Toa Payoh Lor 8 Market Pork Porridge at Toa Payoh Lor 8 Market & Food Centre. "
            "Smooth Teochew-style congee with minced pork, century egg, salted egg, and fish slices. "
            "Comforting and mild — very gentle on the stomach. "
            "Popular with elderly residents and those recovering from illness. Price S$4-6."
        ),
        "metadata": {
            "centre_name": "Toa Payoh Lor 8 Market & FC",
            "stall_name": "Toa Payoh Lor 8 Market Porridge",
            "cuisine": "congee",
            "region": "central",
            "tags": ["porridge", "congee", "pork porridge", "teochew", "comfort food", "toa payoh", "mild"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-1pm",
            "avoid_time": "After 2pm — may close",
            "price_range": "S$4-6",
        },
    },
    {
        "id": "bedok_85_frog_porridge",
        "text": (
            "Frog Porridge at Bedok 85 Market & Food Centre (85 Fengshan Food Centre). "
            "Smooth rice porridge with tender frog legs cooked in ginger and spring onion. "
            "A supper institution — Bedok 85 is Singapore's most famous late-night hawker centre. "
            "Open until 3am. Also serves congee, zi char dishes, and satay. "
            "Price S$8-15 per frog."
        ),
        "metadata": {
            "centre_name": "Bedok 85 Market & Food Centre",
            "stall_name": "Bedok 85 Frog Porridge",
            "cuisine": "frog porridge",
            "region": "east",
            "tags": ["frog porridge", "congee", "supper", "late night", "bedok", "east singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "8pm-2am (supper)",
            "avoid_time": "Daytime — not open",
            "price_range": "S$8-15",
        },
    },
    # ── Fish Soup ─────────────────────────────────────────────────────────────
    {
        "id": "lau_pa_sat_fish_soup",
        "text": (
            "Soon Huat Fish Soup at Lau Pa Sat Festival Market. "
            "Clear fish broth with sliced batang fish, silken tofu, and tomatoes. "
            "Light and nutritious — good for health-conscious diners. "
            "Available for both lunch and dinner. "
            "Price S$6-9."
        ),
        "metadata": {
            "centre_name": "Lau Pa Sat",
            "stall_name": "Soon Huat Fish Soup",
            "cuisine": "fish soup",
            "region": "central",
            "tags": ["fish soup", "clear broth", "healthy", "seafood", "lau pa sat", "CBD"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-8pm",
            "avoid_time": "No bad time",
            "price_range": "S$6-9",
        },
    },
    {
        "id": "katong_fish_soup",
        "text": (
            "Katong Fish Soup at Marine Parade Food Centre. "
            "Milky white fish broth (sliced batang or grouper) with glass noodles or rice. "
            "The broth is boiled to a rich, collagen-heavy stock — creamy without any dairy. "
            "Comforting and very popular with East Singapore residents. Price S$6-9."
        ),
        "metadata": {
            "centre_name": "Marine Parade FC",
            "stall_name": "Katong Fish Soup",
            "cuisine": "fish soup",
            "region": "east",
            "tags": ["fish soup", "milky broth", "seafood", "healthy", "marine parade", "katong", "east singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-8pm",
            "avoid_time": "No bad time",
            "price_range": "S$6-9",
        },
    },
    # ── Ban Mian ──────────────────────────────────────────────────────────────
    {
        "id": "amoy_street_ban_mian",
        "text": (
            "Xing Ji Rou Cuo Mian (Ban Mian) at Amoy Street Food Centre. "
            "Handmade flat noodles in a clear anchovy broth with minced pork, "
            "poached egg, and fried anchovies on top. "
            "Ban mian is a classic comfort dish — light, savoury, filling. "
            "Opens for weekday breakfast and lunch. Price S$4-6."
        ),
        "metadata": {
            "centre_name": "Amoy Street Food Centre",
            "stall_name": "Xing Ji Rou Cuo Mian",
            "cuisine": "ban mian",
            "region": "central",
            "tags": ["ban mian", "handmade noodles", "anchovy broth", "comfort food", "amoy street", "CBD"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7:30am-2pm",
            "avoid_time": "After 3pm — closed",
            "price_range": "S$4-6",
        },
    },
    # ── Oyster Omelette ───────────────────────────────────────────────────────
    {
        "id": "clementi_oyster_omelette",
        "text": (
            "Oyster Omelette (Orh Luak) at Clementi 448 Market & Food Centre. "
            "Crispy fried egg omelette with plump fresh oysters and a starchy, chewy centre. "
            "Served with tangy chilli sauce. A Hokkien favourite — the crispy-chewy texture contrast is key. "
            "Open for lunch and dinner. Price S$5-7."
        ),
        "metadata": {
            "centre_name": "Clementi 448 Market & Food Centre",
            "stall_name": "Clementi 448 Oyster Omelette",
            "cuisine": "oyster omelette",
            "region": "west",
            "tags": ["oyster omelette", "orh luak", "hokkien", "seafood", "clementi", "west singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-8pm",
            "avoid_time": "No bad time",
            "price_range": "S$5-7",
        },
    },
    # ── Curry Puff ────────────────────────────────────────────────────────────
    {
        "id": "toa_payoh_curry_puff",
        "text": (
            "Rolina Traditional Hainanese Curry Puff at Toa Payoh Central. "
            "Flaky spiral pastry filled with curried potato and chicken or black pepper chicken. "
            "The original Hainanese curry puff style — thick flaky crust, dry curry filling. "
            "Sells out fast — best to arrive before 11am. Price S$1.50-2."
        ),
        "metadata": {
            "centre_name": "Toa Payoh Central",
            "stall_name": "Rolina Traditional Hainanese Curry Puff",
            "cuisine": "curry puff",
            "region": "central",
            "tags": ["curry puff", "hainanese", "pastry", "toa payoh", "snack"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "8am-11am",
            "avoid_time": "After 11am — sells out",
            "price_range": "S$1.50-2",
        },
    },
    # ── La Mian / XLB ─────────────────────────────────────────────────────────
    {
        "id": "maxwell_zhong_guo_la_mian",
        "text": (
            "Zhong Guo La Mian Xiao Long Bao at Chinatown Complex. "
            "Hand-pulled noodles and soup dumplings (xiao long bao) made fresh daily. "
            "Michelin Bib Gourmand 2025. "
            "Best choice for a warming lunch in Chinatown. "
            "Queue is fast-moving. Price S$5-9."
        ),
        "metadata": {
            "centre_name": "Chinatown Complex",
            "stall_name": "Zhong Guo La Mian Xiao Long Bao",
            "cuisine": "la mian",
            "region": "central",
            "tags": ["la mian", "xiao long bao", "hand pulled noodles", "dumplings", "michelin", "chinatown"],
            "is_michelin": True,
            "is_halal": False,
            "best_time": "11am-1pm",
            "avoid_time": "Late evening — may close early",
            "price_range": "S$5-9",
        },
    },
    # ── Hor Fun ───────────────────────────────────────────────────────────────
    {
        "id": "sembawang_ipoh_hor_fun",
        "text": (
            "Sembawang Hills Ipoh Hor Fun at Sembawang Hills Food Centre. "
            "Flat rice noodles in a silky, soy-based sauce with poached chicken, "
            "bean sprouts, and a housemade chilli dip. "
            "Inspired by the famous Ipoh hor fun from Malaysia — lighter and more delicate than most. "
            "A north Singapore gem. Price S$5-7."
        ),
        "metadata": {
            "centre_name": "Sembawang Hills FC",
            "stall_name": "Sembawang Hills Ipoh Hor Fun",
            "cuisine": "hor fun",
            "region": "north",
            "tags": ["hor fun", "rice noodles", "ipoh style", "chicken", "sembawang", "north singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "10am-2pm",
            "avoid_time": "After 3pm — may close",
            "price_range": "S$5-7",
        },
    },
    {
        "id": "balestier_beef_hor_fun",
        "text": (
            "Balestier Road Beef Hor Fun at Balestier Road kopitiam. "
            "Cantonese-style saucy hor fun with tender beef slices and beaten egg in thick gravy. "
            "The beef is velveted and the sauce has a beautiful, silky wok hei. "
            "Lunch and dinner. A central Singapore classic. Price S$5-8."
        ),
        "metadata": {
            "centre_name": "Balestier Road",
            "stall_name": "Balestier Road Beef Hor Fun",
            "cuisine": "hor fun",
            "region": "central",
            "tags": ["hor fun", "beef", "cantonese", "wok hei", "balestier", "central singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-8pm",
            "avoid_time": "No bad time",
            "price_range": "S$5-8",
        },
    },
    # ── Kaya Toast / Breakfast ────────────────────────────────────────────────
    {
        "id": "golden_mile_kaya_toast",
        "text": (
            "Golden Mile Food Centre Kaya Toast at Golden Mile Food Centre. "
            "Traditional Hainanese breakfast set — charcoal-toasted bread with homemade pandan kaya and cold butter, "
            "soft-boiled eggs, and local kopi or teh. "
            "A quintessential Singapore breakfast experience. Vegetarian-friendly. "
            "Price S$3-6 for a set."
        ),
        "metadata": {
            "centre_name": "Golden Mile FC",
            "stall_name": "Golden Mile Kaya Toast",
            "cuisine": "kaya toast",
            "region": "central",
            "tags": ["kaya toast", "breakfast", "soft boiled egg", "kopi", "vegetarian", "hainanese", "golden mile"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-11am",
            "avoid_time": "After 12pm — breakfast set may not be available",
            "price_range": "S$3-6",
        },
    },
    # ── Chee Cheong Fun ───────────────────────────────────────────────────────
    {
        "id": "lau_pa_sat_chee_cheong_fun",
        "text": (
            "Lau Pa Sat Chee Cheong Fun at Lau Pa Sat Festival Market. "
            "Silky steamed rice rolls with sweet hoisin sauce, sesame paste, and chilli. "
            "Available plain or stuffed with char siu or prawns. "
            "A popular dim sum street snack. Vegetarian version (plain) available. "
            "Price S$3-5."
        ),
        "metadata": {
            "centre_name": "Lau Pa Sat",
            "stall_name": "Lau Pa Sat Chee Cheong Fun",
            "cuisine": "chee cheong fun",
            "region": "central",
            "tags": ["chee cheong fun", "rice rolls", "dim sum", "vegetarian friendly", "lau pa sat", "CBD", "snack"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "8am-3pm",
            "avoid_time": "Evening — may close",
            "price_range": "S$3-5",
        },
    },
    # ── Fishball Noodles / Lor Mee ────────────────────────────────────────────
    {
        "id": "amoy_street_fishball_noodles",
        "text": (
            "Fishball Story at Amoy Street Food Centre stall #02-01. "
            "Handmade fishballs and fish dumplings in clear broth or dry with mee pok. "
            "Michelin Bib Gourmand 2025. The fishballs are made fresh each morning — bouncy and light. "
            "Opens from 7:30am. Arrive early — sold out by 2pm most days. "
            "Price S$5-7."
        ),
        "metadata": {
            "centre_name": "Amoy Street Food Centre",
            "stall_name": "Fishball Story",
            "cuisine": "fishball noodles",
            "region": "central",
            "tags": ["fishball", "mee pok", "fish dumpling", "handmade", "michelin", "amoy street", "CBD"],
            "is_michelin": True,
            "is_halal": False,
            "best_time": "7:30am-1pm",
            "avoid_time": "After 2pm — likely sold out",
            "price_range": "S$5-7",
        },
    },
    {
        "id": "amoy_street_lor_mee",
        "text": (
            "Stall 02-05 Lor Mee at Amoy Street Food Centre. "
            "Thick yellow noodles in starchy dark gravy with braised pork, ngoh hiang, and half a boiled egg. "
            "A Hokkien breakfast staple. Opens from 7:30am, usually closed by 1pm. "
            "Price S$4-5."
        ),
        "metadata": {
            "centre_name": "Amoy Street Food Centre",
            "stall_name": "Amoy Street Lor Mee",
            "cuisine": "lor mee",
            "region": "central",
            "tags": ["lor mee", "hokkien", "braised pork", "breakfast", "amoy street", "CBD"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7:30am-11am",
            "avoid_time": "After 1pm — likely closed",
            "price_range": "S$4-5",
        },
    },
    {
        "id": "toa_payoh_hwa_heng_roast_duck",
        "text": (
            "Hwa Heng Beef Kway Teow at Toa Payoh Lorong 8 Market. "
            "Dry or soup beef flat noodles — tender beef slices with house-made chilli. "
            "A neighbourhood staple for Toa Payoh residents. "
            "Opens from 8am. Weekday lunch queue about 10-15 minutes. "
            "Price S$5-7."
        ),
        "metadata": {
            "centre_name": "Toa Payoh Lorong 8 Market",
            "stall_name": "Hwa Heng Beef Kway Teow",
            "cuisine": "beef kway teow",
            "region": "central",
            "tags": ["beef noodles", "kway teow", "toa payoh", "central singapore"],
            "is_michelin": False,
            "is_halal": False,
            "best_time": "8am-12pm",
            "avoid_time": "After 2pm — may sell out",
            "price_range": "S$5-7",
        },
    },
]

def seed():
    vs = VectorStore()

    if vs.collection_size() > 0:
        print(f"Collection already has {vs.collection_size()} docs — re-seeding (upsert).")

    vs.add_documents(STALLS)
    size = vs.collection_size()
    print(f"Seeded {size} documents into ChromaDB collection 'hawker_knowledge'.")
    # Note: michelin_2025.json and halal_stalls.json are managed as structured JSON
    # in backend/data/ and are NOT written by this script.

    # Smoke-test a query
    results = vs.query("chicken rice near Maxwell", n_results=2)
    print(f"\nSmoke test — 'chicken rice near Maxwell' top result:")
    if results:
        print(f"  {results[0]['metadata'].get('stall_name')} (distance={results[0]['distance']:.3f})")
    return size


if __name__ == "__main__":
    seed()
