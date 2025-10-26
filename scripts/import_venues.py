import os
import sys
import django
import pandas as pd
import uuid
import re

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venyuk.settings')
django.setup()

from venue.models import Venue

def parse_categories(excel_category):
    """
    Parse Excel category values and return list of valid categories
    """
    if not excel_category or pd.isna(excel_category):
        return ['futsal']  # Default category
    
    category_str = str(excel_category).strip()
    
    # Handle list-like categories (e.g., "[Padel, Tennis]", "[Badminton, Padel, Tennis]")
    if category_str.startswith('[') and category_str.endswith(']'):
        # Extract categories from the list
        categories_inside = category_str[1:-1]
        # Split by comma and clean
        raw_categories = [cat.strip().lower() for cat in categories_inside.split(',')]
    else:
        # Single category
        raw_categories = [category_str.lower()]
    
    # Mapping dictionary
    category_mapping = {
        'padel': 'padel',
        'tennis': 'tennis',
        'basketball': 'basketball',
        'badminton': 'badminton',
        'sepak bola': 'sepak bola',
        'mini soccer': 'mini soccer',
        'futsal': 'futsal',
        'pickleball': 'pickle ball',
        'pickle ball': 'pickle ball',
        'squash': 'squash',
        'billiard': 'biliard',
        'biliard': 'biliard',
        'golf': 'golf',
        'shooting': 'shooting',
        'tenis meja': 'tennis meja',
        'tennis meja': 'tennis meja',
        'volley': 'voli',
        'voli': 'voli'
    }
    
    # Map and filter valid categories
    valid_categories = []
    for raw_cat in raw_categories:
        mapped_cat = category_mapping.get(raw_cat)
        if mapped_cat and mapped_cat not in valid_categories:
            valid_categories.append(mapped_cat)
    
    # If no valid categories found, use default
    if not valid_categories:
        valid_categories = ['futsal']
    
    return valid_categories

def clean_price(price_value):
    """
    Clean and convert price to integer
    """
    if pd.isna(price_value):
        return 0
    
    try:
        # Handle float values
        if isinstance(price_value, float):
            return int(price_value)
        # Handle string values
        elif isinstance(price_value, str):
            # Remove any non-numeric characters except decimal point
            cleaned = ''.join(c for c in price_value if c.isdigit() or c == '.')
            if cleaned:
                return int(float(cleaned))
        return int(price_value)
    except (ValueError, TypeError):
        return 0

def clean_rating(rating_value):
    """
    Clean and convert rating to float
    """
    if pd.isna(rating_value):
        return 0.0
    
    try:
        return float(rating_value)
    except (ValueError, TypeError):
        return 0.0

def import_venues_from_excel(file_path):
    """
    Main function to import venues from Excel file with multiple categories
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        print(f"Loaded {len(df)} records from Excel file")
        
        venues_created = 0
        errors = []
        category_stats = {}
        
        for index, row in df.iterrows():
            try:
                # Skip rows with essential missing data
                if pd.isna(row['name']) or not str(row['name']).strip():
                    continue
                
                # Parse categories
                categories = parse_categories(row['category'])
                
                # Update category statistics
                for cat in categories:
                    category_stats[cat] = category_stats.get(cat, 0) + 1
                
                # Prepare data
                venue_data = {
                    'id': uuid.uuid4(),
                    'name': str(row['name']).strip(),
                    'category': ",".join(categories),  # Save as CSV string
                    'address': str(row['address']).strip() if not pd.isna(row['address']) else '',
                    'price': clean_price(row['price']),
                    'rating': clean_rating(row['rating']),
                    'is_available': True
                }
                
                # Create venue
                venue = Venue(**venue_data)
                venue.save()
                
                venues_created += 1
                categories_display = ", ".join(categories)
                print(f"Created: {venue.name} - Categories: [{categories_display}] - Rp {venue.price}")
                
            except Exception as e:
                error_msg = f"Error at row {index + 2}: {str(e)}"  # +2 karena header + 1-based index
                errors.append(error_msg)
                print(f"ERROR: {error_msg}")
                continue
        
        # Print summary
        print(f"\n=== IMPORT SUMMARY ===")
        print(f"Successfully created: {venues_created} venues")
        print(f"Errors: {len(errors)}")
        
        print(f"\n=== CATEGORY DISTRIBUTION ===")
        for category, count in sorted(category_stats.items()):
            print(f"  {category}: {count} venues")
        
        if errors:
            print(f"\n=== ERRORS ({len(errors)}) ===")
            for error in errors[:10]:  # Show first 10 errors only
                print(f"  {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
                
        return venues_created, errors
        
    except Exception as e:
        print(f"Fatal error reading Excel file: {str(e)}")
        return 0, [str(e)]

if __name__ == "__main__":
    # Path yang benar - file ada di folder yang sama dengan script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file_path = os.path.join(script_dir, "dataset.xlsx")
    
    print(f"Looking for Excel file at: {excel_file_path}")
    
    if not os.path.exists(excel_file_path):
        print(f"Error: Excel file not found at {excel_file_path}")
        print("Please ensure the file exists in the same directory as this script.")
    else:
        print("Starting venue import with multiple categories support...")
        import_venues_from_excel(excel_file_path)