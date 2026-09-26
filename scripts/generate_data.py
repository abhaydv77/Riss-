"""Generate realistic synthetic creator-brand marketplace data.

Creates:
    data/brands.json   (10 brand campaign briefs)
    data/creators.json (40 creator profiles)

The dataset includes strong matches, poor matches, ambiguous matches,
budget mismatches, audience mismatches, geography mismatches,
niche mismatches, platform mismatches, and creator-size mismatches.
"""
from __future__ import annotations

import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")


def main() -> None:
    random.seed(42)
    creators = make_creators()
    brands = make_brands()

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "creators.json"), "w", encoding="utf-8") as f:
        json.dump(creators, f, indent=2, ensure_ascii=False)
    with open(os.path.join(DATA_DIR, "brands.json"), "w", encoding="utf-8") as f:
        json.dump(brands, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(creators)} creators and {len(brands)} brands")
    print("  -> data/creators.json")
    print("  -> data/brands.json")


# ---------------------------------------------------------------------------
# CREATOR DATA
# ---------------------------------------------------------------------------

def make_creators() -> list[dict]:
    return [
        # ---- FITNESS NICHE ----
        make_creator(
            "c01", "Priya Sharma", "fitness", ["sports", "wellness"],
            "Certified CrossFit athlete and nutrition coach based in Mumbai. "
            "I create workout routines, meal plans, and transformation stories "
            "for people who want to build real strength and healthy habits.",
            "Mumbai, India", ["Hindi", "English"], ["instagram", "youtube"],
            185_000, 0.042, 320_000, "18-30", {"female": 0.72, "male": 0.28},
            ["India", "UAE", "Singapore"], ["workout", "nutrition", "healthy lifestyle"],
            "energetic and motivational", "₹15,000–₹50,000",
            ["fitness", "sports", "health apps"],
            ["gym", "running", "yoga"], "4-5 posts/week"
        ),
        make_creator(
            "c02", "Alex Rivera", "fitness", ["lifestyle", "travel"],
            "Los Angeles based fitness model sharing gym tips, supplement reviews, "
            "and behind-the-scenes gym life. Focused on making fitness accessible "
            "for busy professionals who want to stay in shape.",
            "Los Angeles, USA", ["English"], ["instagram", "tiktok"],
            420_000, 0.038, 890_000, "25-34", {"female": 0.55, "male": 0.45},
            ["US", "Canada", "UK"], ["workout", "gym", "fitness"],
            "confident and aspirational", "₹50,000–₹150,000",
            ["sportswear", "supplements", "fitness apps"],
            ["gym", "running"], "6 posts/week"
        ),
        make_creator(
            "c03", "Deepika Joshi", "fitness", ["beauty", "skincare"],
            "Yoga instructor and wellness advocate from Bangalore. I blend "
            "mindfulness with physical fitness. My content covers yoga flows, "
            "skincare routines, and holistic living for mindful millennials.",
            "Bangalore, India", ["English", "Kannada"], ["instagram", "youtube"],
            95_000, 0.051, 145_000, "25-34", {"female": 0.85, "male": 0.15},
            ["India", "Singapore"], ["yoga", "skincare", "wellness"],
            "calm and authentic", "₹5,000–₹15,000",
            ["wellness", "skincare", "fitness"],
            ["yoga", "pilates"], "5 posts/week"
        ),
        # Fitness creator, wrong audience (too old)
        make_creator(
            "c04", "Robert Müller", "fitness", ["bodybuilding"],
            "German bodybuilder and powerlifting coach with 15 years of experience. "
            "I help 40-plus men build muscle and maintain strength. Content focuses "
            "on heavy lifting, joint health, and progressive overload.",
            "Berlin, Germany", ["German", "English"], ["youtube", "instagram"],
            310_000, 0.029, 480_000, "35-44", {"male": 0.88, "female": 0.12},
            ["Germany", "Austria", "Switzerland"], ["bodybuilding", "strength training"],
            "serious and educational", "₹15,000–₹50,000",
            ["sports nutrition", "gym equipment"],
            ["bodybuilding", "powerlifting"], "4 posts/week"
        ),
        # ---- BEAUTY / SKINCARE NICHE ----
        make_creator(
            "c05", "Sofia Chen", "beauty", ["skincare", "lifestyle"],
            "Skincare enthusiast and licensed esthetician from Seoul. I review "
            "K-beauty products, share dermatologist-approved routines, and create "
            "glass-skin content for women aged 18-30 who love skincare culture.",
            "Seoul, South Korea", ["Korean", "English"], ["instagram", "youtube", "tiktok"],
            280_000, 0.055, 520_000, "18-24", {"female": 0.92, "male": 0.08},
            ["South Korea", "Japan", "Singapore"], ["skincare", "beauty", "k-beauty"],
            "gorgeous and detail-oriented", "₹15,000–₹50,000",
            ["beauty brands", "skincare", "cosmetics"],
            ["skincare", "makeup"], "daily posts"
        ),
        make_creator(
            "c06", "Meera Patel", "beauty", ["fashion", "lifestyle"],
            "Mumbai-based beauty and fashion creator. I create makeup tutorials, "
            "outfit planning content, and brand partnerships that feel genuine. "
            "My audience trusts my honest reviews and everyday style tips.",
            "Mumbai, India", ["Hindi", "English"], ["instagram", "youtube"],
            150_000, 0.048, 275_000, "18-30", {"female": 0.78, "male": 0.22},
            ["India", "UAE"], ["beauty", "fashion", "lifestyle"],
            "vibrant and relatable", "₹10,000–₹30,000",
            ["beauty", "fashion", "jewelry"],
            ["makeup", "fashion"], "5-6 posts/week"
        ),
        # Beauty creator, wrong geography (European luxury brand)
        make_creator(
            "c07", "Chloe Dubois", "beauty", ["luxury", "fashion"],
            "Paris-based luxury beauty and fashion influencer. I partner with "
            "haute couture and high-end skincare brands. My content features "
            "exclusive launches, spa retreats, and European beauty standards.",
            "Paris, France", ["French", "English"], ["instagram", "youtube"],
            520_000, 0.031, 950_000, "25-34", {"female": 0.82, "male": 0.18},
            ["France", "UK", "Italy"], ["luxury beauty", "fashion", "travel"],
            "luxe and aspirational", "₹50,000–₹150,000",
            ["luxury cosmetics", "high-end skincare"],
            ["luxury", "beauty"], "3 posts/week"
        ),
        # ---- GAMING NICHE ----
        make_creator(
            "c08", "Kai Tanaka", "gaming", ["tech", "entertainment"],
            "Tokyo-based gaming streamer and tech reviewer. I cover AAA game releases, "
            "esports tournaments, and hardware reviews. My content is energetic and "
            "gen-z friendly with strong community engagement.",
            "Tokyo, Japan", ["Japanese", "English"], ["youtube", "tiktok"],
            680_000, 0.062, 1_200_000, "18-24", {"male": 0.75, "female": 0.25},
            ["Japan", "US", "UK"], ["gaming", "tech", "esports"],
            "high-energy and funny", "₹20,000–₹50,000",
            ["gaming brands", "tech gadgets", "energy drinks"],
            ["gaming", "tech reviews"], "daily streams"
        ),
        make_creator(
            "c09", "Noah Smith", "gaming", ["fitness"],
            "Vancouver-based creator who bridges gaming and fitness. I create "
            "content about gaming setups, posture health for gamers, and "
            "esports fitness routines. Perfect for brands targeting the gaming "
            "lifestyle market.",
            "Vancouver, Canada", ["English"], ["youtube", "tiktok"],
            120_000, 0.045, 210_000, "18-24", {"male": 0.70, "female": 0.30},
            ["Canada", "US"], ["gaming", "fitness", "tech"],
            "quirky and authentic", "₹5,000–₹15,000",
            ["gaming peripherals", "ergonomic furniture"],
            ["gaming", "fitness"], "4 posts/week"
        ),
        # Gaming creator, wrong audience (parents)
        make_creator(
            "c10", "Linda Johansson", "gaming", ["parenting", "family"],
            "Stockholm-based mom blogger who covers family-friendly gaming. "
            "I review age-appropriate games and share parenting tips around "
            "screen time. My audience is parents looking for safe gaming options.",
            "Stockholm, Sweden", ["Swedish", "English"], ["youtube", "instagram"],
            85_000, 0.035, 130_000, "30-44", {"female": 0.88, "male": 0.12},
            ["Sweden", "Norway", "Denmark"], ["family gaming", "parenting", "education"],
            "warm and trustworthy", "₹5,000–₹15,000",
            ["family brands", "educational games"],
            ["family", "parenting"], "3 posts/week"
        ),
        # ---- FOOD / TRAVEL NICHE ----
        make_creator(
            "c11", "Liam O'Brien", "food", ["travel", "photography"],
            "Dublin-based food photographer and travel creator. I create visually "
            "stunning content featuring street food, restaurant reviews, and "
            "culinary adventures. My reels and stories showcase food culture "
            "from around the world.",
            "Dublin, Ireland", ["English"], ["instagram", "youtube", "tiktok"],
            230_000, 0.044, 410_000, "25-34", {"male": 0.55, "female": 0.45},
            ["Ireland", "UK", "US"], ["food", "travel", "photography"],
            "adventurous and cinematic", "₹15,000–₹40,000",
            ["food brands", "travel companies", "camera gear"],
            ["food", "travel"], "5 posts/week"
        ),
        make_creator(
            "c12", "Ananya Rao", "food", ["fitness", "nutrition"],
            "Delhi-based nutritionist and recipe creator. I create healthy Indian "
            "recipes, meal prep guides, and nutrition education content. "
            "My audience loves practical, easy-to-follow wellness recipes."
            "I partner with health food brands and supplement companies.",
            "Delhi, India", ["Hindi", "English"], ["instagram", "youtube"],
            175_000, 0.047, 310_000, "25-34", {"female": 0.75, "male": 0.25},
            ["India", "Singapore", "UAE"], ["healthy food", "nutrition", "fitness"],
            "educational and warm", "₹10,000–₹30,000",
            ["health food", "nutrition supplements", "cooking appliances"],
            ["cooking", "nutrition", "recipes"], "5 posts/week"
        ),
        # Food creator, wrong niche (luxury travel, not food)
        make_creator(
            "c13", "Henrik Larsen", "food", ["luxury", "travel"],
            "Copenhagen-based luxury travel creator. I feature five-star hotels, "
            "private yacht experiences, and premium dining at Michelin-starred "
            "restaurants. My content is aspirational and targets high-income "
            "travelers aged 30-50.",
            "Copenhagen, Denmark", ["Danish", "English"], ["youtube", "instagram"],
            340_000, 0.028, 580_000, "30-44", {"male": 0.50, "female": 0.50},
            ["Denmark", "Norway", "Switzerland"], ["luxury travel", "fine dining", "hotels"],
            "premium and sophisticated", "₹20,000–₹50,000",
            ["luxury travel brands", "hotel chains"],
            ["travel", "luxury"], "2 posts/week"
        ),
        # ---- TECH NICHE ----
        make_creator(
            "c14", "Ethan Park", "tech", ["gaming", "finance"],
            "San Francisco-based tech reviewer and gadget unboxer. I cover "
            "consumer electronics, fintech apps, and productivity tools. "
            "My audience is tech-savvy professionals aged 22-35 who want "
            "honest, in-depth product reviews.",
            "San Francisco, USA", ["English"], ["youtube", "instagram"],
            450_000, 0.039, 780_000, "25-34", {"male": 0.68, "female": 0.32},
            ["US", "Canada", "Australia"], ["tech", "consumer electronics", "fintech"],
            "analytical and clear", "₹20,000–₹60,000",
            ["tech brands", "consumer electronics", "fintech"],
            ["tech reviews", "unboxing"], "4 posts/week"
        ),
        make_creator(
            "c15", "Zoe Kim", "tech", ["fashion", "beauty"],
            "NYC-based creator blending tech and beauty. I review smart mirrors, "
            "AI skincare devices, and wearable tech for fashion-conscious women. "
            "My content is aesthetic and informative, appealing to women who "
            "love both technology and beauty.",
            "New York, USA", ["English"], ["instagram", "youtube", "tiktok"],
            190_000, 0.052, 360_000, "20-30", {"female": 0.85, "male": 0.15},
            ["US", "Canada"], ["tech", "beauty", "fashion"],
            "trendy and innovative", "₹10,000–₹30,000",
            ["beauty tech", "wearables", "consumer electronics"],
            ["tech", "beauty"], "5 posts/week"
        ),
        # Tech creator, wrong audience (too old)
        make_creator(
            "c16", "Walter Chen", "tech", ["finance"],
            "Austin-based fintech consultant and tech educator for seniors. "
            "I create content about digital banking, online security, and "
            "technology for older adults. My mission is to make tech accessible "
            "for everyone regardless of age.",
            "Austin, USA", ["English"], ["youtube", "blog"],
            95_000, 0.033, 160_000, "55-65", {"male": 0.45, "female": 0.55},
            ["US"], ["fintech", "digital literacy", "senior tech"],
            "patient and educational", "₹5,000–₹15,000",
            ["fintech", "insurance", "healthtech"],
            ["fintech", "education"], "3 posts/week"
        ),
        # ---- LIFESTYLE / FASHION NICHE ----
        make_creator(
            "c17", "Ivy Lopez", "fashion", ["lifestyle", "beauty"],
            "Barcelona-based fashion influencer and personal style consultant. "
            "I create outfit inspiration, wardrobe guides, and sustainable "
            "fashion content. My audience is style-conscious women aged 20-35 "
            "who want practical fashion advice.",
            "Barcelona, Spain", ["Spanish", "English"], ["instagram", "tiktok"],
            260_000, 0.041, 440_000, "20-30", {"female": 0.82, "male": 0.18},
            ["Spain", "France", "Italy"], ["fashion", "sustainability", "beauty"],
            "minimal and elegant", "₹15,000–₹40,000",
            ["fashion brands", "sustainable fashion", "accessories"],
            ["fashion", "lifestyle"], "5 posts/week"
        ),
        make_creator(
            "c18", "Maya Singh", "fashion", ["fitness", "sports"],
            "Mumbai-based athleisure and streetwear creator. I blend athletic "
            "wear with everyday style. Perfect for sportswear brands looking "
            "to reach active, fashion-forward young women.",
            "Mumbai, India", ["Hindi", "English"], ["instagram", "youtube"],
            310_000, 0.044, 530_000, "18-28", {"female": 0.78, "male": 0.22},
            ["India", "UAE", "Singapore"], ["fashion", "fitness", "athleisure"],
            "bold and street-style", "₹15,000–₹40,000",
            ["sportswear", "athleisure brands", "footwear"],
            ["fashion", "fitness"], "6 posts/week"
        ),
        # Fashion creator, wrong size (too small)
        make_creator(
            "c19", "Finn O'Connor", "fashion", ["lifestyle"],
            "Melbourne-based lifestyle creator just starting out. I have a small "
            "but growing audience interested in sustainable fashion and "
            "conscious consumerism. Great for micro-influencer campaigns "
            "and authentic content.",
            "Melbourne, Australia", ["English"], ["instagram"],
            8_500, 0.068, 22_000, "18-24", {"female": 0.70, "male": 0.30},
            ["Australia"], ["sustainable fashion", "lifestyle", "thrifting"],
            "authentic and grassroots", "₹1,000–₹5,000",
            ["eco brands", "sustainable products"],
            ["fashion", "sustainability"], "daily posts"
        ),
        # ---- CREATORS WITH DELIBERATE MISMATCHES ----
        # Correct niche but wrong audience
        make_creator(
            "c20", "David Kim", "fitness", ["tech"],
            "Seattle-based tech fitness creator making AI-powered workout apps. "
            "My primary audience is tech professionals aged 40-55 who want "
            "to optimize their fitness routines with data and wearables.",
            "Seattle, USA", ["English"], ["youtube", "tiktok"],
            270_000, 0.035, 460_000, "40-54", {"male": 0.60, "female": 0.40},
            ["US", "Canada"], ["fitness", "tech", "wearables"],
            "data-driven and precise", "₹20,000–₹60,000",
            ["fitness apps", "wearables", "tech gadgets"],
            ["fitness", "tech"], "4 posts/week"
        ),
        # Correct audience but wrong niche
        make_creator(
            "c21", "Hana Ali", "parenting", ["lifestyle"],
            "London-based parenting creator with a primarily young adult audience. "
            "I cover pregnancy, toddler care, and work-life balance. "
            "My audience is primarily women aged 18-30, making them a great "
            "match for lifestyle brands targeting young women.",
            "London, UK", ["English"], ["instagram", "youtube"],
            195_000, 0.046, 340_000, "18-28", {"female": 0.90, "male": 0.10},
            ["UK", "Ireland"], ["parenting", "lifestyle", "family"],
            "warm and nurturing", "₹10,000–₹30,000",
            ["baby products", "maternity brands"],
            ["parenting", "family"], "5 posts/week"
        ),
        # Budget mismatch - very expensive creator for a micro budget brand
        make_creator(
            "c22", "Victoria Stone", "luxury", ["beauty", "fashion"],
            "London-based luxury lifestyle influencer with millions of followers. "
            "I partner exclusively with premium and luxury brands. My rate "
            "reflects my elite audience and premium positioning.",
            "London, UK", ["English"], ["instagram", "youtube"],
            1_800_000, 0.025, 3_200_000, "25-34", {"female": 0.80, "male": 0.20},
            ["UK", "US", "France"], ["luxury", "beauty", "fashion"],
            "glamorous and high-end", "₹150,000–₹500,000",
            ["luxury brands", "premium cosmetics", "high fashion"],
            ["luxury", "beauty"], "3 posts/week"
        ),
        # Creator from wrong geography
        make_creator(
            "c23", "Raj Kapoor", "fitness", ["sports"],
            "Mumbai-based sports fitness creator covering cricket, badminton, "
            "and local sports events. My audience is almost entirely India-based "
            "and I create content in Hindi for the domestic market.",
            "Mumbai, India", ["Hindi"], ["youtube", "instagram"],
            220_000, 0.040, 380_000, "18-30", {"male": 0.65, "female": 0.35},
            ["India"], ["sports", "fitness", "cricket"],
            "passionate and energetic", "₹10,000–₹30,000",
            ["sports brands", "fitness equipment"],
            ["sports", "fitness"], "5 posts/week"
        ),
        # Platform mismatch - brand wants TikTok, creator only on blog
        make_creator(
            "c24", "Grace Murray", "fitness", ["nutrition"],
            "Chicago-based nutrition and wellness writer. I create long-form blog "
            "articles and email newsletters about fitness nutrition, meal planning, "
            "and healthy eating habits. I do not create short-form video content.",
            "Chicago, USA", ["English"], ["blog"],
            75_000, 0.038, 95_000, "25-34", {"female": 0.70, "male": 0.30},
            ["US", "Canada"], ["nutrition", "fitness", "wellness"],
            "informative and evidence-based", "₹5,000–₹15,000",
            ["health food", "nutrition supplements"],
            ["nutrition", "fitness"], "3 blog posts/week"
        ),
        # Size mismatch - too small for the brand's requirements
        make_creator(
            "c25", "Sam Torres", "fitness", ["lifestyle"],
            "Miami-based fitness creator with a modest following. I create "
            "home workout content and fitness tips for beginners. Growing "
            "organically with a loyal community.",
            "Miami, USA", ["English", "Spanish"], ["instagram"],
            12_000, 0.058, 28_000, "18-24", {"female": 0.65, "male": 0.35},
            ["US"], ["fitness", "lifestyle"],
            "friendly and encouraging", "₹2,000–₹5,000",
            ["fitness apps"],
            ["fitness", "wellness"], "daily posts"
        ),
        # ---- MORE DIVERSE CREATORS ----
        make_creator(
            "c26", "Isabella Rossi", "beauty", ["fitness", "wellness"],
            "Rome-based creator combining beauty and fitness. I create content "
            "about skincare routines before and after workouts, healthy glow "
            "tips, and wellness habits. My audience is young women interested "
            "in holistic beauty and fitness.",
            "Rome, Italy", ["Italian", "English"], ["instagram", "youtube"],
            165_000, 0.043, 290_000, "20-30", {"female": 0.83, "male": 0.17},
            ["Italy", "Spain", "France"], ["beauty", "fitness", "wellness"],
            "glowing and aspirational", "₹10,000–₹30,000",
            ["beauty brands", "skincare", "sportswear"],
            ["beauty", "fitness"], "5 posts/week"
        ),
        make_creator(
            "c27", "Omar Hassan", "fitness", ["food", "nutrition"],
            "Dubai-based fitness and nutrition coach creating content in Arabic "
            "and English. I help men in the Middle East build healthy lifestyles "
            "through balanced diets and consistent training. Strong regional "
            "presence across the GCC.",
            "Dubai, UAE", ["Arabic", "English"], ["instagram", "youtube"],
            240_000, 0.049, 420_000, "22-35", {"male": 0.72, "female": 0.28},
            ["UAE", "Saudi Arabia", "Qatar"], ["fitness", "nutrition", "health"],
            "motivational and disciplined", "₹15,000–₹40,000",
            ["fitness brands", "health supplements", "sports drinks"],
            ["fitness", "nutrition"], "5 posts/week"
        ),
        make_creator(
            "c28", "Chloe Martin", "travel", ["lifestyle", "photography"],
            "Amsterdam-based travel and lifestyle creator. I create stunning "
            "photography content and share travel guides for solo female travelers. "
            "My audience is primarily millennial women who love adventure "
            "and cultural experiences.",
            "Amsterdam, Netherlands", ["Dutch", "English"], ["instagram", "youtube"],
            185_000, 0.047, 330_000, "22-32", {"female": 0.75, "male": 0.25},
            ["Netherlands", "Germany", "France"], ["travel", "photography", "lifestyle"],
            "wanderlust and aesthetic", "₹12,000–₹35,000",
            ["travel brands", "camera equipment", "lifestyle"],
            ["travel", "photography"], "4 posts/week"
        ),
        make_creator(
            "c29", "Leo Zhang", "tech", ["gaming", "finance"],
            "Singapore-based tech and finance creator. I cover personal finance "
            "apps, crypto, investing, and tech gadgets for young professionals. "
            "My content is data-driven and practical, appealing to the "
            "financially conscious Gen Z and millennial crowd.",
            "Singapore", ["English", "Mandarin"], ["youtube", "tiktok"],
            380_000, 0.037, 620_000, "22-34", {"male": 0.62, "female": 0.38},
            ["Singapore", "Malaysia", "Hong Kong"], ["tech", "finance", "investing"],
            "smart and analytical", "₹15,000–₹40,000",
            ["fintech", "tech brands", "investing apps"],
            ["tech", "finance"], "4 posts/week"
        ),
        make_creator(
            "c30", "Nora Johansson", "parenting", ["lifestyle", "wellness"],
            "Stockholm-based parent and wellness creator. I share gentle parenting "
            "tips, family wellness routines, and mindful living content. "
            "My audience is primarily parents aged 25-40 seeking balanced "
            "approaches to family life.",
            "Stockholm, Sweden", ["Swedish", "English"], ["instagram", "youtube"],
            130_000, 0.052, 220_000, "25-40", {"female": 0.88, "male": 0.12},
            ["Sweden", "Finland", "Norway"], ["parenting", "wellness", "lifestyle"],
            "warm and gentle", "₹10,000–₹25,000",
            ["family brands", "wellness products", "baby care"],
            ["parenting", "wellness"], "4 posts/week"
        ),
        make_creator(
            "c31", "Aarav Mehta", "fitness", ["tech", "gaming"],
            "Bangalore-based tech fitness creator blending gaming culture with "
            "fitness. I create esports fitness tips, gaming chair reviews, and "
            "content for gamers who want to stay healthy. A unique niche at "
            "the intersection of gaming and physical wellness.",
            "Bangalore, India", ["Hindi", "English"], ["youtube", "tiktok"],
            155_000, 0.046, 260_000, "18-26", {"male": 0.78, "female": 0.22},
            ["India", "Singapore"], ["fitness", "gaming", "tech"],
            "energetic and nerdy", "₹10,000–₹25,000",
            ["gaming brands", "fitness apps", "ergonomic gear"],
            ["fitness", "gaming"], "5 posts/week"
        ),
        make_creator(
            "c32", "Sofia Reyes", "beauty", ["fashion", "lifestyle"],
            "Mexico City-based beauty and fashion creator creating content in "
            "Spanish and English. I cover makeup tutorials, skincare routines, "
            "and Latin fashion. My audience is primarily Latin American women "
            "interested in beauty and self-expression.",
            "Mexico City, Mexico", ["Spanish", "English"], ["instagram", "youtube"],
            210_000, 0.050, 380_000, "18-30", {"female": 0.86, "male": 0.14},
            ["Mexico", "Colombia", "Argentina"], ["beauty", "fashion", "lifestyle"],
            "colorful and expressive", "₹12,000–₹30,000",
            ["beauty brands", "fashion", "cosmetics"],
            ["beauty", "fashion"], "5 posts/week"
        ),
        make_creator(
            "c33", "Kai Nakamura", "gaming", ["tech"],
            "Osaka-based gaming and tech content creator with a strong esports "
            "following. I cover competitive gaming, hardware reviews, and "
            "streaming setups. My audience is primarily young male gamers "
            "interested in the latest tech and gaming trends.",
            "Osaka, Japan", ["Japanese", "English"], ["youtube", "tiktok"],
            540_000, 0.058, 980_000, "18-24", {"male": 0.78, "female": 0.22},
            ["Japan", "South Korea", "Taiwan"], ["gaming", "tech", "esports"],
            "intense and entertaining", "₹20,000–₹50,000",
            ["gaming brands", "tech gadgets", "energy drinks"],
            ["gaming", "tech"], "daily streams"
        ),
        make_creator(
            "c34", "Lena Weber", "fitness", ["wellness", "yoga"],
            "Munich-based yoga and wellness instructor. I create gentle yoga "
            "flows, meditation guides, and holistic wellness content. "
            "My audience is primarily women aged 25-45 seeking mindfulness "
            "and work-life balance.",
            "Munich, Germany", ["German", "English"], ["youtube", "instagram"],
            140_000, 0.053, 240_000, "25-45", {"female": 0.87, "male": 0.13},
            ["Germany", "Austria", "Switzerland"], ["yoga", "wellness", "meditation"],
            "serene and mindful", "₹10,000–₹25,000",
            ["wellness brands", "yoga gear", "meditation apps"],
            ["yoga", "wellness"], "4 posts/week"
        ),
        make_creator(
            "c35", "Priya Nair", "fitness", ["nutrition", "food"],
            "Chennai-based fitness and nutrition creator creating authentic "
            "South Indian healthy recipes and workout routines. I help "
            "my audience combine traditional food wisdom with modern fitness "
            "principles. Strong regional connection with Tamil Nadu audience.",
            "Chennai, India", ["Tamil", "English"], ["youtube", "instagram"],
            135_000, 0.048, 230_000, "22-35", {"female": 0.74, "male": 0.26},
            ["India", "Sri Lanka", "Singapore"], ["fitness", "nutrition", "food"],
            "traditional and practical", "₹8,000–₹20,000",
            ["health food", "nutrition brands", "fitness equipment"],
            ["cooking", "fitness", "nutrition"], "5 posts/week"
        ),
        make_creator(
            "c36", "Luca Bianchi", "fashion", ["travel", "photography"],
            "Milan-based fashion and travel photographer. I create content "
            "combining Italian fashion with global travel destinations. "
            "My aesthetic is editorial and refined, appealing to the luxury "
            "fashion and travel market.",
            "Milan, Italy", ["Italian", "English"], ["instagram", "youtube"],
            290_000, 0.036, 510_000, "25-35", {"male": 0.48, "female": 0.52},
            ["Italy", "France", "US"], ["fashion", "travel", "photography"],
            "editorial and sophisticated", "₹15,000–₹45,000",
            ["fashion brands", "travel companies", "camera brands"],
            ["fashion", "travel"], "4 posts/week"
        ),
        make_creator(
            "c37", "Amira Okafor", "fitness", ["lifestyle", "beauty"],
            "Lagos-based fitness and lifestyle creator representing African "
            "fitness culture. I create workout routines, healthy hair care "
            "for active women, and body positivity content. My audience is "
            "primarily African women aged 18-30 interested in fitness and "
            "self-care.",
            "Lagos, Nigeria", ["English", "Yoruba"], ["instagram", "youtube"],
            170_000, 0.055, 310_000, "18-30", {"female": 0.88, "male": 0.12},
            ["Nigeria", "Ghana", "South Africa"], ["fitness", "beauty", "lifestyle"],
            "bold and body-positive", "₹8,000–₹20,000",
            ["fitness brands", "beauty products", "athleisure"],
            ["fitness", "beauty"], "5 posts/week"
        ),
        make_creator(
            "c38", "Tom Wilson", "tech", ["fitness", "gaming"],
            "Sydney-based tech creator focusing on fitness wearables and "
            "gaming peripherals. I review smartwatches, fitness trackers, "
            "and gaming mice. My audience is tech-savvy men aged 20-35 who "
            "love gadgets and fitness tech.",
            "Sydney, Australia", ["English"], ["youtube", "tiktok"],
            215_000, 0.042, 370_000, "22-35", {"male": 0.72, "female": 0.28},
            ["Australia", "New Zealand", "Singapore"], ["tech", "fitness", "gaming"],
            "geeky and practical", "₹15,000–₹35,000",
            ["tech brands", "wearables", "gaming peripherals"],
            ["tech", "fitness"], "4 posts/week"
        ),
        make_creator(
            "c39", "Zara Khan", "beauty", ["skincare", "lifestyle"],
            "Dubai-based beauty and skincare creator covering Middle Eastern "
            "beauty trends and halal cosmetics. I create skincare routines, "
            "makeup tutorials, and product reviews for women across the MENA "
            "region. Strong presence in the Gulf beauty community.",
            "Dubai, UAE", ["English", "Arabic"], ["instagram", "youtube"],
            265_000, 0.047, 470_000, "20-30", {"female": 0.84, "male": 0.16},
            ["UAE", "Saudi Arabia", "Egypt"], ["beauty", "skincare", "halal cosmetics"],
            "luxury and accessible", "₹15,000–₹40,000",
            ["beauty brands", "skincare", "cosmetics"],
            ["beauty", "skincare"], "5 posts/week"
        ),
        make_creator(
            "c40", "Ravi Patel", "food", ["fitness", "nutrition"],
            "Ahmedabad-based food and fitness creator creating healthy Indian "
            "recipes and protein-rich meal plans. I make nutrition fun and "
            "accessible through traditional Gujarati dishes modified for "
            "modern fitness goals. Strong regional Indian following.",
            "Ahmedabad, India", ["Gujarati", "English"], ["youtube", "instagram"],
            98_000, 0.049, 175_000, "22-35", {"male": 0.55, "female": 0.45},
            ["India"], ["healthy food", "nutrition", "fitness"],
            "traditional and health-conscious", "₹6,000–₹15,000",
            ["health food brands", "nutrition supplements", "cooking appliances"],
            ["cooking", "fitness"], "5 posts/week"
        ),
    ]


def make_creator(
    creator_id: str,
    name: str,
    primary_niche: str,
    secondary_niches: list[str],
    bio: str,
    location: str,
    languages: list[str],
    platforms: list[str],
    followers: int,
    engagement_rate: float,
    average_views: int,
    audience_age_range: str,
    audience_gender_distribution: dict[str, float],
    audience_locations: list[str],
    content_types: list[str],
    content_style: str,
    rate_card: str,
    past_brand_categories: list[str],
    interests: list[str],
    posting_frequency: str,
) -> dict:
    return {
        "creator_id": creator_id,
        "name": name,
        "primary_niche": primary_niche,
        "secondary_niches": secondary_niches,
        "bio": bio,
        "location": location,
        "languages": languages,
        "platforms": platforms,
        "followers": followers,
        "engagement_rate": engagement_rate,
        "average_views": average_views,
        "audience_age_range": audience_age_range,
        "audience_gender_distribution": audience_gender_distribution,
        "audience_locations": audience_locations,
        "content_types": content_types,
        "content_style": content_style,
        "rate_card": rate_card,
        "past_brand_categories": past_brand_categories,
        "interests": interests,
        "posting_frequency": posting_frequency,
    }


# ---------------------------------------------------------------------------
# BRAND DATA
# ---------------------------------------------------------------------------

def make_brands() -> list[dict]:
    return [
        # ---- BRAND 01: Fitness brand targeting young Indian women ----
        {
            "brand_id": "b01",
            "brand_name": "FitNova",
            "industry": "Fitness & Wellness",
            "product": "Home workout equipment and resistance bands",
            "campaign_title": "Move Anywhere Campaign",
            "campaign_goal": "Drive awareness and sales of affordable home fitness equipment among young Indian women",
            "campaign_description": "FitNova launches a new line of compact home workout equipment designed for small apartments. The campaign targets young Indian women who want to stay fit without going to the gym. Looking for creators who can demonstrate products in real home settings and inspire their audience to start their fitness journey.",
            "target_audience": "Young Indian women aged 18-30 interested in fitness and wellness",
            "target_age_range": "18-30",
            "target_gender": "female",
            "target_locations": ["India", "UAE", "Singapore"],
            "required_creator_niches": ["fitness"],
            "preferred_creator_niches": ["fitness", "nutrition", "wellness", "yoga"],
            "creator_size_preference": "mid-tier",
            "minimum_followers": 50_000,
            "maximum_followers": 500_000,
            "budget": 300_000,
            "currency": "INR",
            "content_types": ["workout", "nutrition", "healthy lifestyle"],
            "platforms": ["instagram", "youtube"],
            "tone": "energetic and motivational",
            "mandatory_requirements": ["must be based in India or South Asia", "must post in English or Hindi", "must have fitness content"],
            "preferred_traits": ["authentic", "motivational", "relatable", "female-led"],
            "excluded_traits": ["luxury-focused", "male-dominated audience", "non-English content"],
        },
        # ---- BRAND 02: Beauty/skincare brand targeting young Korean/Japanese women ----
        {
            "brand_id": "b02",
            "brand_name": "GlowEssence",
            "industry": "Beauty & Skincare",
            "product": "K-beauty skincare serum line",
            "campaign_title": "Glass Skin Challenge",
            "campaign_goal": "Generate user-generated content and drive trial of new K-beauty serum among young Asian women",
            "campaign_description": "GlowEssence is launching a K-beauty serum line and wants to create buzz through creator partnerships. The campaign focuses on the 'glass skin' trend popular among young Asian women. Creators should demonstrate the product in realistic routines and show genuine results over time.",
            "target_audience": "Young Asian women aged 18-24 interested in skincare and K-beauty",
            "target_age_range": "18-24",
            "target_gender": "female",
            "target_locations": ["South Korea", "Japan", "Singapore"],
            "required_creator_niches": ["beauty", "skincare"],
            "preferred_creator_niches": ["beauty", "skincare", "k-beauty", "lifestyle"],
            "creator_size_preference": "mid to macro",
            "minimum_followers": 100_000,
            "maximum_followers": 800_000,
            "budget": 600_000,
            "currency": "KRW",
            "content_types": ["skincare", "beauty", "makeup"],
            "platforms": ["instagram", "youtube", "tiktok"],
            "tone": "gorgeous and detail-oriented",
            "mandatory_requirements": ["must be based in East Asia", "must have skincare content", "must create video content"],
            "preferred_traits": ["detail-oriented", "authentic reviews", "skincare knowledgeable", "young female audience"],
            "excluded_traits": ["men's grooming focus", "luxury-only", "anti-aging focus"],
        },
        # ---- BRAND 03: Gaming brand targeting young male gamers ----
        {
            "brand_id": "b03",
            "brand_name": "GameVault",
            "industry": "Gaming & Tech",
            "product": "New gaming headset and peripherals",
            "campaign_title": "Level Up Audio",
            "campaign_goal": "Drive product awareness and pre-orders for new gaming headset among competitive gamers",
            "campaign_description": "GameVault is launching a new gaming headset designed for competitive esports players. The campaign targets young male gamers who prioritize audio quality and comfort during long gaming sessions. Creators should create gameplay content featuring the product authentically.",
            "target_audience": "Young male gamers aged 18-24 interested in esports and gaming hardware",
            "target_age_range": "18-24",
            "target_gender": "male",
            "target_locations": ["Japan", "US", "UK"],
            "required_creator_niches": ["gaming"],
            "preferred_creator_niches": ["gaming", "tech", "esports"],
            "creator_size_preference": "mid to macro",
            "minimum_followers": 150_000,
            "maximum_followers": 1_000_000,
            "budget": 800_000,
            "currency": "JPY",
            "content_types": ["gaming", "tech reviews", "esports"],
            "platforms": ["youtube", "tiktok"],
            "tone": "high-energy and funny",
            "mandatory_requirements": ["must have gaming content", "must be comfortable on camera", "must have male-skewed audience"],
            "preferred_traits": ["high-energy", "knowledgeable about hardware", "esports community presence", "entertaining"],
            "excluded_traits": ["family-friendly only", "female-skewed audience", "non-gaming content"],
        },
        # ---- BRAND 04: Fashion athleisure brand targeting young Indian women ----
        {
            "brand_id": "b04",
            "brand_name": "AthleVibe",
            "industry": "Fashion & Sportswear",
            "product": "Sustainable activewear line",
            "campaign_title": "Wear Your Values",
            "campaign_goal": "Promote sustainable activewear among young Indian women with a focus on ethical fashion",
            "campaign_description": "AthleVibe is launching a sustainable activewear line made from recycled materials. The campaign targets young Indian women who care about fashion and sustainability. Creators should showcase how the activewear fits into everyday life and workout routines.",
            "target_audience": "Young Indian women aged 18-28 interested in fashion, fitness, and sustainability",
            "target_age_range": "18-28",
            "target_gender": "female",
            "target_locations": ["India", "UAE", "Singapore"],
            "required_creator_niches": ["fashion", "fitness"],
            "preferred_creator_niches": ["fashion", "fitness", "sustainability", "athleisure"],
            "creator_size_preference": "mid-tier",
            "minimum_followers": 80_000,
            "maximum_followers": 400_000,
            "budget": 250_000,
            "currency": "INR",
            "content_types": ["fashion", "fitness", "lifestyle"],
            "platforms": ["instagram"],
            "tone": "bold and street-style",
            "mandatory_requirements": ["must have fashion AND fitness content", "must be based in India", "must create instagram content"],
            "preferred_traits": ["stylish", "active lifestyle", "sustainability conscious", "female audience"],
            "excluded_traits": ["luxury-focused", "only fitness content", "only fashion content"],
        },
        # ---- BRAND 05: Fintech brand targeting young professionals ----
        {
            "brand_id": "b05",
            "brand_name": "MoneyWise",
            "industry": "Fintech",
            "product": "Budgeting app for young professionals",
            "campaign_title": "Smart Money Moves",
            "campaign_goal": "Drive app downloads among young professionals who need help managing finances",
            "campaign_description": "MoneyWise is a new budgeting app designed for young professionals. The campaign targets tech-savvy 22-35 year olds who want to take control of their finances. Creators should create content showing real use cases of the app in everyday life.",
            "target_audience": "Young professionals aged 22-35 interested in fintech and personal finance",
            "target_age_range": "22-35",
            "target_gender": "all",
            "target_locations": ["US", "Singapore", "UK"],
            "required_creator_niches": ["tech", "finance"],
            "preferred_creator_niches": ["tech", "finance", "lifestyle", "productivity"],
            "creator_size_preference": "mid-tier",
            "minimum_followers": 100_000,
            "maximum_followers": 500_000,
            "budget": 400_000,
            "currency": "USD",
            "content_types": ["tech", "finance", "productivity"],
            "platforms": ["youtube", "tiktok"],
            "tone": "analytical and clear",
            "mandatory_requirements": ["must have tech or finance content", "must be English-speaking", "must cover apps/products"],
            "preferred_traits": ["analytical", "tech-savvy", "educational", "professional audience"],
            "excluded_traits": ["gaming only", "very young audience", "non-digital content"],
        },
        # ---- BRAND 06: Food/health brand targeting health-conscious Indians ----
        {
            "brand_id": "b06",
            "brand_name": "PurePlate",
            "industry": "Food & Health",
            "product": "Organic protein supplements",
            "campaign_title": "Fuel Your Body",
            "campaign_goal": "Drive trial of organic protein supplements among health-conscious Indians",
            "campaign_description": "PurePlate launches organic protein supplements made from traditional Indian ingredients. The campaign targets health-conscious Indians who want clean nutrition. Creators should demonstrate recipes and protein-packed meals using the product.",
            "target_audience": "Health-conscious Indians aged 22-35 interested in nutrition and fitness",
            "target_age_range": "22-35",
            "target_gender": "all",
            "target_locations": ["India", "Singapore", "UAE"],
            "required_creator_niches": ["fitness", "food", "nutrition"],
            "preferred_creator_niches": ["fitness", "food", "nutrition", "cooking"],
            "creator_size_preference": "mid-tier",
            "minimum_followers": 80_000,
            "maximum_followers": 400_000,
            "budget": 200_000,
            "currency": "INR",
            "content_types": ["cooking", "nutrition", "fitness"],
            "platforms": ["youtube", "instagram"],
            "tone": "traditional and health-conscious",
            "mandatory_requirements": ["must create cooking or recipe content", "must be based in India", "must cover food and nutrition"],
            "preferred_traits": ["health-focused", "cooking skills", "authentic", "nutrition knowledgeable"],
            "excluded_traits": ["junk food focus", "non-food content", "non-Indian geography"],
        },
        # ---- BRAND 07: Luxury travel brand targeting high-income Europeans ----
        {
            "brand_id": "b07",
            "brand_name": "Elysian Travel",
            "industry": "Travel & Luxury",
            "product": "Luxury boutique hotel experiences in Europe",
            "campaign_title": "Hidden Europe",
            "campaign_goal": "Promote luxury boutique hotel experiences among high-income European travelers",
            "campaign_description": "Elysian Travel partners with boutique hotels across Europe for an exclusive campaign. The target audience is high-income travelers aged 30-50 who value unique, premium experiences. Creators should create visually stunning content showcasing the hotels and experiences.",
            "target_audience": "High-income European travelers aged 30-50 seeking luxury and unique experiences",
            "target_age_range": "30-50",
            "target_gender": "all",
            "target_locations": ["France", "Italy", "Switzerland", "Germany"],
            "required_creator_niches": ["travel", "luxury"],
            "preferred_creator_niches": ["travel", "luxury", "photography", "fashion"],
            "creator_size_preference": "macro",
            "minimum_followers": 300_000,
            "maximum_followers": 2_000_000,
            "budget": 1_000_000,
            "currency": "EUR",
            "content_types": ["travel", "luxury", "photography"],
            "platforms": ["instagram", "youtube"],
            "tone": "premium and sophisticated",
            "mandatory_requirements": ["must have travel content", "must be based in Europe", "must have luxury brand experience"],
            "preferred_traits": ["sophisticated", "high-quality visuals", "luxury positioning", "affluent audience"],
            "excluded_traits": ["budget travel", "young audience", "non-European geography"],
        },
        # ---- BRAND 08: Parenting brand targeting young parents ----
        {
            "brand_id": "b08",
            "brand_name": "TinyNest",
            "industry": "Parenting & Family",
            "product": "Eco-friendly baby products",
            "campaign_title": "Green Start",
            "campaign_goal": "Raise awareness for eco-friendly baby products among millennial parents",
            "campaign_description": "TinyNest launches a line of eco-friendly baby products including biodegradable diapers and organic baby clothes. The campaign targets millennial parents who are environmentally conscious and want safe products for their babies.",
            "target_audience": "Environmentally conscious millennial parents aged 25-40",
            "target_age_range": "25-40",
            "target_gender": "female",
            "target_locations": ["UK", "Sweden", "Norway", "Denmark"],
            "required_creator_niches": ["parenting", "lifestyle"],
            "preferred_creator_niches": ["parenting", "wellness", "lifestyle", "sustainability"],
            "creator_size_preference": "mid-tier",
            "minimum_followers": 60_000,
            "maximum_followers": 350_000,
            "budget": 250_000,
            "currency": "SEK",
            "content_types": ["parenting", "wellness", "lifestyle"],
            "platforms": ["instagram", "youtube"],
            "tone": "warm and gentle",
            "mandatory_requirements": ["must have parenting content", "must be based in Scandinavia or UK", "must be female"],
            "preferred_traits": ["warm", "authentic", "eco-conscious", "parenting community"],
            "excluded_traits": ["gaming content", "luxury focused", "male-only audience"],
        },
        # ---- BRAND 09: Tech brand targeting young professionals globally ----
        {
            "brand_id": "b09",
            "brand_name": "NovaTech",
            "industry": "Consumer Tech",
            "product": "Wireless noise-cancelling earbuds",
            "campaign_title": "Sound Freedom",
            "campaign_goal": "Drive pre-orders for new wireless earbuds among young tech professionals",
            "campaign_description": "NovaTech launches premium wireless earbuds with industry-leading noise cancellation. The campaign targets tech-savvy young professionals who need high-quality audio for work and entertainment. Creators should create unboxing and review content.",
            "target_audience": "Tech-savvy young professionals aged 22-35 interested in consumer electronics",
            "target_age_range": "22-35",
            "target_gender": "all",
            "target_locations": ["US", "Canada", "Australia", "UK"],
            "required_creator_niches": ["tech"],
            "preferred_creator_niches": ["tech", "gaming", "fitness"],
            "creator_size_preference": "mid to macro",
            "minimum_followers": 150_000,
            "maximum_followers": 1_000_000,
            "budget": 700_000,
            "currency": "USD",
            "content_types": ["tech", "product reviews", "unboxing"],
            "platforms": ["youtube", "tiktok"],
            "tone": "analytical and clear",
            "mandatory_requirements": ["must have tech review content", "must create video content", "must be English-speaking"],
            "preferred_traits": ["analytical", "product-focused", "tech-savvy audience", "professional"],
            "excluded_traits": ["beauty-only", "parenting focus", "non-English content"],
        },
        # ---- BRAND 10: Health brand targeting young women globally ----
        {
            "brand_id": "b10",
            "brand_name": "VitalityCo",
            "industry": "Health & Wellness",
            "product": "Vitamin gummies for young women",
            "campaign_title": "Glow from Within",
            "campaign_goal": "Drive brand awareness and sales of vitamin gummies among young women",
            "campaign_description": "VitalityCo launches delicious vitamin gummies formulated for young women's health needs. The campaign targets health-conscious women aged 18-30 who want a tasty way to stay healthy. Creators should create fun, engaging content showing the product in daily routines.",
            "target_audience": "Health-conscious women aged 18-30 interested in wellness and supplements",
            "target_age_range": "18-30",
            "target_gender": "female",
            "target_locations": ["US", "UK", "Australia", "Canada"],
            "required_creator_niches": ["fitness", "wellness", "beauty"],
            "preferred_creator_niches": ["fitness", "beauty", "wellness", "lifestyle"],
            "creator_size_preference": "mid-tier",
            "minimum_followers": 50_000,
            "maximum_followers": 500_000,
            "budget": 350_000,
            "currency": "USD",
            "content_types": ["wellness", "fitness", "beauty", "nutrition"],
            "platforms": ["instagram", "youtube"],
            "tone": "fun and energetic",
            "mandatory_requirements": ["must have wellness or fitness content", "must have female audience", "must create engaging video"],
            "preferred_traits": ["fun", "relatable", "health-focused", "young female audience"],
            "excluded_traits": ["luxury-focused", "male audience", "serious/medical tone"],
        },
    ]


if __name__ == "__main__":
    main()
