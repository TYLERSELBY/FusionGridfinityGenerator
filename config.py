# Application Global Variables with 10mm Grid Support
import os
import json

DEBUG = True
ADDIN_NAME = 'GridfinityGenerator'
COMPANY_NAME = 'LevMishin'

# Palettes
sample_palette_id = f'{COMPANY_NAME}_{ADDIN_NAME}_palette_id'

# GRID CONFIGURATION - Modified for 10mm system
GRID_CONFIG = {
    'standard': {
        'base_unit': 42.0,  # mm - Original Gridfinity
        'height_unit': 7.0,  # mm
        'xy_tolerance': 0.25,  # mm
        'wall_thickness': 1.6,  # mm
    },
    'micro_10mm': {
        'base_unit': 10.0,  # mm - Your custom grid
        'height_unit': 1.7,  # mm - Scaled proportionally
        'xy_tolerance': 0.1,  # mm - Tighter tolerance for smaller scale
        'wall_thickness': 0.5,  # mm - Thinner walls for small bins
        'minimum_feature': 0.4,  # mm - Minimum printable feature
    }
}

# Set active grid system
ACTIVE_GRID = 'micro_10mm'  # Change to 'standard' for original 42mm grid

# Batch processing configuration paths
BATCH_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'batch_configs')
if not os.path.exists(BATCH_CONFIG_PATH):
    os.makedirs(BATCH_CONFIG_PATH)
