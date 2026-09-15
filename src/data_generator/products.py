"""
Product catalog generation module for Aura Retail.
Produces dim_products with realistic categories, subcategories, cost prices,
and retail prices reflecting industry-standard gross margins.
"""

from typing import List, Dict, Tuple
import numpy as np
import pandas as pd
from src.data_generator.config import GeneratorConfig

# Catalog definitions: category -> (margin_range, subcategories_with_templates)
CATALOG_SPEC: Dict[str, Tuple[Tuple[float, float], Dict[str, List[str]]]] = {
    "Apparel": (
        (0.55, 0.68),
        {
            "Tees & Tops": [
                "Organic Cotton Crewneck", "Heavyweight Boxy Tee", "Merino Wool Henley",
                "Linen Blend Button-Down", "Ribbed Modal Tank", "Oversized Vintage Tee"
            ],
            "Outerwear": [
                "Technical Trench Coat", "Recycled Down Puffer", "Wool Overcoat",
                "Water-Resistant Bomber", "Fleece Zip Chore Jacket", "Packable Windbreaker"
            ],
            "Denim & Bottoms": [
                "Classic Selvedge Denim", "Relaxed Chino Trouser", "Wide-Leg Linen Pant",
                "Everyday Stretch Denim", "Tailored Pleated Trouser", "Corduroy Carpenter Pant"
            ],
            "Activewear": [
                "Seamless High-Rise Legging", "Performance Running Short", "Four-Way Stretch Hoodie",
                "Athletic Tech Jogger", "Moisture-Wicking Half-Zip", "Compressive Training Bra"
            ],
            "Loungewear": [
                "Cashmere Blend Sweatpant", "French Terry Crewneck", "Waffle Knit Robe",
                "Modal Sleep Pant", "Cozy Knit Cardigan", "Brushed Cotton Lounge Shorts"
            ]
        }
    ),
    "Home Goods": (
        (0.50, 0.65),
        {
            "Bedding": [
                "Washed Linen Duvet Cover", "Crisp Percale Sheet Set", "Mulberry Silk Pillowcase",
                "Bamboo Sateen Sheet Set", "All-Season Down Comforter", "Waffle Weave Blanket"
            ],
            "Kitchen & Dining": [
                "Handcrafted Stoneware Plate Set", "Cast Iron Dutch Oven", "Artisan Chef Knife",
                "Borosilicate Glass Carafe", "Acacia Wood Cutting Board", "Ceramic Pour-Over Dripper"
            ],
            "Home Decor": [
                "Minimalist Ceramic Vase", "Handwoven Wool Area Rug", "Brushed Brass Wall Sconce",
                "Fluted Marble Catchall", "Architectural Bookend Pair", "Sculptural Table Lamp"
            ],
            "Candles & Diffusers": [
                "Cedarwood & Amber Soy Candle", "Ultrasonic Stone Diffuser", "Santai Botanical Mist",
                "Smoked Hinoki Reed Diffuser", "Night Jasmine Wax Melt", "Eucalyptus Shower Bundle"
            ],
            "Storage": [
                "Stackable Linen Storage Box", "Canvas Laundry Hamper", "Modular Acrylic Organizer",
                "Rattan Basket with Lid", "Powder-Coated Steel Shelf", "Felt Storage Bin"
            ]
        }
    ),
    "Beauty & Wellness": (
        (0.65, 0.78),
        {
            "Skincare": [
                "Hydrating Hyaluronic Serum", "Vitamin C Radiance Oil", "Ceramide Barrier Cream",
                "Gentle Gel Cleanser", "Exfoliating BHA Toner", "Mineral Daily Sunscreen SPF 50"
            ],
            "Haircare": [
                "Bond-Repair Treatment Mask", "Volumizing Biotin Shampoo", "Nourishing Argan Conditioner",
                "Scalp Detox Clarifying Scrub", "Heat Protectant Priming Spray", "Silk Gloss Leave-In Milk"
            ],
            "Body & Bath": [
                "Exfoliating Sea Salt Body Polish", "Restorative Magnesium Bath Soak", "Rich Shea Souffle Cream",
                "Botanical Cleansing Body Wash", "Firming Caffeine Body Oil", "Hand Treatment Balm"
            ],
            "Supplements": [
                "Daily Liposomal Multivitamin", "Marine Collagen Peptides", "Organic Ashwagandha Complex",
                "Probiotic Gut Balance", "Deep Rest Sleep Melatonin", "Omega-3 Pure Wild Fish Oil"
            ],
            "Aromatherapy": [
                "Calming Lavender Pulse Oil", "Focus Peppermint Inhaler", "Grounding Frankincense Blend",
                "Pure French Lavender Essential Oil", "Uplifting Sweet Orange Essence", "Sleep Ritual Pillow Spray"
            ]
        }
    ),
    "Accessories": (
        (0.60, 0.75),
        {
            "Bags & Totes": [
                "Full-Grain Leather Tote", "Waterproof Commuter Backpack", "Minimalist Crossbody Bag",
                "Recycled Canvas Weekender", "Nylon Slouchy Sling Bag", "Compact Tech Pouch"
            ],
            "Jewelry": [
                "14k Gold Vermeil Herringbone Chain", "Solid Sterling Silver Band", "Freshwater Pearl Drop Earrings",
                "Chunky Huggie Hoop Set", "Engraved Signet Ring", "Layered Satellite Choker"
            ],
            "Watches & Straps": [
                "Minimalist Bauhaus Quartz Watch", "Italian Calfskin Watch Strap", "Stainless Steel Mesh Band",
                "Automatic Field Timepiece", "Silicone Sport Band", "Chronograph Pilot Watch"
            ],
            "Eyewear": [
                "Handcrafted Acetate Sunglasses", "Blue Light Blocking Glasses", "Polarized Titanium Aviator",
                "Tortoiseshell Round Frame", "Cat-Eye UV Protection Shades", "Ultra-Light Reading Glasses"
            ],
            "Hats & Scarves": [
                "100% Cashmere Ribbed Beanie", "Brushed Alpaca Wool Scarf", "Structured Wool Fedora",
                "Organic Cotton Baseball Cap", "Silk Twill Square Scarf", "Wide-Brim Sun Hat"
            ]
        }
    ),
    "Electronics & Audio": (
        (0.35, 0.52),
        {
            "Earbuds & Headphones": [
                "Active Noise-Cancelling Headphones", "True Wireless Studio Earbuds", "Bone Conduction Sport Headset",
                "Hi-Res Audiophile Monitor", "Retro On-Ear Bluetooth Headphone", "Waterproof Swimming Earbuds"
            ],
            "Wireless Chargers": [
                "3-in-1 MagSafe Charging Stand", "Weighted Aluminum Desk Pad", "Fast Dual Wireless Charging Mat",
                "Portable Magnetic Battery Pack", "Bedside Nightstand Dock", "Braided USB-C Cable Trio"
            ],
            "Smart Desk Accessories": [
                "Smart Temperature Control Mug", "Motorized Cable Management Tray", "Ergonomic Memory Foam Wrist Rest",
                "Precision Sensor Desk Mat", "Ambient Screenbar Light", "Aluminum Laptop Riser Stand"
            ],
            "Portable Speakers": [
                "Rugged Waterproof Bluetooth Speaker", "360-Degree Sound Dome", "Ultra-Slim Pocket Speaker",
                "Smart Home Multi-Room Hub", "Vintage Acoustic Wood Speaker", "Shower Suction Wireless Speaker"
            ]
        }
    )
}


def generate_products(config: GeneratorConfig) -> pd.DataFrame:
    """
    Generates deterministic dim_products catalog.
    
    Args:
        config: Generator configuration with seed and product target count.
        
    Returns:
        pd.DataFrame: Product catalog adhering to schema.
    """
    rng = np.random.default_rng(config.seed)
    n_products = config.n_products

    # Flatten all available items from catalog specs
    catalog_pool = []
    for cat, (margin_range, subcats) in CATALOG_SPEC.items():
        for subcat, items in subcats.items():
            for item in items:
                catalog_pool.append({
                    "category": cat,
                    "sub_category": subcat,
                    "base_name": item,
                    "margin_range": margin_range
                })

    # Sample catalog_pool deterministically to reach n_products
    if n_products <= len(catalog_pool):
        indices = rng.choice(len(catalog_pool), size=n_products, replace=False)
        selected_specs = [catalog_pool[i] for i in sorted(indices)]
    else:
        # If requested more than pool, sample with replacement and add variation descriptors
        indices = rng.choice(len(catalog_pool), size=n_products, replace=True)
        modifiers = ["Signature", "Edition II", "Classic", "Premium", "Essential", "Modern", "Studio"]
        selected_specs = []
        for i, idx in enumerate(indices):
            spec = catalog_pool[idx].copy()
            if i >= len(catalog_pool):
                spec["base_name"] = f"{rng.choice(modifiers)} {spec['base_name']}"
            selected_specs.append(spec)

    # Base price ranges by category (Retail in USD)
    category_price_ranges = {
        "Apparel": (28.0, 160.0),
        "Home Goods": (24.0, 220.0),
        "Beauty & Wellness": (18.0, 95.0),
        "Accessories": (22.0, 180.0),
        "Electronics & Audio": (35.0, 250.0)
    }

    products = []
    for i, spec in enumerate(selected_specs):
        prod_id = f"PROD_{i + 1:03d}"
        cat = spec["category"]
        subcat = spec["sub_category"]
        name = spec["base_name"]
        min_retail, max_retail = category_price_ranges[cat]
        
        # Retail price rounded to .00 or .50
        raw_retail = rng.uniform(min_retail, max_retail)
        retail_cents = rng.choice([0.00, 0.50, 0.99])
        retail_price = round(float(np.floor(raw_retail) + retail_cents), 2)
        
        # Margin determines cost price: margin = (retail - cost) / retail
        min_m, max_m = spec["margin_range"]
        margin = rng.uniform(min_m, max_m)
        cost_price = round(float(retail_price * (1.0 - margin)), 2)
        
        # Sanity constraint: cost_price < retail_price and cost_price >= 1.0
        if cost_price >= retail_price:
            cost_price = round(retail_price * 0.70, 2)
        if cost_price < 1.0:
            cost_price = 1.00

        products.append({
            "product_id": prod_id,
            "product_name": name,
            "category": cat,
            "sub_category": subcat,
            "cost_price": cost_price,
            "retail_price": retail_price
        })

    df = pd.DataFrame(products)
    return df
