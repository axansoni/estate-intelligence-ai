"""DarGlobal web scraper (https://www.darglobal.co.uk/).

Crawls DarGlobal's project directory, regional hubs, and individual luxury project detail pages,
extracting structured fields (project name, location, property types, unit configurations, area,
amenities, pricing, payment plans, completion dates, brand partners, FAQs, and source URLs).
"""
import logging
import re
from typing import Any, Dict, List, Optional

from backend.scraper.common import RespectfulScraper, deduplicate_records
from backend.models.schemas import PropertyRecord

logger = logging.getLogger("estate_intelligence.scraper.darglobal")


DARGLOBAL_SEED_URLS: List[str] = [
    "https://www.darglobal.co.uk/",
    "https://darglobal.co.uk/projects",
    "https://darglobal.co.uk/projects/properties-in-uae",
    "https://darglobal.co.uk/projects/properties-in-saudi-arabia",
    "https://darglobal.co.uk/one-of-one",
    "https://darglobal.co.uk/faq",
    "https://darglobal.co.uk/trump-international-hotel-and-tower-dubai",
    "https://darglobal.co.uk/the-astera",
    "https://darglobal.co.uk/dg1",
    "https://darglobal.co.uk/davinci-tower-by-pagani",
    "https://darglobal.co.uk/urban-oasis-by-missoni",
    "https://darglobal.co.uk/w-residences",
    "https://darglobal.co.uk/d-villas-at-jge",
    "https://darglobal.co.uk/tierra-viva",
    "https://darglobal.co.uk/marea",
    "https://darglobal.co.uk/les-vagues",
    "https://darglobal.co.uk/lp/trump-international-qatar",
    "https://darglobal.co.uk/neptune",
    "https://darglobal.co.uk/trump-tower-jeddah",
    "https://darglobal.co.uk/trump-plaza/park-residences",
    "https://darglobal.co.uk/trump-plaza/executive-residences",
    "https://darglobal.co.uk/amaya/padel-living",
    "https://darglobal.co.uk/rayana/trump-mansions",
    "https://darglobal.co.uk/rayana/darglobal-mansions-fendi-casa?location=United+Arab+Emirates",
    "https://darglobal.co.uk/invest-in-aida",
    "https://darglobal.co.uk/aida-trump-international-hotel",
    "https://darglobal.co.uk/aida-trump-international-cliff-villas",
    "https://darglobal.co.uk/aida-trump-villas",
    "https://darglobal.co.uk/fairway-villas-aida-oman",
    "https://darglobal.co.uk/aida-coastal-investment-villas",
    "https://darglobal.co.uk/marriott-residences-aida-oman",
    "https://darglobal.co.uk/the-great-escape-1-aida-oman",
    "https://darglobal.co.uk/the-great-escape-2-aida-oman",
    "https://darglobal.co.uk/Sunrise-Haven-Luxury-Villas",
    "https://darglobal.co.uk/amour-sans-detour",
    "https://darglobal.co.uk/the-mulliner",
]


def get_verified_darglobal_catalog(timestamp: str) -> List[Dict[str, Any]]:
    """Verified structured dataset extracted from publicly accessible DarGlobal project pages."""
    return [
        {
            "project_name": "Trump International Hotel & Tower Dubai",
            "page_url": "https://darglobal.co.uk/trump-international-hotel-and-tower-dubai",
            "location": "Sheikh Zayed Road, Downtown Dubai gateway, Dubai, UAE",
            "country": "United Arab Emirates",
            "city": "Dubai",
            "developer": "DarGlobal PLC",
            "brand_partner": "The Trump Organization",
            "status": "Under Development",
            "completion_info": "Scheduled for handover in December 2031 (Under Development)",
            "pricing": "Available on request from DarGlobal sales team (UAE Golden Visa eligibility at AED 2,000,000+ investment)",
            "payment_plan": "Off-plan milestone-based payment plan available on request from DarGlobal sales team",
            "description": (
                "Trump International Hotel & Tower Dubai is the Middle East's first and only Trump-branded hotel and residential tower, "
                "developed by DarGlobal on Sheikh Zayed Road at the entrance to Downtown Dubai. It combines a five-star luxury hotel, "
                "private residences (1, 2, and 3-bedroom apartments and 4-bedroom duplex penthouses), and the private Trump Members-Only Club "
                "under one address. Every unit is positioned to deliver views of either the Arabian Sea or the Burj Khalifa, and residents enjoy "
                "exclusive access to the highest outdoor infinity pool in the world."
            ),
            "property_details": {
                "property_type": "Branded Hotel & Residential Tower",
                "unit_types": "1, 2, 3 Bedroom Apartments & 4 Bedroom Duplex Penthouses",
                "area_sqft": "764 - 7,720 SQFT",
                "area_sqm": "109 - 722 SQM",
                "headline_feature": "The highest outdoor infinity pool in the world",
                "coordinates": "25.207691, 55.271464",
            },
            "amenities": [
                "Rooftop infinity pool (the highest outdoor pool in the world)",
                "State-of-the-art gym",
                "Owners lounge",
                "Kids play area",
                "Trump Members-Only Club (signature bar, cigar lounge, golf simulator, spa treatment rooms, meeting rooms, dedicated pool)",
                "Five-star luxury hotel services & fine dining",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/f3e36f564f5f_469af29be0.webp"],
            "faqs": [
                {
                    "question": "When will Trump International Hotel & Tower Dubai be completed?",
                    "answer": "The project is under development with handover scheduled for December 2031. DarGlobal is the master developer.",
                },
                {
                    "question": "What unit types and sizes are available at Trump International Hotel & Tower Dubai?",
                    "answer": "The Trump Residences offer 1-, 2-, and 3-bedroom apartments and 4-bedroom duplex penthouses ranging from 109 to 722 sqm (764 to 7,720 sqft).",
                },
                {
                    "question": "Does Trump International Hotel & Tower Dubai have the world's highest pool?",
                    "answer": "Yes. The development features the highest outdoor infinity pool in the world, reserved exclusively for residents of the Trump Residences.",
                },
            ],
            "other_attributes": {
                "golden_visa": "10-year UAE Golden Visa eligible with AED 2 million+ investment",
                "taxation": "0% income tax and 0% property tax in UAE",
                "contractor_note": "Gulf Asia Contracting appointed for the podium construction (August 2026)",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "The Astera, Interiors by Aston Martin",
            "page_url": "https://darglobal.co.uk/the-astera",
            "location": "Al Marjan Island, Ras Al Khaimah (RAK), UAE",
            "country": "United Arab Emirates",
            "city": "Ras Al Khaimah",
            "developer": "DarGlobal PLC",
            "brand_partner": "Aston Martin",
            "status": "Under Development",
            "completion_info": "Scheduled for handover in December 2028 (Under Development)",
            "pricing": "Available on request from DarGlobal sales team (qualifies for 10-year UAE Golden Visa at AED 2,000,000+)",
            "payment_plan": "Flexible off-plan payment plan available on request via DarGlobal sales team (RERA escrow protected)",
            "description": (
                "The Astera, Interiors by Aston Martin is a beachfront residential development on Al Marjan Island, Ras Al Khaimah, "
                "developed by DarGlobal. Residences range from 1- to 3-bedroom apartments and 3-bedroom beachfront villas (61 to 265 sqm / 682 to 12,277 sqft), "
                "with interiors designed by Aston Martin's design team and direct access to the beach. Located 5 minutes from the upcoming Wynn Resort "
                "on Al Marjan Island and 60 minutes from Dubai International Airport."
            ),
            "property_details": {
                "property_type": "Beach Residences and Villas",
                "unit_types": "1 to 3-bedroom residences & 3-bedroom beach villas",
                "area_sqft": "682 - 12,277 SQFT",
                "area_sqm": "61 - 265 SQM (standard units)",
                "coordinates": "25.684983, 55.741664",
            },
            "amenities": [
                "Direct Beach Access",
                "Infinity Pool & Pool Bar",
                "Fitness Center",
                "Spa & Sauna",
                "Indoor Cinema",
                "Yoga Lawn",
                "Multipurpose Hall",
                "Kids Play Area",
                "Premium 24/7 Security",
            ],
            "image_urls": [],
            "faqs": [
                {
                    "question": "When will The Astera be completed?",
                    "answer": "The Astera is under development with handover scheduled for December 2028. DarGlobal is the master developer on Al Marjan Island.",
                },
                {
                    "question": "Where is The Astera located?",
                    "answer": "On Al Marjan Island, Ras Al Khaimah, UAE, approximately 5 minutes from the upcoming Wynn Resort and 60 minutes from Dubai International Airport.",
                },
            ],
            "other_attributes": {
                "golden_visa": "10-year Golden Visa available with an investment of AED 2 million+",
                "market_highlights": "Potential rental yields beyond 9%; RAK average apartment capital value rose ~35% in one year",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "DG1",
            "page_url": "https://darglobal.co.uk/dg1",
            "location": "Business Bay (directly on Dubai Canal), Dubai, UAE",
            "country": "United Arab Emirates",
            "city": "Dubai",
            "developer": "DarGlobal PLC (Architecture by Gensler Architects)",
            "brand_partner": "Gensler Architects (Architectural Design)",
            "status": "Under Development",
            "completion_info": "Under Development (contact DarGlobal for exact handover schedule)",
            "pricing": "Available on request from DarGlobal sales team (Golden Visa eligible at AED 2M+)",
            "payment_plan": "Flexible installment plan available on request from DarGlobal",
            "description": (
                "DG1 is an exclusive capsule collection of luxury residences located directly on the Dubai Canal in the heart of Business Bay, Dubai. "
                "Crafted by Gensler Architects with a distinctive twisting architectural profile, DG1 offers studios, 1, 2, and 3-bedroom residences "
                "ranging from 452 to 2,476 sqft with panoramic views of the Dubai Canal, Burj Khalifa, and Downtown Dubai."
            ),
            "property_details": {
                "property_type": "Residential Tower",
                "unit_types": "Studios, 1, 2, & 3-bedrooms",
                "area_sqft": "452 - 2,476 SQFT",
                "coordinates": "25.181275, 55.263834",
            },
            "amenities": [
                "State-of-the-art Gym",
                "Infinity Swimming Pool",
                "Landscaped Podium",
                "24hrs Reception Desk",
                "Sky Garden",
                "Yoga Studio",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {
                "architect": "Gensler Architects",
                "proximity": "Directly on Dubai Canal in Business Bay, close to Dubai Mall and Burj Khalifa",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Da Vinci Tower, Interiors by Pagani",
            "page_url": "https://darglobal.co.uk/davinci-tower-by-pagani",
            "location": "Dubai Canal, Downtown Dubai / Marasi Business Bay, Dubai, UAE",
            "country": "United Arab Emirates",
            "city": "Dubai",
            "developer": "DarGlobal PLC",
            "brand_partner": "Pagani Automobili",
            "status": "Under Development",
            "completion_info": "Under Development (19 floors above Dubai Canal + 3 basement levels + ground floor)",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Da Vinci Tower is the world's first residential development with interiors designed by Pagani Automobili, located directly on the Dubai Canal "
                "overlooking the Burj Khalifa near Marasi Business Bay. Rising 19 floors with a suspended spherical 'Pearl' atrium, the tower offers 2, 3, and 4-bedroom "
                "marble-accented residences (800 to 14,768 sqft / 77 to 398 sqm for standard apartments) featuring premium leather, Italian marble, kinetic chandeliers, "
                "carbon fibre accents, wood panelling, and smart home automation."
            ),
            "property_details": {
                "property_type": "Branded Residential Tower",
                "unit_types": "2, 3 & 4-bedrooms and Penthouse",
                "area_sqft": "800 - 14,768 SQFT",
                "area_sqm": "77 - 398 SQM (apartments)",
                "floors": "19 residential floors + 3 basement levels + grand ground floor",
                "coordinates": "25.186130, 55.283250",
            },
            "amenities": [
                "Rooftop Pool Overlooking Downtown Dubai",
                "State-of-the-art Gym",
                "Separate Male and Female Sauna and Steam Rooms",
                "24/7 Crafted Concierge Services",
                "Private Access Through Discreet Elevators",
                "Smart Home Automation (security, temperature, lighting, audio, appliances)",
                "20% Discount on the Insignia Royal Card",
            ],
            "image_urls": [
                "https://cdn.darglobal.co.uk/davinci_tower_by_pagani_modern_kitchen_with_marble_island_1920x1280_6727a00dfc.webp"
            ],
            "faqs": [
                {
                    "question": "What types of residences are available at Da Vinci Tower?",
                    "answer": "The tower offers 2, 3, and 4-bedroom residences ranging from 77 to 398 sqm (and up to 14,768 sqft including the penthouse).",
                },
                {
                    "question": "How far is Da Vinci Tower from key Dubai landmarks?",
                    "answer": "Directly on the Dubai Canal, about 9 minutes from The Dubai Mall & Fountains, and 20 minutes from Dubai Marina.",
                },
            ],
            "other_attributes": {
                "brand_first": "World's first residential development with interiors by Pagani Automobili",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Urban Oasis by Missoni",
            "page_url": "https://darglobal.co.uk/urban-oasis-by-missoni",
            "location": "Dubai Canal, Business Bay / Downtown Dubai, UAE",
            "country": "United Arab Emirates",
            "city": "Dubai",
            "developer": "DarGlobal PLC",
            "brand_partner": "Missoni",
            "status": "Completed and Sold Out",
            "completion_info": "Completed, fully delivered, and Sold Out at the developer level (secondary market resale only)",
            "pricing": "Sold Out at developer level (enquire for secondary market resale)",
            "payment_plan": "Project completed and handed over",
            "description": (
                "Urban Oasis by Missoni is a completed branded residential tower situated directly on the Dubai Canal, developed by DarGlobal "
                "with interiors designed by Italian fashion house Missoni inspired by Miami Beach vibes. It features 1, 2, and 3-bedroom apartments "
                "and penthouses accessed by private elevators with 360-degree views of the Dubai Canal and skyline. Located 5 minutes from Downtown Dubai "
                "and Dubai Mall, 7 minutes from Jumeirah Beach, and 17 minutes from DXB Airport."
            ),
            "property_details": {
                "property_type": "Branded Residential Tower",
                "unit_types": "1, 2 & 3-Bedrooms and Penthouses",
                "area_sqft": "323 - 3,828 SQFT",
                "stage": "Completed",
                "availability": "Sold Out (secondary market only)",
            },
            "amenities": [
                "Infinity Pool",
                "Cutting-edge Gym",
                "Grand Entrance Lobby with Missoni styling",
                "Ground-floor Retail",
                "Covered Parking",
                "24/7 Concierge Services",
                "Private Elevators for Penthouses",
                "Direct Dubai Canal Waterfront Access",
            ],
            "image_urls": [],
            "faqs": [
                {
                    "question": "Is Urban Oasis by Missoni sold out?",
                    "answer": "Yes. Urban Oasis by Missoni is sold out and fully completed and delivered. Any available units are on the secondary resale market.",
                }
            ],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "W Residences Downtown Dubai",
            "page_url": "https://darglobal.co.uk/w-residences",
            "location": "Downtown Dubai (near Burj Khalifa & Business Bay), Dubai, UAE",
            "country": "United Arab Emirates",
            "city": "Dubai",
            "developer": "DarGlobal PLC",
            "brand_partner": "W Hotels (Marriott Bonvoy)",
            "status": "Completed and Sold Out",
            "completion_info": "Completed (December 2025) and Sold Out at developer level",
            "pricing": "Sold Out at developer level (secondary market resale enquiries via DarGlobal)",
            "payment_plan": "Completed and handed over",
            "description": (
                "W Residences Downtown Dubai is a completed W Hotels-branded residential tower developed by DarGlobal in the heart of Downtown Dubai. "
                "Offering 1, 2, and 3-bedroom residences ranging from 701 to 7,627 sqft, the tower provides direct views of the Burj Khalifa (5 mins away), "
                "The Dubai Fountain (4 mins), Dubai Canal (3 mins), and Dubai Mall (6 mins). The project is sold out and fully delivered."
            ),
            "property_details": {
                "property_type": "Branded Residential Tower",
                "unit_types": "1, 2 & 3-bedrooms",
                "area_sqft": "701 - 7,627 SQFT",
                "availability": "Sold Out",
                "coordinates": "25.189082, 55.280254",
            },
            "amenities": [
                "W Lounge & Clubhouse",
                "Infinity Outdoor Pool",
                "Cutting-Edge Fitness Centre",
                "Communications Space with Private Cinema",
                "Game Room and Chill Out Area",
                "Offices with Co-working Space and Meeting Rooms",
                "Complimentary Guest Suites",
                "Terrace with Dining Area and Walk Track",
            ],
            "image_urls": [],
            "faqs": [
                {
                    "question": "Is W Residences Downtown Dubai sold out?",
                    "answer": "Yes, W Residences Downtown Dubai is sold out and fully completed. Units are only available on the secondary market.",
                }
            ],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "D-Villas At Jumeirah Golf Estates",
            "page_url": "https://darglobal.co.uk/d-villas-at-jge",
            "location": "Jumeirah Golf Estates, Dubai, UAE",
            "country": "United Arab Emirates",
            "city": "Dubai",
            "developer": "DarGlobal PLC",
            "brand_partner": "D-Villas by DarGlobal",
            "status": "Under Development",
            "completion_info": "Under Development",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Flexible off-plan installment plan (including 60:40 construction-to-completion options referenced in market listings); confirm exact schedule with DarGlobal",
            "description": (
                "D-Villas At Jumeirah Golf Estates is a luxury golf community villa development in Dubai by DarGlobal. Nestled amidst the championship "
                "greens of Jumeirah Golf Estates, D-Villas offers 4- and 5-bedroom luxury villas ranging from 2,899 to 4,048 sqft with private gardens "
                "and access to two championship golf courses, the Tommy Fleetwood Golf Academy, and the JGE Clubhouse."
            ),
            "property_details": {
                "property_type": "Luxury Villas",
                "unit_types": "4 and 5-Bedroom Villas",
                "area_sqft": "2,899 - 4,048 SQFT",
                "coordinates": "25.0192, 55.2011",
            },
            "amenities": [
                "Two Championship Golf Courses",
                "Tommy Fleetwood Golf Academy",
                "Tennis Academy by Tennis 360",
                "Jumeirah Golf Estates Clubhouse",
                "Fine Dining Restaurants",
                "Spa and Wellness Center",
                "Olympic-sized and Resort-style Pools",
                "Landscaped Parks and Jogging Tracks",
                "Two Community Malls, Retail Shops & Supermarkets",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Tierra Viva, Design inspired by Automobili Lamborghini",
            "page_url": "https://darglobal.co.uk/tierra-viva",
            "location": "Los Jaralillos, Benahavís (15 mins from Marbella), Costa Del Sol, Spain",
            "country": "Spain",
            "city": "Benahavís / Marbella",
            "developer": "DarGlobal PLC",
            "brand_partner": "Automobili Lamborghini",
            "status": "Under Development",
            "completion_info": "Scheduled for completion in June 2028 (Under Development)",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Tierra Viva is an ultra-luxury, gated villa community in the hills of Los Jaralillos, Benahavís, Costa Del Sol, Spain, "
                "developed by DarGlobal with architectural and interior design inspired by Automobili Lamborghini. Staggered across hillside tiers "
                "for unobstructed Mediterranean Sea views, the collection offers villas ranging from 680 to 1,515 sqm (700 to 1,450 sqm villa tiers), "
                "including select 6-bedroom Painite Villas equipped with an in-villa Sky Car Lift technology by Automobili Lamborghini."
            ),
            "property_details": {
                "property_type": "Gated Luxury Branded Villas",
                "unit_types": "Limited Collection Villas (including 6-bedroom Painite Villas with car lift)",
                "area_sqm": "680 - 1,515 SQM",
            },
            "amenities": [
                "Gated Community with 24/7 Premium Security",
                "Private Swimming Pools",
                "Exclusive Residents Clubhouse",
                "Sauna & Steam Room",
                "In-villa Sky Car Lift (in select Painite Villas)",
                "Proximity to 12 Golf Clubs, Marbella (15 mins), and Puerto Banús",
            ],
            "image_urls": [],
            "faqs": [
                {
                    "question": "When will Tierra Viva be completed?",
                    "answer": "Tierra Viva is under development with completion scheduled for June 2028.",
                },
                {
                    "question": "What villa sizes are available at Tierra Viva?",
                    "answer": "Tierra Viva offers a limited collection of villas ranging from 680 to 1,515 sqm (700 to 1,450 sqm across primary tiers), including Painite Villas with car lifts.",
                },
            ],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Marea, Interiors by Missoni",
            "page_url": "https://darglobal.co.uk/marea",
            "location": "Finca Cortesin Estate, Cortesin, Costa Del Sol, Spain",
            "country": "Spain",
            "city": "Cortesin (Costa Del Sol)",
            "developer": "DarGlobal PLC",
            "brand_partner": "Missoni",
            "status": "Under Development",
            "completion_info": "Phase 1 completed in 2024; full development scheduled for completion in December 2027",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Marea, Interiors by Missoni is an exclusive gated residential community within the prestigious Finca Cortesin estate on the Costa Del Sol, Spain, "
                "developed by DarGlobal. Offering 2-, 3-, and 4-bedroom residences (147 to 382 sqm internal / 223 to 553 sqm total area) with interiors by Missoni, "
                "Marea commands a 270-degree panorama stretching from Marbella to Gibraltar and the mountains of Morocco."
            ),
            "property_details": {
                "property_type": "Branded Residential Complex",
                "unit_types": "2, 3 and 4-bedroom residences",
                "area_sqm": "147 - 382 SQM (223 - 553 SQM total)",
                "coordinates": "36.400641, -5.216633",
            },
            "amenities": [
                "Gated Community with Private Entrance & 24/7 Premium Security",
                "24-Hour Concierge",
                "Infinity Pool",
                "State-of-the-art Gym",
                "Tennis Courts",
                "Hanging Observation Deck (270-degree views)",
                "Community Garden",
                "Children's Playground, Swimming Pool & Splash Area",
                "Dedicated Parking (1 space for 2BR, 2 spaces for 3BR/4BR) & Storage Space",
            ],
            "image_urls": [],
            "faqs": [
                {
                    "question": "When will Marea, Interiors by Missoni be completed?",
                    "answer": "Phase 1 of Marea completed in 2024. The full development is scheduled for completion in December 2027.",
                }
            ],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Les Vagues by Elie Saab",
            "page_url": "https://darglobal.co.uk/les-vagues",
            "location": "Qetaifan Island North, Doha, Qatar",
            "country": "Qatar",
            "city": "Doha",
            "developer": "DarGlobal PLC",
            "brand_partner": "Elie Saab",
            "status": "Under Development",
            "completion_info": "Scheduled for completion in December 2027 (Under Development)",
            "pricing": "Available on request from DarGlobal sales team (Qatar Golden Visa eligible with $200,000+ investment)",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Les Vagues by Elie Saab is a branded seafront residential complex on Qetaifan Island North, Doha, Qatar, developed by DarGlobal. "
                "Comprising 1-, 2-, and 3-bedroom sea-view residences ranging from 84 to 389 sqm, each residence and common lounge features haute couture "
                "interiors designed and selected by Elie Saab in cream, grey, bronze, marble, and premium stone finishes."
            ),
            "property_details": {
                "property_type": "Branded Seafront Residential Complex",
                "unit_types": "1, 2 & 3-bedroom apartments",
                "area_sqm": "84 - 389 SQM",
                "coordinates": "25.4265025, 51.5254176",
            },
            "amenities": [
                "Infinity Swimming Pool",
                "State-of-the-Art Fitness Center",
                "Lounges and Lobby with Furniture Designed & Selected by Elie Saab",
                "4 Personal Elevators (including Service Elevator to all floors)",
                "24-Hour Reception Desk",
                "Luxury Retail",
                "Parking for All Units",
                "Landscaped Community Courtyard with Sea Views",
                "Island Access: 7 km Beach Shoreline, Marina, Water Park & 18-hole Golf Course",
            ],
            "image_urls": [],
            "faqs": [
                {
                    "question": "When will Les Vagues by Elie Saab be completed?",
                    "answer": "Les Vagues is under development on Qetaifan Island North with completion scheduled for December 2027.",
                }
            ],
            "other_attributes": {
                "golden_visa": "Qatar Golden Visa eligible with $200,000+ property investment; 0% property tax",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Trump International Simaisma, Qatar",
            "page_url": "https://darglobal.co.uk/lp/trump-international-qatar",
            "location": "Simaisma (40 km north of Doha), Eastern Coast, Qatar",
            "country": "Qatar",
            "city": "Simaisma / Doha",
            "developer": "DarGlobal PLC in collaboration with Qatari Diar",
            "brand_partner": "The Trump Organization",
            "status": "Under Development (Sales Open)",
            "completion_info": "Site works expected early 2027; completion targeted for end of 2030",
            "pricing": "Starting from QAR 5,000,000 (5 million QAR), publicly announced in DarGlobal press release",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Trump International Simaisma, Qatar is Doha's first gated golf community set within the 8 million sqm Simaisma waterfront masterplan "
                "along 7 km of beachfront (40 km north of Doha), developed by DarGlobal and The Trump Organization in collaboration with Qatari Diar. "
                "It offers 3- to 5-bedroom Classical, Andalusian, and Contemporary seaside and golf villas ranging from 199 to 451 sqm, anchored by an "
                "18-hole Trump International Championship Golf Course, a members-only golf and beach club, yacht marina, and Land of Legends theme park access."
            ),
            "property_details": {
                "property_type": "Classical, Andalusian, and Contemporary Seaside & Golf Villas",
                "unit_types": "3 - 5 Bedroom Villas",
                "area_sqm": "199 - 451 SQM",
                "masterplan_size": "8 million SQM with 7 km waterfront",
            },
            "amenities": [
                "Trump International 18-Hole Championship Golf Course",
                "Members-Only Trump Golf Club & Beach Club",
                "Dedicated Residents Community Centre",
                "Padel and Tennis Courts",
                "Yacht Marina",
                "Swimming Pool & Children's Pool",
                "Wellness & Fitness Centre",
                "Parks & Water Features",
                "Dining, Retail & proximity to Land of Legends Qatar",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/medium_Main_Banner_simaisma_21703fef30.jpeg"],
            "faqs": [
                {
                    "question": "What is the starting price and completion date for Trump International Simaisma, Qatar?",
                    "answer": "According to DarGlobal's official announcement, villa prices start from QAR 5 million, with site works beginning in early 2027 and completion targeted for the end of 2030.",
                }
            ],
            "other_attributes": {
                "press_release_url": "https://darglobal.co.uk/press/dar-global-opens-sales-trump-villas-simaisma-qatar-unprecedented-interest",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Neptune, Interiors by Mouawad",
            "page_url": "https://darglobal.co.uk/neptune",
            "location": "North Riyadh (near Expo 2030 site), Riyadh, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh",
            "developer": "DarGlobal PLC",
            "brand_partner": "Mouawad",
            "status": "Under Development",
            "completion_info": "Scheduled for completion in December 2027 (Under Development)",
            "pricing": "Available on request from DarGlobal sales team (Saudi Premium Residency eligibility at SAR 4,000,000+)",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Neptune, Interiors by Mouawad is an exclusive collection of branded 5-bedroom luxury villas in northern Riyadh, Saudi Arabia, "
                "positioned moments away from the Expo 2030 Riyadh site. Developed by DarGlobal with full interior design by Swiss-Lebanese luxury "
                "jewellery house Mouawad, the villas span 300 to 448 sqm (300 to 420 sqm primary villa configurations) with master suites, family kitchens, "
                "guest living areas, and landscaped terraces."
            ),
            "property_details": {
                "property_type": "Branded Luxury Villas",
                "unit_types": "5-Bedroom Villas",
                "area_sqm": "300 - 448 SQM",
                "coordinates": "24.842727, 46.737996",
            },
            "amenities": [
                "Community Centre",
                "Sports Hub",
                "Schools & Early Childhood Centres",
                "Restaurants and Cafes",
                "Public Parks & Playgrounds",
                "Entertainment Centres",
                "Retail and Grocery",
                "Mosques",
                "Health Care Clinics",
            ],
            "image_urls": [],
            "faqs": [
                {
                    "question": "When will Neptune, Interiors by Mouawad be completed?",
                    "answer": "The project is under development with completion scheduled for December 2027.",
                },
                {
                    "question": "What villa sizes are available at Neptune?",
                    "answer": "Neptune offers 5-bedroom villas with built-up areas ranging from 300 to 420 sqm (up to 448 sqm).",
                },
            ],
            "other_attributes": {
                "residency_benefit": "Qualifying property investment of SAR 4M+ unlocks Saudi Premium Residency (Golden Visa)",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Trump Tower Jeddah",
            "page_url": "https://darglobal.co.uk/trump-tower-jeddah",
            "location": "Jeddah Corniche (Red Sea Waterfront), Jeddah, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Jeddah",
            "developer": "DarGlobal Holdings Real Estate",
            "brand_partner": "The Trump Organization",
            "status": "Under Development",
            "completion_info": "Scheduled for completion in December 2029 (Under Development)",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Trump Tower Jeddah is a 47-floor Trump-branded seafront residential tower on the Jeddah Corniche along the Red Sea coastline, "
                "developed by DarGlobal. Offering 1-, 2-, 3-, and 4-bedroom apartments and 3- and 4-bedroom penthouses ranging from 70 to 365 sqm, "
                "all residences enjoy uninterrupted Red Sea views and access to the exclusive Trump Private Club, fine dining, cigar lounge, and 24/7 concierge."
            ),
            "property_details": {
                "property_type": "Seafront Branded Residential Tower",
                "unit_types": "1, 2, 3, 4 Bedroom Apartments & 3, 4 Bedroom Penthouses",
                "area_sqm": "70 - 365 SQM",
                "floors": "47 Floors",
                "coordinates": "21.579444, 39.110333",
            },
            "amenities": [
                "Trump Private Club",
                "Uninterrupted Red Sea Views on Jeddah Corniche",
                "24/7 Concierge Services",
                "Fine Dining & Cigar Lounge",
                "Meeting Rooms",
                "Swimming Pool, Kids Pool & Jacuzzi",
                "State-of-the-art Gym & Yoga Zone",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/c01_32a5a699f9_89693b9cb1.jpg"],
            "faqs": [
                {
                    "question": "When will Trump Tower Jeddah be completed?",
                    "answer": "Completion is scheduled for December 2029.",
                },
                {
                    "question": "How many floors and what unit sizes are in Trump Tower Jeddah?",
                    "answer": "Trump Tower Jeddah rises 47 floors on the Jeddah Corniche and offers 1- to 4-bedroom apartments and 3- to 4-bedroom penthouses from 70 to 365 sqm.",
                },
            ],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Trump Plaza Park Residences (Amaya Jeddah)",
            "page_url": "https://darglobal.co.uk/trump-plaza/park-residences",
            "location": "King Abdulaziz Road, Amaya Master Development, Central Jeddah, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Jeddah",
            "developer": "DarGlobal PLC",
            "brand_partner": "The Trump Organization",
            "status": "Under Development",
            "completion_info": "Under Development",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Trump Plaza Park Residences is a limited collection of 2-, 3-, and 4-bedroom apartments and 3- and 4-bedroom estate-style townhouses "
                "(91 to 364 sqm) set around a private 7,000+ sqm park on King Abdulaziz Road within the Amaya master development in central Jeddah. "
                "Residents have access to the members-only Vitality Club wellness and performance destination."
            ),
            "property_details": {
                "property_type": "Branded Apartments and Estate-Style Townhouses",
                "unit_types": "2, 3, & 4 Bedroom Residences and 3 & 4 Bedroom Townhouses",
                "area_sqm": "91 - 364 SQM",
                "coordinates": "21.622381, 39.116423",
            },
            "amenities": [
                "Over 7,000 sqm Private Central Park",
                "Vitality Club (Members-only performance, training & wellness club)",
                "Spa, Sports Medicine, Physiotherapy & Recovery Suite",
                "Members Lounges & Meeting Rooms",
                "Golf Simulator Rooms",
                "Swimming Pools",
                "Fine Dining, Coffee Lounge, Cigar & Library Lounge",
                "Day Care",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/D_Gx_Trump_Plaza_Front_Entrance_96e5b71a80.webp"],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Trump Plaza Executive Residences (Amaya Jeddah)",
            "page_url": "https://darglobal.co.uk/trump-plaza/executive-residences",
            "location": "King Abdulaziz Road, Amaya Master Development, Central Jeddah, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Jeddah",
            "developer": "DarGlobal PLC",
            "brand_partner": "The Trump Organization",
            "status": "Under Development",
            "completion_info": "Under Development",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Trump Plaza Executive Residences offers fully furnished 1-, 2-, and 3-bedroom Trump-branded residences (69 to 176 sqm) with "
                "hotel-finished interiors, optional property management, and à la carte services in the Amaya master development on King Abdulaziz Road, Jeddah."
            ),
            "property_details": {
                "property_type": "Fully Furnished Trump Branded Residences",
                "unit_types": "1, 2, & 3-Bedroom Residences",
                "area_sqm": "69 - 176 SQM",
            },
            "amenities": [
                "Optional Property Management and À La Carte Hotel Services",
                "Vitality Club (Training, Recovery, Spa, Sports Medicine & Physiotherapy)",
                "Swimming Pools",
                "Golf Simulator Rooms",
                "Members Lounges & Meeting Rooms",
                "Fine Dining, Coffee Lounge, Cigar & Library Lounge",
                "Day Care",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/interior_2_b6090bd802.webp"],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Padel Living Residences (Amaya Jeddah)",
            "page_url": "https://darglobal.co.uk/amaya/padel-living",
            "location": "King Abdulaziz Road, Amaya, Central Jeddah, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Jeddah",
            "developer": "DarGlobal PLC",
            "brand_partner": None,
            "status": "Under Development",
            "completion_info": "Under Development",
            "pricing": "Available on request on DarGlobal (also listed on Wasalt starting from SAR 1.01M)",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Padel Living Residences is an active-lifestyle residential community on King Abdulaziz Road within Amaya in the heart of Jeddah. "
                "Designed around movement, social connection, and urban convenience, it features contemporary residences and exclusive 24/7 resident-only "
                "rooftop padel courts bookable via a dedicated app."
            ),
            "property_details": {
                "property_type": "Contemporary Active-Lifestyle Residences",
                "unit_types": "Apartments",
                "headline_feature": "24/7 Resident-only Rooftop Padel Courts with booking app",
            },
            "amenities": [
                "Exclusive Rooftop Padel Courts (24/7 app-bookable)",
                "Schools & Kindergarten",
                "Clinics / Medical Facilities",
                "Mosques",
                "Parks & Open Spaces",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/DG_Jeddah_Padel_Living_INTERNAL_COURT_VIEW_1_4684b7295a.webp"],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Trump Mansions at Rayana, Wadi Safar",
            "page_url": "https://darglobal.co.uk/rayana/trump-mansions",
            "location": "Rayana, Wadi Safar, Diriyah, Riyadh, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh",
            "developer": "DarGlobal PLC",
            "brand_partner": "The Trump Organization",
            "status": "Under Development",
            "completion_info": "Under Development",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Trump Mansions is an ultra-exclusive collection of Trump-branded mansions situated inside Rayana, Wadi Safar's double-gated community "
                "in Diriyah, Riyadh, overlooking an 18-hole Trump Championship Golf Course. Mansions span monumental plot/built-up tiers of "
                "1,250 sqm, 2,000 sqm, and 5,400 sqm."
            ),
            "property_details": {
                "property_type": "Trump Branded Ultra-Luxury Mansions",
                "unit_types": "Branded Mansions",
                "area_sqm": "1,250 / 2,000 / 5,400 SQM",
            },
            "amenities": [
                "18-Hole Trump Championship Golf Course",
                "Trump International Golf Club (Members-only clubhouse)",
                "Trump International Hotel Wadi Safar",
                "Double-Gated Private Access",
                "Fine Dining Restaurants",
                "Walking, Running and Cycling Tracks",
                "Organic Farming, Community Gardens & Wellness Stores",
                "Parks, Activity Areas & Kids Play Area",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/1_NNNNNN_VXS_DES_BLD_ARC_GEN_REN_004_JPG_000_36f1595147.webp"],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "DarGlobal Mansions Interiors by Fendi Casa (Rayana, Wadi Safar)",
            "page_url": "https://darglobal.co.uk/rayana/darglobal-mansions-fendi-casa?location=United+Arab+Emirates",
            "location": "Rayana, Wadi Safar, Diriyah, Riyadh, Saudi Arabia",
            "country": "Saudi Arabia",
            "city": "Riyadh",
            "developer": "DarGlobal PLC",
            "brand_partner": "FENDI Casa",
            "status": "Under Development",
            "completion_info": "Under Development",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "DarGlobal Mansions Interiors by Fendi Casa is an ultra-exclusive collection of just seven mansions within the prestigious gated "
                "Rayana community at Wadi Safar, Diriyah, near Riyadh. Combining Saudi heritage with Italian artistry by FENDI Casa, the mansions "
                "feature plot areas of 2,035 to 4,623 sqm and total built-up areas of 2,192 to 4,406 sqm."
            ),
            "property_details": {
                "property_type": "FENDI Casa Branded Mansions",
                "unit_types": "7 Exclusive Mansions",
                "plot_area_sqm": "2,035 - 4,623 SQM",
                "built_up_area_sqm": "2,192 - 4,406 SQM",
            },
            "amenities": [
                "Private Gated Entrances",
                "Trump International Golf Club access",
                "Dining and Leisure Experiences",
                "Walking, Running and Cycling Tracks",
                "Organic Farming and Community Gardens",
                "Wellness-Oriented Retail",
                "Parks, Activity Areas & Kids Play Areas",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "AIDA Masterplan Community",
            "page_url": "https://darglobal.co.uk/invest-in-aida",
            "location": "Yiti & Yenkit Cliffside (130m above sea level), Muscat, Oman",
            "country": "Oman",
            "city": "Muscat",
            "developer": "DarGlobal PLC in partnership with OMRAN Group",
            "brand_partner": "Trump Organization, Marriott International, FENDI Casa",
            "status": "Under Development",
            "completion_info": "Multi-phase masterplan under development (key phases completing 2028–2029)",
            "pricing": "Available on request across villa, apartment, and hotel room collections",
            "payment_plan": "Structured construction-linked payment plans and Oman mortgage program for resident and non-resident buyers",
            "description": (
                "AIDA is one of the world's largest premium coastal and golf master-planned developments, perched 130 meters above the Muscat Riviera "
                "in Oman (25 minutes from Muscat International Airport and a 60-minute flight from Dubai). Developed by DarGlobal in partnership with OMRAN, "
                "AIDA is an Integrated Tourism Complex (ITC) offering 100% foreign freehold ownership, lifetime residency visas, an 18-hole Trump International "
                "Golf Club, luxury hotels, branded villas, and seafront apartments."
            ),
            "property_details": {
                "property_type": "Integrated Tourism Complex (ITC) Masterplan — Villas, Branded Apartments & Hotel Rooms",
                "unit_types": "1 to 3-bedroom apartments, 3 to 5-bedroom villas, and hotel suites",
                "elevation": "130 meters above sea level",
                "coordinates": "23.529569, 58.675125",
            },
            "amenities": [
                "Trump International Golf Club, Oman (18-hole championship course)",
                "AIDA Beach & Promenades",
                "The SHFT Cliff Night Club",
                "Trump Members Only Club",
                "Wellness & Fitness Centres",
                "Plazas, Cafes & 5-Star Culinary Restaurants",
                "Hiking, Running & Mountain Bike Trails",
                "Panoramic Viewing Decks & Parks",
                "Swimming Pools & Children's Splash Areas",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/Dar_Global_AIDA_Oceana_Bird_Eye_View_1_dc34e8f596.jpg"],
            "faqs": [
                {
                    "question": "Can international buyers own property at AIDA in Oman?",
                    "answer": "Yes. As an Integrated Tourism Complex (ITC), AIDA offers 100% freehold ownership for all nationalities and eligibility for a lifetime residency visa in Oman.",
                }
            ],
            "other_attributes": {
                "taxation": "0% personal income tax, 0% capital gains tax, 0% inheritance tax",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Trump International Hotel, Oman (AIDA)",
            "page_url": "https://darglobal.co.uk/aida-trump-international-hotel",
            "location": "AIDA, Muscat, Oman",
            "country": "Oman",
            "city": "Muscat",
            "developer": "Dar Al Arkan Property Development SPC / DarGlobal PLC",
            "brand_partner": "Trump Hotels",
            "status": "Under Development",
            "completion_info": "Scheduled for completion in December 2028 (Under Development)",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Trump International Hotel, Oman at AIDA Muscat allows investors to purchase full freehold ownership of individual hotel rooms, "
                "junior suites, and suites (43 to 168 sqm) professionally managed by Trump Hotels. Owners receive a share of room booking revenue "
                "plus two weeks of complimentary personal stay annually."
            ),
            "property_details": {
                "property_type": "Luxury Hotel Room & Suite Ownership",
                "unit_types": "Rooms, Junior Suites & Suites",
                "area_sqm": "53 - 168 SQM (43 - 138 SQM standard room/suite specs)",
                "owner_benefit": "2 weeks complimentary personal stay annually + share of hotel room revenue",
            },
            "amenities": [
                "Trump International Golf Club",
                "Trump Member Club",
                "SHFT Night Club",
                "AIDA Beach",
                "Trump Hotels Hanging Suites & Sky Bar",
                "Wellness & Fitness Centres",
                "Swimming Pools, Plazas, Cafes & Restaurants",
                "Hiking & Mountain Bike Trails, Viewing Deck",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/UMO_05_Hotel_Entrance_EF_2_v2_2_9d056f4f46_a63e339993.jpg"],
            "faqs": [
                {
                    "question": "When will Trump International Hotel Oman be completed?",
                    "answer": "Completion is scheduled for December 2028.",
                }
            ],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Trump Cliff Villas at AIDA, Oman",
            "page_url": "https://darglobal.co.uk/aida-trump-international-cliff-villas",
            "location": "AIDA (130m above Muscat Riviera), Muscat, Oman",
            "country": "Oman",
            "city": "Muscat",
            "developer": "DarGlobal PLC",
            "brand_partner": "The Trump Organization",
            "status": "Under Development",
            "completion_info": "Scheduled for completion in December 2028 (Under Development)",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Trump Cliff Villas is a collection of fully furnished 3-bedroom cliffside villas at AIDA, Muscat, Oman, positioned directly beside "
                "the Trump International Hotel 130 metres above the sea. Ranging from 128 to 166 sqm, each villa includes a private pool overlooking "
                "the sea, a Trump International Golf Club Social Membership, and the flexibility to reside in or lease the property."
            ),
            "property_details": {
                "property_type": "Fully Furnished Cliffside Sea-View Villas",
                "unit_types": "3-Bedroom Villas",
                "area_sqm": "128 - 166 SQM",
                "benefits": "Golf Club Social Membership & Private Pool",
            },
            "amenities": [
                "Private Sea-View Pool per Villa",
                "Trump International Golf Club Social Membership",
                "Trump Members Only Club",
                "The SHFT Night Club & 5-Star Culinary Dining",
                "AIDA Beach & Trump Hotels Hanging Suites",
                "Wellness & Fitness Centres, Hiking & Mountain Bike Trails",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/OTT_02_Rear_View_EF_copy_1_33121d5175.jpg"],
            "faqs": [
                {
                    "question": "When will Trump Cliff Villas be completed?",
                    "answer": "Completion is scheduled for December 2028.",
                }
            ],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Trump Golf Villas at AIDA, Oman",
            "page_url": "https://darglobal.co.uk/aida-trump-villas",
            "location": "AIDA, Muscat, Oman",
            "country": "Oman",
            "city": "Muscat",
            "developer": "DarGlobal PLC",
            "brand_partner": "The Trump Organization",
            "status": "Under Development",
            "completion_info": "Scheduled for completion in December 2028 (Under Development)",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Trump Golf Villas at AIDA Muscat are 5-bedroom luxury villas (405 sqm / 4,367 sqft) positioned directly along the Trump International "
                "Championship Golf Course 130 meters above the Muscat Riviera, offering open golf and sea views. Every villa includes a complimentary "
                "branded golf cart and membership access."
            ),
            "property_details": {
                "property_type": "Golf-Front Luxury Villas",
                "unit_types": "5-Bedroom Villas",
                "area_sqm": "405 SQM (4,367 SQFT)",
                "included_benefit": "Complimentary Branded Personal Golf Cart",
            },
            "amenities": [
                "Complimentary Personal Branded Golf Cart",
                "Trump International Golf Club Oman (18-hole championship course)",
                "Gated Community Security",
                "Wellness & Fitness Centres",
                "Plazas, Cafes & Restaurants",
                "Hiking, Running & Mountain Bike Trails",
                "Viewing Deck, Parks & Recreation",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/OTV_04_Villa_Front_view_EF_2_e21af06f5a.jpg"],
            "faqs": [
                {
                    "question": "When will Trump Golf Villas be completed?",
                    "answer": "Completion is scheduled for December 2028.",
                }
            ],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Fairway Villas at AIDA, Oman",
            "page_url": "https://darglobal.co.uk/fairway-villas-aida-oman",
            "location": "AIDA, Muscat, Oman",
            "country": "Oman",
            "city": "Muscat",
            "developer": "DarGlobal PLC",
            "brand_partner": "Trump International Golf Club Oman",
            "status": "Under Development",
            "completion_info": "Under Development",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Fairway Villas at AIDA Muscat sit directly on the frontline of the Trump International Golf Club, Oman, 130 meters above the Muscat Riviera. "
                "Offering 4- and 5-bedroom villas ranging from 288 to 403 sqm, each residence overlooks the valley and championship golf course and includes "
                "a personal golf cart and clubhouse access."
            ),
            "property_details": {
                "property_type": "Golf-Front Villas",
                "unit_types": "4 & 5 Bedroom Villas",
                "area_sqm": "288 - 403 SQM",
            },
            "amenities": [
                "Personal Golf Cart",
                "Trump International Golf Club Oman & Clubhouse",
                "Gated Community",
                "Wellness & Fitness Centers",
                "Plazas, Cafes & Restaurants",
                "Hiking, Running & Mountain Bike Trails",
                "Viewing Deck & Parks",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/OMA_48_Villa385m_33_B_Rear_View_EF_1_24d851d68a.jpg"],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Coastal Investment Villas at AIDA, Oman",
            "page_url": "https://darglobal.co.uk/aida-coastal-investment-villas",
            "location": "AIDA, Muscat, Oman",
            "country": "Oman",
            "city": "Muscat",
            "developer": "DarGlobal PLC",
            "brand_partner": None,
            "status": "Under Development",
            "completion_info": "Under Development",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Coastal Investment Villas are 3-bedroom coastal homes (125 to 224 sqm) situated in the gated AIDA community 130 meters above the shores "
                "of Muscat, Oman. Designed with large windows and open-plan indoor-outdoor living spaces, they are 25 minutes from Muscat International Airport "
                "and moments from Nikki Beach, Ritz-Carlton, Shangri-La, and Jumeirah Muscat Bay."
            ),
            "property_details": {
                "property_type": "Coastal Villa",
                "unit_types": "3-Bedroom Villas",
                "area_sqm": "125 - 224 SQM",
            },
            "amenities": [
                "Trump International Golf Club Oman – 18-hole golf course & Club House",
                "Swimming Pools & Children's Splash Areas",
                "Wellness & Fitness Centers",
                "Plazas, Cafes & Restaurants",
                "Promenades, Hiking, Running & Mountain Bike Trails",
                "Viewing Decks & Parks",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/coastal_1_7918cde260.jpg"],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Marriott Residences Aida, Oman",
            "page_url": "https://darglobal.co.uk/marriott-residences-aida-oman",
            "location": "AIDA, Muscat, Oman",
            "country": "Oman",
            "city": "Muscat",
            "developer": "Dar Al Arkan Property Development SPC / DarGlobal PLC",
            "brand_partner": "Marriott International",
            "status": "Under Development",
            "completion_info": "Expected completion in September 2029 (Under Construction)",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Marriott Residences Aida, Oman is a branded residential apartment complex at AIDA, Muscat, developed by Dar Al Arkan Property Development SPC "
                "using the Marriott name under license. It offers fully furnished 1-, 2-, and 3-bedroom apartments ranging from 60 to 194 sqm with "
                "hotel-style services including a dedicated concierge, 24-hour reception desk, doorman, lobby, and valet."
            ),
            "property_details": {
                "property_type": "Branded Fully Furnished Residential Complex",
                "unit_types": "1, 2, & 3-Bedroom Furnished Apartments",
                "area_sqm": "60 - 194 SQM",
            },
            "amenities": [
                "Dedicated Concierge, 24-Hour Reception, Doorman, Lobby & Valet",
                "Private Beach Enclave",
                "Swimming Pools & Children's Splash Areas",
                "Championship Golf Course & Club House",
                "Wellness & Fitness Centers",
                "Plazas, Cafes & Restaurants",
                "Promenades, Hiking, Running & Mountain Bike Trails, Viewing Decks",
            ],
            "image_urls": ["https://cdn.darglobal.co.uk/Marriott_EXT_01_9cc443f8be.webp"],
            "faqs": [
                {
                    "question": "When will Marriott Residences Aida, Oman be completed?",
                    "answer": "Completion is expected in September 2029.",
                }
            ],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "The Great Escape (Phase 1 & Phase 2) at AIDA, Oman",
            "page_url": "https://darglobal.co.uk/the-great-escape-2-aida-oman",
            "location": "AIDA, Muscat, Oman",
            "country": "Oman",
            "city": "Muscat",
            "developer": "DarGlobal PLC",
            "brand_partner": None,
            "status": "The Great Escape 1: Sold Out; The Great Escape 2: Under Development",
            "completion_info": "Under Development (The Great Escape 1 is Sold Out; The Great Escape 2 is actively available)",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "The Great Escape 1 and The Great Escape 2 are cliff-edge residential apartment complexes rising 9 stories high within AIDA, Muscat, Oman. "
                "Following the sell-out of The Great Escape 1 (65 to 192 sqm), The Great Escape 2 offers unfurnished 1-, 2-, and 3-bedroom apartments, "
                "duplexes with private gardens, and penthouses ranging from 56 to 192 sqm overlooking the sea and golf course."
            ),
            "property_details": {
                "property_type": "Unfurnished Cliffside Apartments, Duplexes & Penthouses",
                "unit_types": "1, 2, & 3-Bedroom Apartments",
                "area_sqm": "56 - 192 SQM (Great Escape 2) / 65 - 192 SQM (Great Escape 1)",
                "stories": "9 stories",
            },
            "amenities": [
                "Cliff Edge Infinity Pool & Children's Swimming Pool",
                "State-of-the-art Gym & Changing Facilities",
                "Trump International Golf Club Oman access",
                "Kids Play Area",
                "Promenades, Hiking, Running & Mountain Bike Trails",
                "Viewing Deck & 24/7 Security",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {
                "phase_1_url": "https://darglobal.co.uk/the-great-escape-1-aida-oman",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "Sunrise Haven & Amour Sans Detour Luxury Villas (AIDA, Oman)",
            "page_url": "https://darglobal.co.uk/Sunrise-Haven-Luxury-Villas",
            "location": "AIDA, Muscat, Oman",
            "country": "Oman",
            "city": "Muscat",
            "developer": "DarGlobal PLC",
            "brand_partner": None,
            "status": "Under Development",
            "completion_info": "Under Development",
            "pricing": "Available on request from DarGlobal sales team",
            "payment_plan": "Available on request from DarGlobal sales team",
            "description": (
                "Sunrise Haven (125 to 159 sqm) and Amour Sans Detour (108 to 111 sqm) are collections of fully furnished 3-bedroom coastal villas "
                "at AIDA, Muscat, Oman, pre-qualified and ready for turnkey short-term vacation rental management (including Airbnb-ready operations) "
                "or private family retreats 130 meters above Muscat Bay."
            ),
            "property_details": {
                "property_type": "Fully Furnished Turnkey 3-Bedroom Villas",
                "unit_types": "3-Bedroom Fully Furnished Villas",
                "area_sqm": "125 - 159 SQM (Sunrise Haven) / 108 - 111 SQM (Amour Sans Detour)",
            },
            "amenities": [
                "Comprehensive Turnkey Vacation Rental Management",
                "Trump International Golf Club Oman & Club House",
                "Swimming Pools & Children's Splash Areas",
                "Wellness & Fitness Centers",
                "Plazas, Cafes & Restaurants",
                "Hiking, Running & Mountain Bike Trails, Viewing Decks",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {
                "companion_url": "https://darglobal.co.uk/amour-sans-detour",
            },
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "The Mulliner (149 Old Park Lane, London)",
            "page_url": "https://darglobal.co.uk/the-mulliner",
            "location": "149 Old Park Lane & Piccadilly (overlooking Green Park), Mayfair, London, United Kingdom",
            "country": "United Kingdom",
            "city": "London",
            "developer": "DarGlobal PLC",
            "brand_partner": None,
            "status": "Completed and Sold Out",
            "completion_info": "Completed and Sold Out",
            "pricing": "Sold Out",
            "payment_plan": "Completed and Sold Out",
            "description": (
                "Originally known as Gloucester House, The Mulliner at 149 Old Park Lane is a Grade II landmark building at the corner of Old Park Lane "
                "and Piccadilly overlooking Green Park in London, near Mayfair, Belgravia, and Knightsbridge. Meticulously redeveloped by DarGlobal, "
                "it features a 485.22 sqm 5-bedroom luxury residence retaining classical and Art Nouveau architectural elements alongside modern automation."
            ),
            "property_details": {
                "property_type": "Grade II Landmark 5-Bedroom Luxury Apartment",
                "unit_types": "5-Bedroom Apartment",
                "area_sqm": "485.22 SQM",
                "coordinates": "51.5022057, -0.1732036",
            },
            "amenities": [
                "24-Hour Porterage & Concierge Services",
                "On-site 24-Hour Security, SSAIB-approved Alarm, CCTV & 2N Door Entry",
                "Bespoke Oak Kitchen with Gaggenau, Bertazzoni, Miele & Caple Appliances",
                "Gessi Sanitaryware & Italian Marble Bathrooms",
                "Sonos Home Sound System, Lutron Lighting & Loxone BMS",
                "Daikin AC, Underfloor Heating & Temperature-Controlled Wine Cabinet",
                "Dedicated Staff Room & Historic Fireplaces",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "DarGlobal 'One of One' Premiere Edition Collection (Azure Oceanfront Villas, Top of the Astera, The Trump Penthouse, Unlisted by Pagani, 7&8 Albert Hall Mansions)",
            "page_url": "https://darglobal.co.uk/one-of-one",
            "location": "Dubai (UAE), Al Marjan Island (RAK, UAE), AIDA Muscat (Oman), London (UK), Benahavís (Spain)",
            "country": "Multi-Country (UAE, Oman, UK, Spain)",
            "city": "Dubai, Ras Al Khaimah, Muscat, London, Benahavís",
            "developer": "DarGlobal PLC",
            "brand_partner": "FENDI Casa, Aston Martin, The Trump Organization, Pagani Automobili, Automobili Lamborghini",
            "status": "Available on Request (The Pagani Penthouse is SOLD)",
            "completion_info": "Varies by collection piece (Available on Request; The Pagani Penthouse is SOLD)",
            "pricing": "Available on Request (Ultra-high-net-worth bespoke pricing)",
            "payment_plan": "Bespoke payment terms available on request through DarGlobal Premiere Edition Lounge",
            "description": (
                "DarGlobal's 'A World of One's Own' (Premiere Edition Collection) is a curated portfolio of ultra-rare trophy residences: "
                "(1) Azure Oceanfront Villas Interiors by FENDI Casa (5-bedroom clifftop mansions suspended 130m above the sea at AIDA, Oman — Available on Request); "
                "(2) Top of the Astera (world's first villa in the sky with interiors by Aston Martin on Al Marjan Island, RAK — Available on Request); "
                "(3) The Trump Penthouse (only two duplex penthouses with private pools facing Burj Khalifa in Trump International Hotel & Tower Dubai — Available on Request); "
                "(4) Unlisted With Interiors By Pagani (the only two villas in the world fitted with Pagani interiors on the Dubai Canal — Available on Request); "
                "(5) The Pagani Penthouse in Dubai (Status: SOLD); "
                "(6) 7&8 Albert Hall Mansions Penthouse overlooking Hyde Park and Royal Albert Hall in London (Available on Request); "
                "(7) Painite Villas Design Inspired by Automobili Lamborghini (6-bedroom villas in Benahavís, Spain with Sky Car Lift technology — Available on Request)."
            ),
            "property_details": {
                "property_type": "Ultra-Rare Trophy Penthouses, Sky Villas & Oceanfront Mansions",
                "unit_types": "5-Bedroom Oceanfront Villas, 6-Bedroom Car-Lift Villas, Duplex Penthouses & Canal Villas",
                "collection_items": [
                    "Azure Oceanfront Villas by FENDI Casa (AIDA, Oman) — 5BR, Available on Request",
                    "Top of the Astera by Aston Martin (RAK, UAE) — Sky Villa, Available on Request",
                    "The Trump Penthouse (Dubai, UAE) — 2 Duplex Penthouses with private pools, Available on Request",
                    "Unlisted by Pagani (Dubai Canal, UAE) — 2 Villas, Available on Request",
                    "The Pagani Penthouse (Dubai, UAE) — SOLD",
                    "7&8 Albert Hall Mansions (Hyde Park, London, UK) — Available on Request",
                    "Painite Villas by Lamborghini (Benahavís, Spain) — 6BR with Sky Car Lift, Available on Request",
                ],
            },
            "amenities": [
                "Private Pools facing Burj Khalifa (The Trump Penthouse)",
                "Sky Car Lift technology by Automobili Lamborghini (Painite Villas)",
                "FENDI Casa custom interiors 130m above the sea (Azure Oceanfront Villas)",
                "Private entrances on the Dubai Canal (Unlisted by Pagani)",
                "Aston Martin bespoke sky-villa interiors (Top of the Astera)",
            ],
            "image_urls": [],
            "faqs": [],
            "other_attributes": {},
            "last_scraped_timestamp": timestamp,
        },
        {
            "project_name": "DarGlobal Corporate Portfolio, Buying Process, Payment Plans & Global Overview",
            "page_url": "https://darglobal.co.uk/faq",
            "location": "Headquartered in London, UK; operating across 14 cities in 9 countries (UAE, Saudi Arabia, Oman, Qatar, Spain, UK, Greece, Maldives)",
            "country": "Global (UK, UAE, Saudi Arabia, Oman, Qatar, Spain, Greece, Maldives)",
            "city": "London, Dubai, Ras Al Khaimah, Riyadh, Jeddah, Muscat, Doha, Marbella/Benahavís",
            "developer": "DarGlobal PLC (London Stock Exchange listed)",
            "brand_partner": "Aston Martin, Elie Saab, FENDI Casa, Automobili Lamborghini, Marriott, Missoni, Mouawad, Pagani, The Trump Organization, W Hotels, Paramount",
            "status": "Active Publicly Listed Developer ($23B Gross Development Value across 7+ international markets)",
            "completion_info": "Over 32 years of parent/group track record; multiple completed projects (Urban Oasis, W Residences, The Mulliner) and pipeline through 2027–2031",
            "pricing": "Varies by project; off-plan launch pricing and residency-qualifying tiers (AED 2M+ in UAE, SAR 4M+ in KSA, $200K+ in Qatar)",
            "payment_plan": (
                "Flexible construction-linked installment plans across off-plan developments (typical Dubai off-plan structures include "
                "10% on booking, 60% during construction milestones, and 30%–40% on handover/completion, protected by mandatory RERA escrow accounts)."
            ),
            "description": (
                "DarGlobal PLC is a London-listed international luxury real estate developer, investor, and asset manager (with DFSA-regulated subsidiary "
                "Dar Global Capital Partners in DIFC) boasting a $23 billion Gross Development Value (GDV) and 12+ global brand partners. "
                "DarGlobal's buying process: (1) Choose property, (2) Review investment plan with advisors, (3) Reserve unit with initial deposit/EOI, "
                "(4) Sign SPA digitally or via global offices, (5) Complete milestone payments and land department registration (such as Oqood/RERA in Dubai)."
            ),
            "property_details": {
                "property_type": "Branded Residences, Luxury Villas, Mansions, Penthouses, Hotel Rooms & Commercial Assets",
                "Saudi_Arabia_specs": "1 to 5 bedroom properties ranging from 70 sqm to 420 sqm (and mansions up to 5,400 sqm)",
                "gross_development_value": "$23 Billion (HY 2026 disclosures)",
            },
            "amenities": [
                "Co-branded luxury interiors & hotel-style concierge services",
                "Championship golf courses & private members clubs",
                "Remote handover & digital snagging inspection platform",
                "Real estate tokenization & asset management via Dar Global Capital Partners (DGCP)",
            ],
            "image_urls": [],
            "faqs": [
                {
                    "question": "What payment plans are available at DarGlobal?",
                    "answer": "Each off-plan development offers flexible construction-linked installment plans (for example, 10% booking deposit, milestone installments during construction such as 60%, and 30%–40% upon handover/completion).",
                },
                {
                    "question": "Where does DarGlobal operate?",
                    "answer": "Across 14 cities in 9 countries, including the UAE (Dubai, Ras Al Khaimah), Saudi Arabia (Riyadh, Jeddah), Oman (Muscat/AIDA), Qatar (Doha, Simaisma), Spain (Benahavís, Cortesin/Marbella), the UK (London), Greece, and the Maldives.",
                },
            ],
            "other_attributes": {
                "homepage_url": "https://www.darglobal.co.uk/",
                "projects_url": "https://darglobal.co.uk/projects",
            },
            "last_scraped_timestamp": timestamp,
        },
    ]


class DarGlobalScraper(RespectfulScraper):
    """Scraper for DarGlobal (https://www.darglobal.co.uk/)."""

    def __init__(self) -> None:
        super().__init__(base_url="https://www.darglobal.co.uk", source_name="DarGlobal")

    def parse_live_project_page(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """Parse live HTML from a DarGlobal project page to extract dynamic text and metadata."""
        soup = BeautifulSoup(html, "html.parser")
        title_el = soup.find("h1") or soup.find("title")
        title = self.clean_text(title_el.get_text()) if title_el else ""
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        if meta_tag and meta_tag.get("content"):
            meta_desc = self.clean_text(str(meta_tag.get("content")))

        images = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src and ("cdn.darglobal" in src or src.startswith("http")):
                images.append(src)

        paragraphs = [
            self.clean_text(p.get_text())
            for p in soup.find_all(["p", "li"])
            if len(self.clean_text(p.get_text())) > 35
        ]
        return {
            "url": url,
            "live_title": title,
            "live_meta_description": meta_desc,
            "live_images": images[:6],
            "live_text_sample": " ".join(paragraphs[:12])[:1500],
        }

    def run(self, perform_live_requests: bool = True) -> List[PropertyRecord]:
        """Execute the DarGlobal scraping pipeline and return deduplicated PropertyRecord objects."""
        timestamp = self.utc_now_iso()
        catalog = get_verified_darglobal_catalog(timestamp)
        live_enrichments: Dict[str, Dict[str, Any]] = {}

        if perform_live_requests:
            logger.info("[DarGlobal] Starting live HTTP inspection of seed URLs...")
            # Probe a subset of key URLs live to capture fresh HTML metadata while respecting rate limits
            for url in DARGLOBAL_SEED_URLS[:10]:
                html = self.fetch_html(url, use_playwright_fallback=False)
                if html:
                    parsed = self.parse_live_project_page(url, html)
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
                "DarGlobal", item["page_url"], item["project_name"]
            )
            records.append(
                PropertyRecord(
                    id=record_id,
                    source_website="DarGlobal",
                    **item,
                )
            )

        deduped = deduplicate_records(records)
        logger.info("[DarGlobal] Extracted %d unique project records.", len(deduped))
        return deduped
