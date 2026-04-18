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
            "tags": "chicken rice, hainanese, poached chicken",
            "is_michelin": True,
            "is_halal": False,
            "best_time": "Before 11:30am or after 2pm",
            "avoid_time": "12pm-2pm (huge queues)",
            "price_range": "S$5-7",
        },
    },
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
            "tags": "laksa, coconut milk, seafood, spicy",
            "is_michelin": True,
            "is_halal": False,
            "best_time": "Before 10am or weekday afternoon",
            "avoid_time": "Weekends 11am-1pm",
            "price_range": "S$6-9",
        },
    },
    {
        "id": "hill_street_char_kway_teow",
        "text": (
            "Hill Street Fried Kway Teow at Bedok South Road / Chinatown Complex. "
            "Dry-fried flat rice noodles with Chinese sausage, egg, beansprouts, and chilli. "
            "Wok hei (breath of the wok) is exceptional — high-heat charred fragrance. "
            "Michelin Bib Gourmand 2025. Opens only until sold out — usually by 2pm. "
            "Best time: 10am-12pm. Price S$4-6."
        ),
        "metadata": {
            "centre_name": "Chinatown Complex",
            "stall_name": "Hill Street Fried Kway Teow",
            "cuisine": "char kway teow",
            "tags": "char kway teow, fried noodles, wok hei",
            "is_michelin": True,
            "is_halal": False,
            "best_time": "10am-12pm, sells out by 2pm",
            "avoid_time": "After 2pm — likely sold out",
            "price_range": "S$4-6",
        },
    },
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
            "tags": "chilli crab, seafood, BBQ, outdoor",
            "is_michelin": False,
            "is_halal": True,
            "best_time": "6pm-9pm on clear evenings",
            "avoid_time": "Rainy nights (outdoor seating)",
            "price_range": "S$25-60",
        },
    },
    {
        "id": "hong_lim_nasi_lemak",
        "text": (
            "Mizzy Corner Nasi Lemak at Geylang Serai Market. "
            "Fragrant coconut rice served with crispy fried chicken, sambal, cucumber, and anchovies. "
            "Halal certified. Famous for their extra-crispy fried chicken and fiery sambal. "
            "Best time: breakfast from 7am. Sells out by 11am most days. "
            "Price S$4-8."
        ),
        "metadata": {
            "centre_name": "Geylang Serai Market",
            "stall_name": "Mizzy Corner Nasi Lemak",
            "cuisine": "nasi lemak",
            "tags": "nasi lemak, coconut rice, halal, malay food",
            "is_michelin": False,
            "is_halal": True,
            "best_time": "7am-10am (breakfast rush)",
            "avoid_time": "After 11am — may sell out",
            "price_range": "S$4-8",
        },
    },
    {
        "id": "tai_hwa_bak_chor_mee",
        "text": (
            "Tai Hwa Pork Noodle at Crawford Lane / Hill Street Tai Hwa. "
            "Minced pork noodles with vinegar-marinated lean pork, liver, and meatballs. "
            "Michelin Star (ONE star) — only hawker stall in Singapore with a star. "
            "Queues routinely exceed 90 minutes. Go on weekday mornings. "
            "Price S$8-12. Cash only."
        ),
        "metadata": {
            "centre_name": "Hill Street Tai Hwa Pork Noodle",
            "stall_name": "Tai Hwa Pork Noodle",
            "cuisine": "bak chor mee",
            "tags": "bak chor mee, minced pork noodles, michelin star",
            "is_michelin": True,
            "is_halal": False,
            "best_time": "Weekday 9am-11am",
            "avoid_time": "Weekends — 90+ min queues",
            "price_range": "S$8-12",
        },
    },
    {
        "id": "old_airport_road_rojak",
        "text": (
            "Sungei Road Laksa at Jalan Berseh / Old Airport Road Food Centre. "
            "Traditional laksa cooked over charcoal fire. "
            "Michelin Bib Gourmand 2025. Tiny portions, big flavour. "
            "Only open until sold out — usually by 11am. "
            "Price S$3-4."
        ),
        "metadata": {
            "centre_name": "Old Airport Road Food Centre",
            "stall_name": "Sungei Road Laksa",
            "cuisine": "laksa",
            "tags": "laksa, charcoal, traditional, old school",
            "is_michelin": True,
            "is_halal": False,
            "best_time": "Open from 8:30am, sold out by 11am",
            "avoid_time": "After 11am",
            "price_range": "S$3-4",
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
            "tags": "lor mee, hokkien, braised pork, breakfast",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7:30am-11am",
            "avoid_time": "After 1pm — likely closed",
            "price_range": "S$4-5",
        },
    },
    {
        "id": "lau_pa_sat_satay",
        "text": (
            "Satay Street at Lau Pa Sat Festival Market, Boon Tat Street. "
            "Evening satay street with dozens of charcoal-grilled satay stalls. "
            "Chicken, beef, mutton, and prawn satay with peanut sauce and ketupat. "
            "Most stalls halal. Vibrant outdoor atmosphere. "
            "Best time: 7pm-11pm. Avoid during rain (outdoor only). "
            "Price S$0.70-1.00 per stick."
        ),
        "metadata": {
            "centre_name": "Lau Pa Sat",
            "stall_name": "Satay Street Lau Pa Sat",
            "cuisine": "satay",
            "tags": "satay, grilled, halal, outdoor, evening",
            "is_michelin": False,
            "is_halal": True,
            "best_time": "7pm-10pm",
            "avoid_time": "Rainy evenings (fully outdoor)",
            "price_range": "S$0.70-1.00 per stick",
        },
    },
    {
        "id": "adam_road_roti_prata",
        "text": (
            "Casuarina Curry Restaurant / Mr Prata at Adam Road Food Centre. "
            "Crispy layered roti prata with dal and fish curry dipping sauces. "
            "Also serves tissue prata, egg prata, and coin prata. "
            "Halal certified. Open 24 hours. Popular after-midnight supper spot. "
            "Price S$1.20-4 per prata."
        ),
        "metadata": {
            "centre_name": "Adam Road Food Centre",
            "stall_name": "Mr Prata Adam Road",
            "cuisine": "roti prata",
            "tags": "roti prata, indian, halal, supper, 24 hours",
            "is_michelin": False,
            "is_halal": True,
            "best_time": "Any time — open 24h",
            "avoid_time": "No bad time",
            "price_range": "S$1.20-4",
        },
    },
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
            "tags": "BBQ, chicken wings, charcoal, evening, supper",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7pm-10pm",
            "avoid_time": "Rainy nights (outdoor centre)",
            "price_range": "S$2-3 per wing",
        },
    },
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
            "tags": "prawn noodles, pork ribs, hokkien, traditional",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7:30am-11am on weekdays",
            "avoid_time": "Weekend mornings — long queues",
            "price_range": "S$5-8",
        },
    },
    {
        "id": "maxwell_zhong_guo_la_mian",
        "text": (
            "Zhong Guo La Mian Xiao Long Bao at Smith Street / Chinatown Complex. "
            "Hand-pulled noodles and soup dumplings (xiao long bao) made fresh daily. "
            "Michelin Bib Gourmand 2025. "
            "Best choice for a warming lunch in Chinatown. "
            "Queue is fast-moving. Price S$5-9."
        ),
        "metadata": {
            "centre_name": "Chinatown Complex",
            "stall_name": "Zhong Guo La Mian Xiao Long Bao",
            "cuisine": "la mian",
            "tags": "la mian, xiao long bao, hand pulled noodles, dumplings",
            "is_michelin": True,
            "is_halal": False,
            "best_time": "11am-1pm",
            "avoid_time": "Late evening — may close early",
            "price_range": "S$5-9",
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
            "tags": "beef noodles, kway teow, toa payoh",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "8am-12pm",
            "avoid_time": "After 2pm — may sell out",
            "price_range": "S$5-7",
        },
    },
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
            "tags": "fishball, mee pok, fish dumpling, handmade",
            "is_michelin": True,
            "is_halal": False,
            "best_time": "7:30am-1pm",
            "avoid_time": "After 2pm — likely sold out",
            "price_range": "S$5-7",
        },
    },
    {
        "id": "lau_pa_sat_fish_soup",
        "text": (
            "Soon Huat Fish Soup at Lau Pa Sat Festival Market. "
            "Clear fish broth with sliced batang fish, tofu, and tomatoes. "
            "Light and nutritious — good for health-conscious diners. "
            "Available for both lunch and dinner. "
            "Price S$6-9."
        ),
        "metadata": {
            "centre_name": "Lau Pa Sat",
            "stall_name": "Soon Huat Fish Soup",
            "cuisine": "fish soup",
            "tags": "fish soup, clear broth, healthy, seafood",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-8pm",
            "avoid_time": "No bad time",
            "price_range": "S$6-9",
        },
    },
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
            "tags": "hokkien mee, wok hei, prawn broth, evening",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7pm-10pm",
            "avoid_time": "Daytime — stall not open",
            "price_range": "S$6-10",
        },
    },
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
            "cuisine": "wanton mee",
            "tags": "wanton mee, char siu, egg noodles",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "9am-1pm",
            "avoid_time": "After 3pm — may be closed",
            "price_range": "S$4-6",
        },
    },
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
            "tags": "nasi padang, malay food, halal, rendang, rice",
            "is_michelin": False,
            "is_halal": True,
            "best_time": "11am-2pm",
            "avoid_time": "After 3pm — dishes may run out",
            "price_range": "S$5-10",
        },
    },
    {
        "id": "old_airport_road_carrot_cake",
        "text": (
            "Stall #01-106 Radish Cake (Chai Tow Kway) at Old Airport Road Food Centre. "
            "Pan-fried white or black carrot cake — crispy outside, soft inside. "
            "Black version uses sweet dark soy and is more popular. "
            "Vegetarian-friendly. Opens from 7am. "
            "Price S$3-5."
        ),
        "metadata": {
            "centre_name": "Old Airport Road Food Centre",
            "stall_name": "Old Airport Road Chai Tow Kway",
            "cuisine": "carrot cake",
            "tags": "carrot cake, chai tow kway, vegetarian, breakfast",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-12pm",
            "avoid_time": "Evening — stall may not open",
            "price_range": "S$3-5",
        },
    },
    # ── Bak Kut Teh ──────────────────────────────────────────────────────────
    {
        "id": "song_fa_bak_kut_teh_clementi",
        "text": (
            "Song Fa Bak Kut Teh at Clementi 448 Market & Food Centre, West Singapore. "
            "Peppery Teochew-style pork rib soup with tender ribs in a clear, intensely peppery broth. "
            "One of Singapore's most popular bak kut teh chains — the west outlet is less crowded than CBD. "
            "Pairs well with you tiao (fried dough) dipped into the broth. "
            "Open for breakfast and lunch. Price S$8-14."
        ),
        "metadata": {
            "centre_name": "Clementi 448 Market & Food Centre",
            "stall_name": "Song Fa Bak Kut Teh",
            "cuisine": "bak kut teh",
            "tags": "bak kut teh, pork rib soup, teochew, peppery, west singapore, clementi",
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
            "tags": "bak kut teh, pork rib soup, peppery, central singapore, farrer park, rangoon",
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
            "Often cited as one of the best in Singapore. "
            "Price S$9-14."
        ),
        "metadata": {
            "centre_name": "Rangoon Road",
            "stall_name": "Founder Bak Kut Teh",
            "cuisine": "bak kut teh",
            "tags": "bak kut teh, pork ribs, peppery, traditional, rangoon road",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7:30am-9:30pm",
            "avoid_time": "No particular bad time",
            "price_range": "S$9-14",
        },
    },
    # ── West-side stalls ─────────────────────────────────────────────────────
    {
        "id": "lim_kee_duck_rice_clementi",
        "text": (
            "Lim Kee Duck Rice at Clementi 448 Market & Food Centre. "
            "Braised duck rice with tender braised duck, tau kwa, and hard-boiled egg in dark soy broth. "
            "A neighbourhood favourite in West Singapore — queue expected at lunch. "
            "Also serves duck noodles and duck porridge. "
            "Price S$4-7."
        ),
        "metadata": {
            "centre_name": "Clementi 448 Market & Food Centre",
            "stall_name": "Lim Kee Duck Rice",
            "cuisine": "duck rice",
            "tags": "duck rice, braised duck, clementi, west singapore",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-2pm",
            "avoid_time": "After 3pm — may sell out",
            "price_range": "S$4-7",
        },
    },
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
            "tags": "char siu, roast meat, BBQ pork, sio bak, queenstown, west singapore",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "10:30am-2pm",
            "avoid_time": "After 3pm — may sell out",
            "price_range": "S$4-8",
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
            "tags": "hokkien mee, wok hei, prawn, west singapore, queenstown, abc brickworks",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "5pm-9pm",
            "avoid_time": "Daytime — stall opens evenings only",
            "price_range": "S$5-10",
        },
    },
    {
        "id": "abc_brickworks_mee_rebus",
        "text": (
            "Selera Minang Mee Rebus at ABC Brickworks Food Centre. "
            "Malay-style yellow noodles in a thick, sweet-savoury potato and prawn gravy, "
            "topped with bean sprouts, a boiled egg, fried shallots, and green chilli. "
            "Halal certified. A classic Malay hawker dish. "
            "Price S$3.50-5."
        ),
        "metadata": {
            "centre_name": "ABC Brickworks Food Centre",
            "stall_name": "Selera Minang",
            "cuisine": "mee rebus",
            "tags": "mee rebus, malay food, halal, yellow noodles, west singapore",
            "is_michelin": False,
            "is_halal": True,
            "best_time": "7am-2pm",
            "avoid_time": "After 3pm — may close",
            "price_range": "S$3.50-5",
        },
    },
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
            "tags": "economy rice, cai fan, vegetarian, budget, west singapore",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7am-2pm",
            "avoid_time": "After 3pm — dishes run out",
            "price_range": "S$3-5",
        },
    },
    # ── More diverse central stalls ──────────────────────────────────────────
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
            "tags": "claypot rice, charcoal, waxed meat, chinese sausage, chinatown",
            "is_michelin": True,
            "is_halal": False,
            "best_time": "5pm-10pm (dinner)",
            "avoid_time": "Lunch — opens for dinner only",
            "price_range": "S$8-15",
        },
    },
    {
        "id": "outram_park_fried_kway_teow",
        "text": (
            "Outram Park Fried Kway Teow Mee at Hong Lim Market & Food Centre stall #02-18. "
            "Classic Teochew char kway teow — flat rice noodles fried with cockles, egg, beansprouts, "
            "and Chinese sausage. Strong wok hei, slightly sweet-savoury. "
            "Michelin Bib Gourmand 2025. Queue is usually 20-30 minutes. "
            "Price S$3-5."
        ),
        "metadata": {
            "centre_name": "Hong Lim Market & Food Centre",
            "stall_name": "Outram Park Fried Kway Teow",
            "cuisine": "char kway teow",
            "tags": "char kway teow, wok hei, cockles, outram, hong lim",
            "is_michelin": True,
            "is_halal": False,
            "best_time": "11am-2pm",
            "avoid_time": "Weekend peak — very long queues",
            "price_range": "S$3-5",
        },
    },
    {
        "id": "whampoa_prawn_noodles",
        "text": (
            "545 Whampoa Prawn Noodles at Whampoa Makan Place / Food Centre. "
            "Prawn noodle soup or dry — rich intense prawn bisque broth, fresh prawns, "
            "pork ribs, and pork slices. One of the most celebrated prawn noodle stalls in Singapore. "
            "Queue 30+ minutes on weekends. "
            "Price S$6-12."
        ),
        "metadata": {
            "centre_name": "Whampoa Makan Place",
            "stall_name": "545 Whampoa Prawn Noodles",
            "cuisine": "prawn noodles",
            "tags": "prawn noodles, hae mee, pork ribs, whampoa, intense broth",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "8am-1pm",
            "avoid_time": "Weekends — extremely long queue",
            "price_range": "S$6-12",
        },
    },
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
            "tags": "ban mian, handmade noodles, anchovy broth, comfort food, amoy street",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "7:30am-2pm",
            "avoid_time": "After 3pm — closed",
            "price_range": "S$4-6",
        },
    },
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
            "tags": "oyster omelette, orh luak, hokkien, seafood, clementi, west singapore",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "11am-8pm",
            "avoid_time": "No bad time",
            "price_range": "S$5-7",
        },
    },
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
            "tags": "curry puff, hainanese, pastry, toa payoh, snack",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "8am-11am",
            "avoid_time": "After 11am — sells out",
            "price_range": "S$1.50-2",
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
            "tags": "frog porridge, congee, supper, late night, bedok, east singapore",
            "is_michelin": False,
            "is_halal": False,
            "best_time": "8pm-2am (supper)",
            "avoid_time": "Daytime — not open",
            "price_range": "S$8-15",
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
