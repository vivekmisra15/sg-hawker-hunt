"""
One-time seed script for the ChromaDB hawker knowledge base.
Run from backend/: python3 -m rag.seed
"""
import json
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
]

MICHELIN_2025 = [
    "Tian Tian Hainanese Chicken Rice",
    "328 Katong Laksa",
    "Hill Street Fried Kway Teow",
    "Sungei Road Laksa",
    "Tai Hwa Pork Noodle",
    "Zhong Guo La Mian Xiao Long Bao",
    "Fishball Story",
    "Hawker Chan Soya Sauce Chicken",
    "A Noodle Story",
    "Liao Fan Hong Kong Soya Sauce Chicken Rice & Noodle",
]

HALAL_STALLS = [
    "Alliance Seafood",
    "Mizzy Corner Nasi Lemak",
    "Mr Prata Adam Road",
    "Satay Street Lau Pa Sat",
    "Hajjah Mona Nasi Padang",
    "Zam Zam Restaurant",
    "Adam Road Prata House",
    "Bismillah Biryani",
    "Al-Azhar Restaurant",
    "Geylang Serai BBQ",
]


def seed():
    vs = VectorStore()

    if vs.collection_size() > 0:
        print(f"Collection already has {vs.collection_size()} docs — re-seeding (upsert).")

    vs.add_documents(STALLS)
    size = vs.collection_size()
    print(f"Seeded {size} documents into ChromaDB collection 'hawker_knowledge'.")

    # Write static JSON files
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    michelin_path = os.path.join(data_dir, "michelin_2025.json")
    halal_path = os.path.join(data_dir, "halal_stalls.json")

    with open(michelin_path, "w") as f:
        json.dump(MICHELIN_2025, f, indent=2)
    print(f"Wrote {len(MICHELIN_2025)} entries to michelin_2025.json")

    with open(halal_path, "w") as f:
        json.dump(HALAL_STALLS, f, indent=2)
    print(f"Wrote {len(HALAL_STALLS)} entries to halal_stalls.json")

    # Smoke-test a query
    results = vs.query("chicken rice near Maxwell", n_results=2)
    print(f"\nSmoke test — 'chicken rice near Maxwell' top result:")
    if results:
        print(f"  {results[0]['metadata'].get('stall_name')} (distance={results[0]['distance']:.3f})")
    return size


if __name__ == "__main__":
    seed()
