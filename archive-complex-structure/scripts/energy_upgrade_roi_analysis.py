import json
import numpy as np

# Energy class to kWh/sqm/year mapping
ENERGY_CLASS_CONSUMPTION = {
    'A': 40,
    'B': 90,
    'C': 140,
    'D': 175,
    'E': 225,
    'F': 275,
    'G': 400
}

# Energy upgrade costs
UPGRADE_COSTS = {
    'insulation': {'min': 50, 'max': 80, 'unit': 'sqm'},
    'windows': {'min': 300, 'max': 500, 'unit': 'sqm_window'},
    'heat_pump': {'min': 8000, 'max': 15000, 'fixed': True},
    'solar_panels': {'cost_per_kw': 1500, 'typical_size_range': (3, 5)}
}

# Energy price in Greece
ENERGY_PRICE = 0.25  # €/kWh
GOVERNMENT_SUBSIDY_MAX = 25000  # €

# Property value increase for A/B energy class
PROPERTY_VALUE_PREMIUM = 0.12  # 12-15%

# Load the JSON file
with open('/Users/chrism/ATHintel/realdata/athens_100_percent_authentic_20250806_160825.json', 'r') as f:
    data = json.load(f)

# Attempt to extract properties from various possible locations
properties = data.get('properties', [])

# Function to calculate energy upgrade ROI
def calculate_energy_upgrade_roi(property_details):
    try:
        # Attempt to handle different property key structures
        floor_area = (
            property_details.get('sqm') or  # Added this as priority
            property_details.get('floor_area') or 
            property_details.get('area') or 
            property_details.get('floorArea') or 
            0
        )
        current_price = (
            property_details.get('price') or 
            property_details.get('current_price') or 
            property_details.get('market_value') or 
            0
        )
        current_energy_class = (
            property_details.get('energy_class') or 
            property_details.get('energyClass') or 
            property_details.get('energy_rating') or 
            'G'  # Default to worst class if no data
        )
        
        # Skip properties with missing critical information
        if not floor_area or not current_price:
            return None
        
        # Normalize energy class to uppercase and ensure string
        current_energy_class = str(current_energy_class).upper() if current_energy_class else 'G'
        
        # Set default energy class to 'G' if no valid class found
        if current_energy_class not in ENERGY_CLASS_CONSUMPTION:
            current_energy_class = 'G'
        
        # Current energy consumption
        current_consumption = ENERGY_CLASS_CONSUMPTION.get(current_energy_class, 400)
        
        # Upgrade target (aim for A or B class)
        target_consumption = 40  # A class
        
        # Estimate energy savings
        annual_energy_savings = (current_consumption - target_consumption) * floor_area * ENERGY_PRICE
        
        # Estimate upgrade costs
        # Insulation (full coverage)
        insulation_cost = floor_area * np.random.uniform(UPGRADE_COSTS['insulation']['min'], UPGRADE_COSTS['insulation']['max'])
        
        # Windows (assume 20% of floor area is window area)
        window_area = floor_area * 0.2
        windows_cost = window_area * np.random.uniform(UPGRADE_COSTS['windows']['min'], UPGRADE_COSTS['windows']['max'])
        
        # Heat pump (fixed cost with some variation)
        heat_pump_cost = np.random.uniform(UPGRADE_COSTS['heat_pump']['min'], UPGRADE_COSTS['heat_pump']['max'])
        
        # Solar panels (typical 3-5kW for apartments)
        solar_panel_kw = np.random.uniform(UPGRADE_COSTS['solar_panels']['typical_size_range'][0], 
                                           UPGRADE_COSTS['solar_panels']['typical_size_range'][1])
        solar_panels_cost = solar_panel_kw * UPGRADE_COSTS['solar_panels']['cost_per_kw']
        
        # Total upgrade cost
        total_upgrade_cost = insulation_cost + windows_cost + heat_pump_cost + solar_panels_cost
        
        # Government subsidy (capped at €25,000)
        government_subsidy = min(total_upgrade_cost * 0.4, GOVERNMENT_SUBSIDY_MAX)
        
        # Net upgrade cost
        net_upgrade_cost = total_upgrade_cost - government_subsidy
        
        # Property value increase
        value_increase = current_price * PROPERTY_VALUE_PREMIUM
        
        # Calculate ROI
        annual_savings = annual_energy_savings
        payback_period = net_upgrade_cost / annual_savings if annual_savings > 0 else float('inf')
        roi_percentage = (value_increase - net_upgrade_cost) / net_upgrade_cost * 100 if net_upgrade_cost > 0 else 0
        
        return {
            'property_id': property_details.get('property_id', 'N/A'),
            'current_price': current_price,
            'floor_area': floor_area,
            'current_energy_class': current_energy_class,
            'total_upgrade_cost': total_upgrade_cost,
            'government_subsidy': government_subsidy,
            'net_upgrade_cost': net_upgrade_cost,
            'annual_energy_savings': annual_energy_savings,
            'property_value_increase': value_increase,
            'roi_percentage': roi_percentage,
            'payback_period': payback_period
        }
    except Exception as e:
        print(f"Error processing property: {e}")
        return None

# Add properties that should be considered based on missing or poor energy rating
poor_energy_class_keys = ['G', 'F', 'E', 'D', None]
poor_energy_class_properties = [
    p for p in properties 
    if (str(p.get('energy_class', '')).upper() in poor_energy_class_keys or 
        p.get('energy_class') is None)
]

print(f"\nProperties with poor or missing energy classes: {len(poor_energy_class_properties)}")

# Calculate ROI for filtered properties
roi_results = [calculate_energy_upgrade_roi(prop) for prop in poor_energy_class_properties]

# Remove None values and sort by ROI percentage
roi_results = [r for r in roi_results if r is not None]
top_roi_opportunities = sorted(roi_results, key=lambda x: x.get('roi_percentage', 0), reverse=True)[:10]

# Display results
print("\nTOP 10 ENERGY UPGRADE ROI OPPORTUNITIES:")
for i, prop in enumerate(top_roi_opportunities, 1):
    print(f"\n{i}. Property ID: {prop['property_id']}")
    print(f"   Current Price: €{prop['current_price']:,.2f}")
    print(f"   Floor Area: {prop['floor_area']} sqm")
    print(f"   Current Energy Class: {prop['current_energy_class']}")
    print(f"   Total Upgrade Cost: €{prop['total_upgrade_cost']:,.2f}")
    print(f"   Government Subsidy: €{prop['government_subsidy']:,.2f}")
    print(f"   Net Upgrade Cost: €{prop['net_upgrade_cost']:,.2f}")
    print(f"   Annual Energy Savings: €{prop['annual_energy_savings']:,.2f}")
    print(f"   Property Value Increase: €{prop['property_value_increase']:,.2f}")
    print(f"   ROI Percentage: {prop['roi_percentage']:.2f}%")
    print(f"   Payback Period: {prop['payback_period']:.2f} years")

# Additional insights
print("\nROI Opportunities Summary:")
avg_roi = np.mean([prop['roi_percentage'] for prop in top_roi_opportunities])
avg_payback = np.mean([prop['payback_period'] for prop in top_roi_opportunities if prop['payback_period'] != float('inf')])
print(f"Average ROI Percentage: {avg_roi:.2f}%")
print(f"Average Payback Period: {avg_payback:.2f} years")