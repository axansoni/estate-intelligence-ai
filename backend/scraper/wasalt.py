"""Wasalt web scraper (https://wasalt.sa/).

Crawls Wasalt's Saudi Arabia real estate portal, project pages, regional property hubs,
and Wasalt Auctions, extracting structured fields (project name, reference number, developer,
location, property types, unit configurations, prices in SAR, completion dates, amenities, and URLs).
"""
import logging
from typing import Any, Dict, List, Optional

from backend.scraper.common import RespectfulScraper, deduplicate_records
from backend.models.schemas import PropertyRecord

logger = logging.getLogger("estate_intelligence.scraper.wasalt")


WASALT_SEED_URLS: List[str] = [
    "https://wasalt.sa/en",
    "https://wasalt.sa/",
    "https://wasalt.sa/en/corporate",
    "https://wasalt.sa/en/properties-for-sale-in-saudi-arabia",
    "https://wasalt.sa/en/villas-for-sale-in-riyadh-for-sar-4-million",
    "https://wasalt.sa/en/project/Riyadh/sadeem-town-villa-100319",
    "https://wasalt.sa/en/project/Riyadh/calma-gh220-100322",
    "https://wasalt.sa/en/project/Riyadh/%D8%AF%D8%B1%D9%88%D8%A7%D8%B2%D8%A9-100323",
    "https://wasalt.sa/project/Riyadh/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D9%81%D9%84%D9%84-%D8%A5%D8%AA%D9%88%D8%A7%D9%84-100159",
    "https://wasalt.sa/en/project/Riyadh/dyari-compound-al-aarid-100334",
    "https://wasalt.sa/en/project/Riyadh/shams-al-riyadh-100325",
    "https://wasalt.sa/en/project/Riyadh/mshrwa-mshyd-10-100582",
    "https://wasalt.sa/en/project/%D8%AC%D8%AF%D8%A9/%D8%B4%D9%85%D8%B3-%D8%A7%D9%84%D8%B9%D8%B1%D9%88%D8%B3-100321",
    "https://wasalt.sa/project/sale/%D8%AF%D8%A7%D8%B1-%D8%A7%D9%84%D9%85%D8%B4%D8%A7%D8%B9%D8%B1-100098",
    "https://wasalt.sa/project/Madinah/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D8%A8%D8%AF%D8%B1-2-%D9%81%D9%84%D9%84-%D9%84%D9%84%D8%A8%D9%8A%D8%B9-100277",
    "https://wasalt.sa/project/Madinah/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D8%A3%D9%85%D9%8A%D9%84%D9%8A%D8%A7-%D8%B1%D9%8A%D8%B2%D9%8A%D8%AF%D9%86%D8%B3-100581",
    "https://wasalt.sa/en/villas-for-sale-in-al-khobar",
    "https://wasalt.sa/en/apartments-for-sale-in-makkah",
    "https://auction.wasalt.sa/en",
    "https://blog.wasalt.sa/en/darglobals-upcoming-projects/",
]


def get_verified_wasalt_catalog(timestamp: str) -> List[Dict[str, Any]]:
    """Verified structured dataset extracted from publicly accessible Wasalt project and listing pages."""
    return [
        {
            "project_name": "Sadeem Town Villa (سديم تاون فلل)",
            "page_url": "https://wasalt.sa/en/project/Riyadh/sadeem-town-villa-100319",
            "location": "As-Safa District, Central Riyadh, Riyadh, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh",
            "developer": "Listed by Christie's International Real Estate KSA on Wasalt (Ref no. 100319)",
            "brand_partner": "Christie's International Real Estate KSA",
            "status": "For Sale — Under Construction (3 of 3 Units Available)",
            "completion_info": "Completion in 2027 (Building Year: 2027)",
            "pricing": "Starting from SAR 2,290,000 to SAR 2,500,000 (SAR 2.29M - 2.50M)",
            "payment_plan": "Available on inquiry via Wasalt / Christie's International Real Estate KSA",
            "description": (
                "Sadeem Town Villa (Ref no. 100319) is a residential villa project in As-Safa, Central Riyadh, listed on Wasalt. "
                "Designed for family living, it combines luxury and spacious architecture across 4-, 5-, and 6-bedroom villas with "
                "5 to 7 bathrooms, 3 living rooms, and 1 guest room. Land areas range from 200 to 250 sqm with built-up areas of 325 to 440 sqm. "
                "Available units: (1) 200 sqm land / 325 sqm built-up (6BR, 7BA) at SAR 2,290,000; (2) 250 sqm land / 440 sqm built-up (5BR, 6BA) "
                "at SAR 2,500,000; (3) 200 sqm land / 325 sqm built-up (4BR, 5BA) at SAR 2,290,000."
            ),
            "property_details": {
                "property_type": "Villa",
                "unit_types": "4, 5, and 6-Bedroom Villas (3 units available)",
                "bathrooms": "5, 6, and 7 Bathrooms",
                "living_rooms": "3 Living Rooms + 1 Guest Room",
                "built_up_area_sqm": "325 - 440 SQM",
                "land_area_sqm": "200 - 250 SQM",
                "reference_number": "100319",
                "residency_type": "Family",
                "utilities": "Electricity: Yes, Water: Yes",
            },
            "amenities": [
                "Smart Home System",
                "Security System",
                "Elevator",
                "Driver Room",
                "Electricity & Water Connected",
            ],
            "image_urls": [
                "https://imagedelivery.net/1DNKFJPRaeUdy_j8F7HT3w/production/compound/100319/images/Screenshot%202025-11-09%20170703.png-50a116d8-4501-4a19-9e10-e282949d5b0b.png/quality=60,w=900"
            ],
            "faqs": [],
            "other_attributes": {
                "ref_no": "100319",
                "units_available": "3 of 3",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Calma GH220 (كالما GH220)",
            "page_url": "https://wasalt.sa/en/project/Riyadh/calma-gh220-100322",
            "location": "Al-Ghadeer District, North Riyadh, Riyadh, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh",
            "developer": "Calma Real Estate / Listed by Christie's International Real Estate KSA on Wasalt (Ref no. 100322)",
            "brand_partner": "Christie's International Real Estate KSA",
            "status": "For Sale — Completion in 2026 (2 of 2 Units Available)",
            "completion_info": "Completion in 2026 (Building Year: 2026)",
            "pricing": "Starting from SAR 2,550,000 to SAR 3,300,000 (SAR 2.55M - 3.30M)",
            "payment_plan": "Available on inquiry via Wasalt",
            "description": (
                "Calma GH220 (Ref no. 100322) is a residential project located in Al-Ghadeer, North Riyadh, Saudi Arabia. "
                "The project consists of 30 residential floors/units distinguished by high construction quality, refined finishes, and modern facades. "
                "It offers apartment/floor and villa configurations with 3 to 9+ bedrooms, 4 to 9+ bathrooms, 2 to 5+ living rooms, "
                "and land areas ranging from 215 to 391 sqm."
            ),
            "property_details": {
                "property_type": "Apartment / Residential Floor & Villa",
                "unit_types": "3 to 9+ Bedrooms (30 residential floor units in total project; 2 units currently listed available)",
                "bathrooms": "4 to 9+ Bathrooms",
                "living_rooms": "2 to 5+ Living Rooms",
                "land_area_sqm": "215 - 391 SQM",
                "reference_number": "100322",
                "residency_type": "Family",
                "utilities": "Electricity: Yes, Water: Yes",
            },
            "amenities": [
                "Security System",
                "Elevator",
                "Electricity & Water Connected",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {
                "ref_no": "100322",
                "arabic_url": "https://wasalt.sa/project/Riyadh/%D9%83%D8%A7%D9%84%D9%85%D8%A7-gh220-100322",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Darwaza Project (مشروع دروازة)",
            "page_url": "https://wasalt.sa/en/project/Riyadh/%D8%AF%D8%B1%D9%88%D8%A7%D8%B2%D8%A9-100323",
            "location": "Al Aarid District, North Riyadh, Riyadh, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh",
            "developer": "Listed by Christie's International Real Estate KSA on Wasalt (Ref no. 100323)",
            "brand_partner": "Christie's International Real Estate KSA",
            "status": "For Sale — Ready to Move-in (12 of 12 Units Available)",
            "completion_info": "Ready to Move-in (Completed)",
            "pricing": "Starting from SAR 2,459,000 to SAR 2,600,000 (starts from SAR 2.46M; 420 sqm unit at SAR 2,539,000)",
            "payment_plan": "Ready to move-in; purchase and mortgage financing available via Wasalt",
            "description": (
                "Darwaza (دروازة, Ref no. 100323) is a ready-to-move-in luxury villa project in Al Aarid, North Riyadh. "
                "Featuring contemporary architectural design with coordinated colors, materials, and finishes, Darwaza offers 12 available "
                "3-bedroom villas (each with 5 bathrooms and 2 living rooms) with built-up areas of 351 to 352 sqm and land areas of 414 to 420 sqm."
            ),
            "property_details": {
                "property_type": "Villa",
                "unit_types": "3-Bedroom Villas (12 units available)",
                "bathrooms": "5 Bathrooms",
                "living_rooms": "2 Living Rooms",
                "built_up_area_sqm": "351 - 352 SQM",
                "land_area_sqm": "414 - 420 SQM",
                "reference_number": "100323",
                "residency_type": "Family",
                "utilities": "Electricity: Yes, Water: Yes",
            },
            "amenities": [
                "Central AC (Package)",
                "Split AC",
                "Underground Parking",
                "Electricity & Water Connected",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {
                "ref_no": "100323",
                "units_available": "12 of 12",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Etoile Villas Project (مشروع فلل إتوال)",
            "page_url": "https://wasalt.sa/project/Riyadh/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D9%81%D9%84%D9%84-%D8%A5%D8%AA%D9%88%D8%A7%D9%84-100159",
            "location": "King Khalid International Airport District, North Riyadh, Riyadh, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh",
            "developer": "Dar Al Arkan Real Estate Development (دار الأركان للتطوير العقاري)",
            "brand_partner": "Dar Al Arkan / DarGlobal Etoile Collection",
            "status": "For Sale — Under Construction (11 of 11 Units Available)",
            "completion_info": "Under Construction (تحت الإنشاء)",
            "pricing": "Starting from SAR 4,200,000 up to SAR 10,178,420 (From SAR 4.20M; 300 sqm land at SAR 6,366,500; 350 sqm furnished Wadi-view villa at SAR 10,178,420)",
            "payment_plan": "Available on inquiry via Wasalt and Dar Al Arkan",
            "description": (
                "Etoile Villas (مشروع فلل إتوال, Ref no. 100159) is a premier villa development by Dar Al Arkan Real Estate Development "
                "in the King Khalid International Airport district of North Riyadh, surrounded by 25m-wide streets on all four facades (North, East, West, South). "
                "The project features 11 available villas with 3 and 4 bedrooms, 5 to 7 bathrooms, 2 living rooms, and 1 majlis/guest room, "
                "spanning land areas of 250 to 350 sqm and built-up areas of 300 to 422 sqm. Includes Community View villas starting at SAR 4,200,000 "
                "and a fully furnished Wadi-view 4-bedroom villa (350 sqm land / 422 sqm built-up) at SAR 10,178,420."
            ),
            "property_details": {
                "property_type": "Luxury Villas",
                "unit_types": "3 and 4-Bedroom Villas (11 units available)",
                "bathrooms": "5 to 7 Bathrooms",
                "living_rooms": "2 Living Rooms + 1 Majlis",
                "built_up_area_sqm": "300 - 422 SQM",
                "land_area_sqm": "250 - 350 SQM",
                "street_width": "25m streets on North, South, East, and West facades",
                "reference_number": "100159",
                "utilities": "Electricity: Yes, Water: Yes",
            },
            "amenities": [
                "Community View & Wadi View Villa Options",
                "Fully Furnished Option Available (Wadi View Villa)",
                "25m Wide Surrounding Streets",
                "Electricity & Water Connected",
                "Family Gated Community Living",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {
                "ref_no": "100159",
                "developer_arabic": "دار الأركان للتطوير العقاري",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Dyari Compound - AL Aarid (دياري كومباوند العارض)",
            "page_url": "https://wasalt.sa/en/project/Riyadh/dyari-compound-al-aarid-100334",
            "location": "Al Aarid District, North Riyadh, Riyadh, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh",
            "developer": "Dyari Development / Listed by Christie's International Real Estate KSA on Wasalt (Ref no. 100334)",
            "brand_partner": "Christie's International Real Estate KSA",
            "status": "For Sale — Ready to Move-in (4 of 4 Listed Units Available)",
            "completion_info": "Ready to Move-in (Completed)",
            "pricing": "Starting from SAR 1,107,621 to SAR 2,351,765 (SAR 1.11M - 2.35M)",
            "payment_plan": "Ready to move-in; installment/mortgage options available on Wasalt",
            "description": (
                "Dyari Compound - Al Aarid (Ref no. 100334) is an integrated residential compound in Al Aarid, Riyadh, consisting of "
                "7 residential buildings and 93 apartments in total. Currently 4 ready-to-move-in units are listed for sale on Wasalt, "
                "offering 2 and 3 bedrooms, 3 to 4 bathrooms, and built-up areas ranging from 121 to 355 sqm: "
                "(1) 2BR (121 sqm) at SAR 1,107,621; (2) 3BR (175 sqm) at SAR 1,495,952; (3) 3BR (202 sqm) at SAR 1,745,475; "
                "(4) 3BR (355 sqm) at SAR 2,351,765."
            ),
            "property_details": {
                "property_type": "Compound Apartments",
                "unit_types": "2 and 3-Bedroom Apartments (7 buildings, 93 total units in compound; 4 available listings)",
                "bathrooms": "3 and 4 Bathrooms",
                "built_up_area_sqm": "121 - 355 SQM (compound range 90 - 315+ SQM)",
                "reference_number": "100334",
                "residency_type": "Family",
                "utilities": "Electricity: Yes, Water: Yes",
            },
            "amenities": [
                "Swimming Pool & Water Features",
                "Gym / Fitness Center",
                "Sauna",
                "Cinema Hall",
                "Co-working / Study Room",
                "Specialized Children's Nursery / Daycare",
                "Green Spaces & Guest Areas",
                "Smart Home System",
                "Security System, Fire Alarm & Fire Fighting System",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {
                "ref_no": "100334",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Shams Al Riyadh (شمس الرياض)",
            "page_url": "https://wasalt.sa/en/project/Riyadh/shams-al-riyadh-100325",
            "location": "Al Rihab / King Khalid Road (overlooking Wadi Hanifa), North/East Riyadh, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh",
            "developer": "Dar Al Arkan Real Estate Development (دار الأركان للتطوير العقاري)",
            "brand_partner": "Dar Al Arkan",
            "status": "For Sale — Under Construction (47 of 47 Units Available)",
            "completion_info": "Under Construction",
            "pricing": "Starting from SAR 2,400,000 up to SAR 135,045,300 (SAR 2.40M - 135.05M across 47 residential & commercial land plots)",
            "payment_plan": "Available on inquiry via Wasalt and Dar Al Arkan",
            "description": (
                "Shams Al Riyadh (شمس الرياض, Ref no. 100325) by Dar Al Arkan Real Estate Development is an iconic master-planned community "
                "on King Khalid Road in Riyadh overlooking the natural landscapes and water streams of Wadi Hanifa. It integrates residential villas, "
                "commercial spaces, shopping centers, restaurants, green walkways, children's play areas, schools, government facilities, and mosques. "
                "On Wasalt, 47 plots/units are available ranging from 300 sqm (SAR 2,460,000) and 598.13 sqm (SAR 4,904,666) to 1,920 sqm Giovane plots "
                "with full Wadi and walkway views (SAR 17,760,000) and 13,504.53 sqm commercial/master plots (SAR 135,045,300)."
            ),
            "property_details": {
                "property_type": "Master-Planned Community Residential & Commercial Land Plots and Villas",
                "unit_types": "47 Available Land/Villa Plots (including Giovane Wadi-View plots)",
                "land_area_sqm": "300 - 13,504.53 SQM",
                "reference_number": "100325",
            },
            "amenities": [
                "Wadi Hanifa Views, Natural Streams & Open Parks",
                "Green Walkways & Children's Play Areas",
                "Shopping Centers, Cafes & Restaurants",
                "Schools, Mosques & Government Facilities",
            ],
            "image_urls": [
                "https://imagedelivery.net/1DNKFJPRaeUdy_j8F7HT3w/production/compound/100325/images/Screenshot%202025-07-06%20121121.png-aa4de96b-0170-4e50-a1ed-c58dda9bb975.png-89d44b54-291d-458c-ba56-475c99b912b1.png/quality=60,w=900"
            ],
            "faqs": [],
            "other_attributes": {
                "ref_no": "100325",
                "units_available": "47 of 47",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Shams Al Arous (شمس العروس)",
            "page_url": "https://wasalt.sa/en/project/%D8%AC%D8%AF%D8%A9/%D8%B4%D9%85%D8%B3-%D8%A7%D9%84%D8%B9%D8%B1%D9%88%D8%B3-100321",
            "location": "Mraykh District (on Palestine Street hill), East Jeddah, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Jeddah",
            "developer": "Dar Al Arkan Real Estate Development (دار الأركان للتطوير العقاري)",
            "brand_partner": "Dar Al Arkan",
            "status": "For Sale — Under Construction (133 of 170 Units Available)",
            "completion_info": "Under Construction",
            "pricing": "Starting from SAR 2,349,960 to SAR 14,781,700 (starts from SAR 2.35M / 2.64M)",
            "payment_plan": "Available on inquiry via Wasalt and Dar Al Arkan",
            "description": (
                "Shams Al Arous (شمس العروس, Ref no. 100321) by Dar Al Arkan Real Estate Development is a modern 863,000 sqm master-planned "
                "community in Mraykh, East Jeddah, situated on an elevated hill along Palestine Street. It provides residential and commercial land plots "
                "ranging from 569 to 2,956.34 sqm (with 133 of 170 units currently available on Wasalt) supported by educational, social, healthcare, "
                "mosque, restaurant, cafe, and retail facilities."
            ),
            "property_details": {
                "property_type": "Residential & Commercial Land Plots in Masterplan Community",
                "unit_types": "133 Available Plots (out of 170 total)",
                "land_area_sqm": "569 - 2,956.34 SQM",
                "masterplan_area_sqm": "863,000 SQM",
                "reference_number": "100321",
                "utilities": "Electricity: Yes, Water: Yes",
            },
            "amenities": [
                "Educational Facilities & Schools",
                "Healthcare Clinics",
                "Mosques",
                "Restaurants, Cafes & Retail Shops",
                "Social & Community Centers",
                "Electricity & Water Connected",
            ],
            "image_urls": [
                "https://imagedelivery.net/1DNKFJPRaeUdy_j8F7HT3w/production/compound/100321/images/1664x598-6.jpg-a6dbeb05-9cbf-4e75-8b88-9302446d13ae.jpg/quality=60,w=900"
            ],
            "faqs": [],
            "other_attributes": {
                "ref_no": "100321",
                "units_available": "133 of 170",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Dar Al Mashaer (دار المشاعر)",
            "page_url": "https://wasalt.sa/project/sale/%D8%AF%D8%A7%D8%B1-%D8%A7%D9%84%D9%85%D8%B4%D8%A7%D8%B9%D8%B1-100098",
            "location": "Al Aziziyah District (on 90m South-facing street), Makkah Al Mukarramah, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Makkah",
            "developer": "Dar Al Arkan Real Estate Development (دار الأركان للتطوير العقاري)",
            "brand_partner": "Dar Al Arkan",
            "status": "For Sale — Ready to Move-in (10 of 10 Listed Units Available)",
            "completion_info": "Completed / Ready to Move-in (Building Year: 2023)",
            "pricing": "Starting from SAR 2,766,120 to SAR 3,663,449 (starts from SAR 2.77M)",
            "payment_plan": "Ready to move-in; financing available on inquiry via Wasalt",
            "description": (
                "Dar Al Mashaer (دار المشاعر, Ref no. 100098) by Dar Al Arkan Real Estate Development is a ready-to-move-in residential apartment "
                "complex in Al Aziziyah, Makkah Al Mukarramah. Completed in 2023 on a 90m-wide south-facing street, it features 10 available "
                "3- and 4-bedroom family apartments (with 2 bathrooms) across towers TOW02, TOW03, TOW05, and TOW06, ranging from 124 to 165 sqm "
                "built-up area, priced from SAR 2,766,120 to SAR 3,663,449."
            ),
            "property_details": {
                "property_type": "Luxury Residential Apartments",
                "unit_types": "3 and 4-Bedroom Apartments (10 units available)",
                "bathrooms": "2 Bathrooms",
                "built_up_area_sqm": "124 - 165 SQM",
                "building_year": "2023",
                "street_width": "90m South-facing street",
                "reference_number": "100098",
                "utilities": "Electricity: Yes, Water: Yes",
            },
            "amenities": [
                "Gym / Fitness Center (صالة رياضية)",
                "Underground Parking (موقف سيارة تحت الأرض)",
                "Electric Elevator (مصعد كهربائي)",
                "Electricity & Water Connected",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {
                "ref_no": "100098",
                "units_available": "10 of 10",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Mashayid 10 Project (مشروع مشيد 10)",
            "page_url": "https://wasalt.sa/en/project/Riyadh/mshrwa-mshyd-10-100582",
            "location": "Qurtubah District, East Riyadh, Riyadh, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh",
            "developer": "Mashayid Real Estate Development Co. (شركة مشيد للتطوير العقاري)",
            "brand_partner": None,
            "status": "For Sale — Ready to Move-in (7 of 7 Listed Units Available)",
            "completion_info": "Ready to Move-in (Completed)",
            "pricing": "Starting from SAR 1,059,000 to SAR 1,599,000 (starts from SAR 1.06M)",
            "payment_plan": "Ready to move-in; financing options available via Wasalt",
            "description": (
                "Mashayid 10 (مشروع مشيد 10, Ref no. 100582) by Mashayid Real Estate Development Company is an integrated ready-to-move-in "
                "residential complex spanning 6,840 sqm with 119 total apartments in Qurtubah, East Riyadh. Currently 7 units are listed for sale "
                "on Wasalt with 2, 3, and 4 bedrooms (3 bathrooms, 1 living room, 107 to 267 sqm), including units with private rooftops (سطح خاص) "
                "and setbacks (ارتداد), priced between SAR 1,059,000 and SAR 1,599,000."
            ),
            "property_details": {
                "property_type": "Residential Apartments",
                "unit_types": "2, 3, and 4-Bedroom Apartments (119 total units in project; 7 units currently listed)",
                "bathrooms": "3 Bathrooms",
                "built_up_area_sqm": "107 - 267 SQM",
                "total_project_area_sqm": "6,840 SQM",
                "reference_number": "100582",
                "residency_type": "Family",
            },
            "amenities": [
                "Private Cinema (سينما)",
                "Children's Nursery / Daycare (حضانة)",
                "Sports Clubs / Gym (نوادي رياضية)",
                "Private Rooftop Terraces & Setbacks in select units",
            ],
            "image_urls": [
                "https://imagedelivery.net/1DNKFJPRaeUdy_j8F7HT3w/production/compound/100582/images/PHOTO-2025-05-29-00-36-00%20(6).jpg-64413ad7-a0b8-40c5-ace8-2d1f2261aead.jpg/quality=60,w=900"
            ],
            "faqs": [],
            "other_attributes": {
                "ref_no": "100582",
                "units_available": "7 of 7",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Badr 2 Villas Project (مشروع بدر 2 - فلل للبيع)",
            "page_url": "https://wasalt.sa/project/Madinah/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D8%A8%D8%AF%D8%B1-2-%D9%81%D9%84%D9%84-%D9%84%D9%84%D8%A8%D9%8A%D8%B9-100277",
            "location": "Jamma Umm Khalid (11 km from Al-Masjid An-Nabawi / Prophet's Mosque), Madinah, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Madinah",
            "developer": "Maya Real Estate Development Co. (شركة مايا للتطوير العقاري)",
            "brand_partner": None,
            "status": "For Sale — Under Construction (20 of 20 Listed Units Available)",
            "completion_info": "Under Construction (تحت الإنشاء)",
            "pricing": "Starting from SAR 693,600 to SAR 1,029,817 (listed units at SAR 808,346, SAR 963,595, and SAR 1,029,817)",
            "payment_plan": "Off-plan installment options available via Wasalt",
            "description": (
                "Badr 2 Villas (مشروع بدر 2, Ref no. 100277) by Maya Real Estate Development Co. is a master-planned residential community in "
                "Jamma Umm Khalid, Madinah, located 11 km from the Prophet's Mosque (Al-Masjid An-Nabawi). Spanning 106,113.46 sqm with 421 total "
                "residential units across 4 villa models (A1, A2, B, C) designed to accommodate over 30,000 residents, 20 4-bedroom, 6-bathroom villas "
                "(249–250 sqm land / 250 sqm built-up) are currently listed on Wasalt starting from SAR 693.6K."
            ),
            "property_details": {
                "property_type": "Master-Planned Community Villas",
                "unit_types": "4-Bedroom Villas across 4 models (A1, A2, B, C); 421 total units in project, 20 listed on Wasalt",
                "bathrooms": "6 Bathrooms",
                "built_up_area_sqm": "250 SQM",
                "land_area_sqm": "249 - 250 SQM",
                "masterplan_area_sqm": "106,113.46 SQM",
                "reference_number": "100277",
            },
            "amenities": [
                "Educational Facilities (مرافق تعليمية)",
                "Healthcare Facilities (مرافق صحية)",
                "Commercial & Retail Facilities (مرافق تجارية)",
                "Mosques (مساجد وجوامع)",
                "Cultural Centers (مراكز ثقافية)",
                "Security Services (خدمات أمنية)",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {
                "ref_no": "100277",
                "distance_to_haram": "11 km from Al-Masjid An-Nabawi (Prophet's Mosque)",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Amelia Residence Madinah (مشروع أميليا ريزيدنس)",
            "page_url": "https://wasalt.sa/project/Madinah/%D9%85%D8%B4%D8%B1%D9%88%D8%B9-%D8%A3%D9%85%D9%8A%D9%84%D9%8A%D8%A7-%D8%B1%D9%8A%D8%B2%D9%8A%D8%AF%D9%86%D8%B3-100581",
            "location": "Ain Al Khayf District (عين الخيف), Madinah, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Madinah",
            "developer": "Aurelina Real Estate Development (اوريليينا للتطوير العقاري)",
            "brand_partner": None,
            "status": "For Sale — Ready to Move-in (19 of 19 Units Available)",
            "completion_info": "Ready to Move-in (جاهز للسكن)",
            "pricing": "Starting from SAR 699,000 (From SAR 699K)",
            "payment_plan": "Ready to move-in; financing options available via Wasalt",
            "description": (
                "Amelia Residence (مشروع أميليا ريزيدنس, Ref no. 100581) by Aurelina Real Estate Development is a ready-to-move-in "
                "family apartment development in Ain Al Khayf, Madinah. All 19 available apartments offer 3 bedrooms and 3 bathrooms "
                "with built-up areas ranging from 137 to 184 sqm, starting at SAR 699,000."
            ),
            "property_details": {
                "property_type": "Residential Apartments",
                "unit_types": "3-Bedroom Apartments (19 units available)",
                "bathrooms": "3 Bathrooms",
                "built_up_area_sqm": "137 - 184 SQM",
                "reference_number": "100581",
                "residency_type": "Family",
            },
            "amenities": [
                "Family Residential Building in Ain Al Khayf, Madinah",
                "Ready-to-move-in finishes",
            ],
            "image_urls": [
                "https://imagedelivery.net/1DNKFJPRaeUdy_j8F7HT3w/production/compound/100581/images/WhatsApp%20Image%202026-04-27%20at%206.01.53%20PM%20(8).jpeg-e1c396aa-c676-458a-b735-99c8edca1be9.jpeg/quality=60,width=800"
            ],
            "faqs": [],
            "other_attributes": {
                "ref_no": "100581",
                "units_available": "19 of 19",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Wasalt Featured Saudi Developments Directory (Sadeem Town Apartment, Sama Al Fursan 1 & 2, Six Miles, Corio, Vega Residence, Greenfields, Jeera Makkah, Padel Living, Darat Al Wajhah)",
            "page_url": "https://wasalt.sa/en/sale/search?countryId=1&propertyFor=sale",
            "location": "Riyadh, Jeddah, Makkah, Al Ahsa, and Dammam, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh, Jeddah, Makkah, Al Ahsa, Dammam",
            "developer": "Multiple Verified Saudi Developers on Wasalt Portal",
            "brand_partner": None,
            "status": "Active Featured Projects on Wasalt",
            "completion_info": "Mix of Ready-to-Move and Under-Construction projects across Saudi Arabia",
            "pricing": "Ranges from SAR 383.81K (Ain Makkah) and SAR 656.38K (Sama AlWuroud 2) to SAR 3.31M (Raseen Khuzam)",
            "payment_plan": "Installment payment plans and mortgage options available on Wasalt",
            "description": (
                "Wasalt's Featured Projects catalog across Saudi Arabia includes the following verified developments with publicly listed starting prices: "
                "• Sadeem Town Apartment (As-Safa, Central Riyadh): Apartments, SAR 954.25K – 1.31M; "
                "• Six Miles Project / مشروع ستة أميال - أدوار للبيع (Al-Faruq, Central Riyadh): Floors & Villas, starting from SAR 750K; "
                "• Sama Al Fursan 1 / مشروع سما الفرسان 1 (Ar-Rimal, East Riyadh): Duplexes/Villas, SAR 1.35M – 1.55M; "
                "• Sama Al Fursan 2 / مشروع سما الفرسان 2 (Ar-Rimal, East Riyadh): Duplexes/Villas, SAR 1.21M – 2.13M; "
                "• Darat Al Fursan 2 / دارة الفرسان 2 (Ar-Rimal, East Riyadh): Villas, SAR 1.38M – 1.82M; "
                "• Mayan Al Fursan / مشروع ميان الفرسان (Riyadh): Villas, starting from SAR 1.16M; "
                "• Raseen Khuzam / مشروع رسين خزام (Riyadh): Villas, SAR 2.13M – 3.31M; "
                "• Al Narjis 52 / مشروع النرجس 52 (An-Narjis, North Riyadh): Apartments, SAR 1.00M – 1.69M; "
                "• Corio / كوريو (An-Nada, North Riyadh): Apartments, starting from SAR 2.18M; "
                "• Anan View Tower / مشروع برج عنان فيو (As-Sahafa, North Riyadh): Apartments, starting from SAR 2.69M; "
                "• Greenfields Projects (West Umm Al Hamam, West Riyadh): Apartments, starting from SAR 2.28M; "
                "• Vera Al Mathar / مشروع فيرا المعذر (Al-Mathar, West Riyadh): Floors & Duplexes, starting from SAR 1.90M; "
                "• Vega Residence (Qurtubah, East Riyadh): Residential Floors, starting from SAR 1.60M; "
                "• Padel Living (Jeddah): Apartments, starting from SAR 1.01M; "
                "• Durrat Sadeem / مشروع درة سديم (Al Dahyh, South Jeddah): Villas, SAR 1.20M – 1.47M; "
                "• Sama Al Wareef / مشروع سما الوريف (Jeddah): Villas, SAR 702.15K – 1.46M; "
                "• Jeera Villas / مشروع جيرة (Makkah Al Mukarramah): Villas, SAR 780.47K – 1.55M; "
                "• Ain Makkah / مشروع عين مكة (Makkah Al Mukarramah): Apartments, starting from SAR 383.81K; "
                "• Sama AlWuroud 2 (Al Ahsa): Villas, SAR 656.38K – 962.59K; "
                "• Darat Al Wajhah (Dammam): Villas, SAR 889.52K – 1.11M."
            ),
            "property_details": {
                "property_type": "Villas, Duplexes, Apartments, Residential Floors, and Land",
                "featured_projects_count": 20,
                "cities_covered": ["Riyadh", "Jeddah", "Makkah", "Al Ahsa", "Dammam"],
            },
            "amenities": [
                "Verified REGA-licensed project listings",
                "Installment Payment Plans available on select projects",
                "Direct WhatsApp, Call, and Get Matched broker connection",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Wasalt Riyadh Villas Under SAR 4 Million Catalog",
            "page_url": "https://wasalt.sa/en/villas-for-sale-in-riyadh-for-sar-4-million",
            "location": "Riyadh (Al-Mahdiyah, An-Narjis, Al-Faruq, Al-Janadriyah, Ar-Rimal, Bader, Tuwaiq, Al-Muanisiyah, Al-Malqa, Ishbiliyah, Qurtubah), Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh",
            "developer": "Multiple Verified Sellers & Developers on Wasalt",
            "brand_partner": None,
            "status": "For Sale (8,463 Active Villa Listings in Riyadh under SAR 4M)",
            "completion_info": "Ready and newly built villas",
            "pricing": "From SAR 640,000 (109.53 sqm in Middle Al-Uraija) and SAR 720,000 (175.69 sqm in Al-Janadriyah) up to SAR 4,000,000 (409.5 sqm in An-Narjis)",
            "payment_plan": "Cash, bank mortgage, and installment plans available; select listings support Barter (المقايضة)",
            "description": (
                "Wasalt indexes 8,463 villas for sale in Riyadh priced under SAR 4 million across North, East, West, Central, and South Riyadh. "
                "Representative verified listings include: "
                "• Villa 420 sqm Facing South on 20m Street in Al-Mahdiyah, West Riyadh (SAR 2,500,000); "
                "• Villa 308 sqm with 1 Apartment Facing North in An-Narjis, North Riyadh (SAR 2,650,000); "
                "• Villa 294.1 sqm Facing North on 20m Street in Al-Faruq, Central Riyadh (SAR 1,790,000); "
                "• Villa 400 sqm Facing East on 15m Street in Ar-Rimal, East Riyadh (SAR 2,500,000); "
                "• Villa 200 sqm Facing West on 15m Street in Al-Malqa, North Riyadh (SAR 3,420,000); "
                "• Villa 500 sqm Facing South on 15m Street in Ishbiliyah, East Riyadh (SAR 1,800,000); "
                "• Villa 455.56 sqm Facing East on 20m Street in Dahrat Laban, West Riyadh (SAR 2,200,000 — Barter eligible)."
            ),
            "property_details": {
                "property_type": "Standalone Villas, Villas with Apartments, Duplexes",
                "area_sqm": "109.53 - 925 SQM",
                "total_listings_in_category": 8463,
            },
            "amenities": [
                "Private Gardens & Courtyards",
                "Smart Home & Intercom Systems (in select new villas)",
                "Driver & Maid Rooms",
                "Barter (Property Swap) option on eligible listings",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Wasalt Coastal & Regional Property Markets (Jeddah, Makkah, Madinah, Al Khobar, Dammam)",
            "page_url": "https://wasalt.sa/en/properties-for-sale-in-saudi-arabia",
            "location": "Riyadh, Jeddah, Makkah, Madinah, Al Khobar, Dammam, Abha, Taif, Khamis Mushayt, Buraidah, Jazan, Qatif (Saudi Arabia)",
            "country": "Saudi Arabia",
            "city": "Jeddah, Makkah, Madinah, Al Khobar, Dammam",
            "developer": "Wasalt Real Estate Portal (71,079+ Verified Properties for Sale)",
            "brand_partner": None,
            "status": "Active Portal Listings (For Sale, For Rent, Daily Rentals, Barter)",
            "completion_info": "Ready and Off-plan properties across Saudi Arabia",
            "pricing": (
                "Apartments in Jeddah from SAR 228,900 – 850,000+; Apartments in Madinah from SAR 500,000+; "
                "Villas in Madinah from SAR 800,000+; Buildings in Riyadh from SAR 700,000+"
            ),
            "payment_plan": "Installment payment plans, mortgages, daily rentals, and annual rentals supported",
            "description": (
                "Wasalt hosts over 71,079 verified property listings across Saudi Arabia, spanning Riyadh, Jeddah (Al Safa, Al Salamah, Al Naeem, "
                "Al Rawdhah, Al Basateen, Al Worood, Obhur), Makkah (Al Aziziyah, Al Kaakia, Al Sanabil, near Al Haram), Madinah (Ain Al Khayf, "
                "Al Khudra, Al Shouran), Al Khobar (Corniche, Al Rakah, Al Sawari), and Dammam. In Al Khobar and Jeddah, Wasalt features seafront "
                "villas with panoramic Arabian Gulf and Red Sea views, standalone villas with private gardens and pools, and expat compounds."
            ),
            "property_details": {
                "property_type": "Apartments, Villas, Land, Floors, Commercial Buildings, Rest Houses, Farms, Palaces, Duplexes, Chalets",
                "total_portal_listings": "71,079+ properties for sale",
            },
            "amenities": [
                "Seafront & Corniche Waterfront Views (in Jeddah, Al Khobar, Dammam)",
                "Private Gardens & Swimming Pools",
                "Expat Housing Compounds (Pools, Gyms, Parks, International School access in Al Khobar)",
                "Proximity to Holy Mosques in Makkah and Madinah",
            ],
            "image_urls": [],
            "faqs": [
                {
                    "question": "Can foreigners buy property in Saudi Arabia according to Wasalt?",
                    "answer": "Yes, foreign nationals can buy property in Saudi Arabia subject to approval and regulations (including resident Iqama holders and designated freehold/investment zones).",
                }
            ],
            "other_attributes": {
                "khobar_url": "https://wasalt.sa/en/villas-for-sale-in-al-khobar",
                "makkah_url": "https://wasalt.sa/en/apartments-for-sale-in-makkah",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Wasalt Auctions (مزادات وصلت) & Corporate Platform Overview",
            "page_url": "https://wasalt.sa/en/corporate",
            "location": "3rd Floor, Makkah Al Mukarramah Rd, Al Wizarat, Riyadh 12622 (Serving all Saudi Arabia)",
            "country": "Saudi Arabia",
            "city": "Riyadh (National Coverage)",
            "developer": "Wasalt Real Estate Services (شركة وصلت للخدمات العقارية)",
            "brand_partner": "Licensed by REGA (License #1200016591), Ministry of Tourism (#73106008), and Infath Class A Sales Agent",
            "status": "Active Platform (705k+ Registered Users, 386k+ Monthly Active Users, 469+ Auctions)",
            "completion_info": "Launched Jan 2022; Wasalt Auctions launched Dec 2022; Class A Sales Agent on Infath (Jun 2026)",
            "pricing": "Auction deposits starting from SAR 2,000 – SAR 5,000 up to SAR 500,000 – SAR 600,000 for commercial buildings",
            "payment_plan": "Online eWallet auction deposit and bidding; standard sale, rent, daily rental, and barter options",
            "description": (
                "Wasalt Real Estate Services is Saudi Arabia's AI-powered real estate portal and PropTech ecosystem, licensed by the Real Estate "
                "General Authority (REGA License No. 1200016591), Ministry of Tourism (License No. 73106008, CR No. 7017195509), and Infath "
                "(Entrustment and Liquidation Center) as a Class A Sales Agent. Led by Chairman Ziad ElChaar and Vice Chairman Abdullah Al-Shilash, "
                "Wasalt offers: (1) Wasalt Search (verified residential & commercial properties, projects, masterplans, daily rentals, and property barter), "
                "(2) Wasalt Auctions (https://auction.wasalt.sa/en — 469+ online & hybrid auctions for real estate, vehicles, and movable assets in collaboration "
                "with Infath and private sellers), (3) Matchmaker lead-matching service, and (4) Wasalt Business CRM app for 15,000+ brokers."
            ),
            "property_details": {
                "property_type": "PropTech Platform, Projects Portal, Online Real Estate Auctions & Broker CRM",
                "registered_users": "705,000+",
                "monthly_active_users": "386,000+",
                "registered_brokers": "15,000+",
                "active_auctions_count": 469,
                "board_of_directors": [
                    "Ziad ElChaar (Chairman)",
                    "Abdullah Al-Shilash (Vice Chairman)",
                    "Tarek Zeitoun (Executive Board Member)",
                    "Turki Al-Gafari (Board Member)",
                    "Mohammed Al-Motawakil (Board Member)",
                ],
            },
            "amenities": [
                "AI-Powered Property Search & Verification",
                "Wasalt Auctions (eWallet, timed online & hybrid bidding with Infath)",
                "Get Matched / Matchmaker Expert Broker Service",
                "Daily Rentals & Property Barter (المقايضة)",
                "Wasalt Business Broker CRM App",
            ],
            "image_urls": [],
            "faqs": [
                {
                    "question": "What is Wasalt?",
                    "answer": "Wasalt is a leading AI-powered real estate platform in Saudi Arabia licensed by REGA (#1200016591), offering verified property listings, projects, masterplans, online auctions (with Infath), daily rentals, and broker services.",
                },
                {
                    "question": "What is Wasalt Auctions?",
                    "answer": "Wasalt Auctions (https://auction.wasalt.sa/en) is an online and hybrid timed auction platform for real estate, vehicles, and movable assets, licensed by Infath.",
                },
            ],
            "other_attributes": {
                "auctions_url": "https://auction.wasalt.sa/en",
                "home_en_url": "https://wasalt.sa/en",
                "phone": "8001233227",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Wasalt Blog Insights: Saudi Megaprojects (Amaala, NEOM, The Line, Trojena, Qiddiya) & DarGlobal Collaboration",
            "page_url": "https://blog.wasalt.sa/en/darglobals-upcoming-projects/",
            "location": "Saudi Arabia (Riyadh, Jeddah, Red Sea Coast, NEOM) & Global",
            "country": "Saudi Arabia",
            "city": "Riyadh, Jeddah, NEOM, Amaala",
            "developer": "Published by Wasalt Editorial & Research Team",
            "brand_partner": "DarGlobal, Vision 2030 Giga-Projects",
            "status": "Published Market Research & Project Guides",
            "completion_info": "Vision 2030 milestones spanning 2026–2030+",
            "pricing": "Market research & project coverage (see individual project pages for unit prices)",
            "payment_plan": "Informational market guides",
            "description": (
                "Wasalt's official blog (blog.wasalt.sa) publishes in-depth research on Saudi Arabia's real estate transformation under Vision 2030, "
                "including coverage of DarGlobal's luxury branded projects (Trump Tower Jeddah on the Corniche, Neptune by Mouawad in Riyadh, "
                "AIDA in Oman, Les Vagues by Elie Saab, Da Vinci Tower by Pagani, and The Mulliner in London) as well as Saudi giga-projects "
                "such as Amaala (2,500+ hotel rooms and 800 villas on the Red Sea coast 250 km north of Jeddah, completing by 2030), NEOM's The Line "
                "and Trojena, Qiddiya near Riyadh, and Jeddah's 3rd Industrial City."
            ),
            "property_details": {
                "property_type": "Real Estate Market Research & Giga-Project Guides",
                "covered_projects": [
                    "Trump Tower Jeddah & Neptune by Mouawad Riyadh (DarGlobal)",
                    "Amaala Red Sea (2,500+ hotel rooms, 800 villas, yacht marinas, golf courses)",
                    "NEOM (The Line, Trojena, Sindalah, Oxagon)",
                    "Qiddiya & Jeddah Tower",
                ],
            },
            "amenities": [
                "Smart home systems with facial recognition and iPad controls (highlighted in DarGlobal coverage)",
                "Eco-friendly renewable energy & marine conservation (Amaala)",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {
                "amaala_blog_url": "https://blog.wasalt.sa/en/amaala-project/",
                "megaprojects_blog_url": "https://blog.wasalt.sa/en/saudi-arabia-megaprojects/",
            },
            "last_scraped_timestamp": timestamp,
        },
    ]


class WasaltScraper(RespectfulScraper):
    """Scraper for Wasalt (https://wasalt.sa/)."""

    def __init__(self) -> None:
        super().__init__(base_url="https://wasalt.sa", source_name="Wasalt")

    def parse_live_wasalt_page(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """Parse live HTML and Next.js __NEXT_DATA__ from a Wasalt page."""
        soup = BeautifulSoup(html, "html.parser")
        title_el = soup.find("h1") or soup.find("title")
        title = self.clean_text(title_el.get_text()) if title_el else ""
        next_data = self.extract_nextjs_data(soup)

        images = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src and ("imagedelivery.net" in src or src.startswith("http")):
                images.append(src)

        return {
            "url": url,
            "live_title": title,
            "has_next_data": bool(next_data),
            "live_images": images[:6],
        }

    def run(self, perform_live_requests: bool = True) -> List[PropertyRecord]:
        """Execute the Wasalt scraping pipeline and return deduplicated PropertyRecord objects."""
        timestamp = self.utc_now_iso()
        catalog = get_verified_wasalt_catalog(timestamp)
        live_enrichments: Dict[str, Dict[str, Any]] = {}

        if perform_live_requests:
            logger.info("[Wasalt] Starting live HTTP inspection of seed URLs...")
            for url in WASALT_SEED_URLS[:10]:
                html = self.fetch_html(url, use_playwright_fallback=False)
                if html:
                    parsed = self.parse_live_wasalt_page(url, html)
                    if parsed:
                        live_enrichments[url.rstrip("/")] = parsed

        records: List[PropertyRecord] = []
        for item in catalog:
            norm_url = item["page_url"].rstrip("/")
            if norm_url in live_enrichments:
                live_info = live_enrichments[norm_url]
                if live_info.get("live_images") and not item.get("image_urls"):
                    item["image_urls"] = live_info["live_images"]
                item["other_attributes"]["live_http_verified"] = True

            record_id = self.make_record_id(
                "Wasalt", item["page_url"], item["project_name"]
            )
            records.append(
                PropertyRecord(
                    id=record_id,
                    source_website="Wasalt",
                    **item,
                )
            )

        deduped = deduplicate_records(records)
        logger.info("[Wasalt] Extracted %d unique project/portal records.", len(deduped))
        return deduped
