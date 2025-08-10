import adsk.core
import adsk.fusion
import json
import csv
import os
from ..lib import fusion360utils as futil
from .. import config
from . import BinGeneratorCommand

app = adsk.core.Application.get()
ui = app.userInterface

class BatchProcessorExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        try:
            command = args.firingEvent.sender
            inputs = command.commandInputs
            
            # Get selected configuration file
            config_file = inputs.itemById('config_file').selectedItem.name
            size_group = inputs.itemById('size_group').value
            
            # Process batch configuration
            if config_file.endswith('.csv'):
                process_csv_batch(config_file, size_group)
            elif config_file.endswith('.json'):
                process_json_batch(config_file, size_group)
            else:
                process_text_batch(config_file, size_group)
                
        except Exception as e:
            ui.messageBox(f'Batch processing failed:\n{str(e)}')

def process_csv_batch(csv_file, size_group):
    """Process CSV configuration for batch bin generation"""
    
    csv_path = os.path.join(config.BATCH_CONFIG_PATH, csv_file)
    
    with open(csv_path, 'r') as file:
        reader = csv.DictReader(file)
        
        bins_generated = 0
        for row in reader:
            if int(row['Group']) == size_group or size_group == 0:  # 0 = all groups
                # Parse bin dimensions
                size_parts = row['BinSize'].split('x')
                width = int(size_parts[0]) // 10  # Convert to grid units
                length = int(size_parts[1]) // 10
                
                # Parse compartments
                comp_parts = row['Compartments'].split('x')
                comp_x = int(comp_parts[0])
                comp_y = int(comp_parts[1])
                
                # Parse features
                features = {}
                if 'magnet' in row['Features']:
                    features['magnet'] = True
                if 'scoop' in row['Features']:
                    features['scoop'] = True
                if 'label' in row['Features']:
                    features['label'] = True
                
                # Generate bins
                quantity = int(row['Quantity'])
                for i in range(quantity):
                    comp = BinGeneratorCommand.generate_bin(
                        width_units=width,
                        length_units=length,
                        height_units=2,  # Default height
                        compartments=(comp_x, comp_y),
                        features=features
                    )
                    
                    # Position bins in grid layout
                    position_bin_in_tray(comp, row['TrayPosition'], i)
                    bins_generated += 1
        
        ui.messageBox(f'Successfully generated {bins_generated} bins for Size Group {size_group}')

def process_text_batch(text_file, size_group):
    """Process your custom text format for batch generation"""
    
    text_path = os.path.join(config.BATCH_CONFIG_PATH, text_file)
    
    # Parse format: "10x20,8,Level4,Pos[0-160,90]"
    with open(text_path, 'r') as file:
        lines = file.readlines()
        
        current_group = None
        bins_generated = 0
        
        for line in lines:
            line = line.strip()
            
            # Check for group header
            if line.startswith('GROUP'):
                current_group = int(line.split('GROUP')[1].split('_')[0])
                continue
            
            # Skip if not target group
            if current_group != size_group and size_group != 0:
                continue
            
            # Parse bin configuration
            if ',' in line:
                parts = line.split(',')
                if len(parts) >= 4:
                    # Parse size
                    size = parts[0]
                    width, length = map(lambda x: int(x)//10, size.split('x'))
                    
                    # Parse quantity
                    quantity = int(parts[1])
                    
                    # Parse level (for Z positioning)
                    level = int(parts[2].replace('Level', ''))
                    
                    # Parse position
                    pos_str = parts[3]
                    
                    # Generate bins
                    for i in range(quantity):
                        comp = BinGeneratorCommand.generate_bin(
                            width_units=width,
                            length_units=length,
                            height_units=2,
                            compartments=(1, 1)
                        )
                        
                        # Calculate position
                        z_offset = level * 20  # 20mm per level
                        position_bin_with_offset(comp, pos_str, i, z_offset)
                        bins_generated += 1
        
        ui.messageBox(f'Generated {bins_generated} bins from text configuration')

def process_json_batch(json_file, size_group):
    """Process JSON configuration for batch bin generation"""
    json_path = os.path.join(config.BATCH_CONFIG_PATH, json_file)
    with open(json_path, 'r') as file:
        data = json.load(file)
    bins_generated = 0
    for item in data.get('bins', []):
        if int(item.get('Group', 0)) == size_group or size_group == 0:
            width = int(item['BinSize'].split('x')[0]) // 10
            length = int(item['BinSize'].split('x')[1]) // 10
            comp_x, comp_y = map(int, item.get('Compartments', '1x1').split('x'))
            features = item.get('Features', {})
            quantity = int(item.get('Quantity', 1))
            for i in range(quantity):
                comp = BinGeneratorCommand.generate_bin(
                    width_units=width,
                    length_units=length,
                    height_units=2,
                    compartments=(comp_x, comp_y),
                    features=features
                )
                position_bin_in_tray(comp, item.get('TrayPosition', '0:0'), i)
                bins_generated += 1
    ui.messageBox(f'Generated {bins_generated} bins from JSON configuration')

def position_bin_in_tray(component, position_string, index):
    """Position bin component in tray based on position string"""
    
    # Parse position string like "0:90" or "0:160:90"
    pos_parts = position_string.split(':')
    
    if len(pos_parts) >= 2:
        if len(pos_parts) == 2:
            x = float(pos_parts[0])
            y = float(pos_parts[1])
        else:
            # Range positioning
            x_start = float(pos_parts[0])
            x_end = float(pos_parts[1])
            y = float(pos_parts[2])
            x = x_start + (index * 20)  # 20mm spacing
        
        # Create transform
        transform = adsk.core.Matrix3D.create()
        transform.translation = adsk.core.Vector3D.create(x/10.0, y/10.0, 0)
        
        # Apply transform to component
        component.transform = transform

def position_bin_with_offset(component, position_string, index, z_offset):
    """Position bin with additional Z offset"""
    pos = position_string[position_string.find('[')+1:position_string.find(']')]
    coords = pos.split(',')
    x_part = coords[0]
    y = float(coords[1])
    if '-' in x_part:
        x_start, x_end = map(float, x_part.split('-'))
        x = x_start + (index * 20)
    else:
        x = float(x_part)
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(x/10.0, y/10.0, z_offset/10.0)
    component.transform = transform

CMD_NAME = 'Batch Bin Processor'
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_batchProcessor'
CMD_Description = 'Generate multiple bins from configuration files'

def start():
    """Create the batch processor command"""
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description
    )
    
    futil.add_handler(cmd_def.commandCreated, command_created_batch)
    
    workspace = ui.workspaces.itemById('FusionSolidEnvironment')
    panel = workspace.toolbarPanels.itemById('SolidCreatePanel')
    control = panel.controls.addCommand(cmd_def)

def stop():
    """Clean up the command"""
    workspace = ui.workspaces.itemById('FusionSolidEnvironment')
    panel = workspace.toolbarPanels.itemById('SolidCreatePanel')
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    
    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()

def command_created_batch(args: adsk.core.CommandCreatedEventArgs):
    """Set up the batch command dialog"""
    
    cmd = args.command
    onExecute = BatchProcessorExecuteHandler()
    cmd.execute.add(onExecute)
    
    inputs = cmd.commandInputs
    
    # Configuration file selector
    config_files = os.listdir(config.BATCH_CONFIG_PATH)
    fileDropdown = inputs.addDropDownCommandInput('config_file', 'Configuration File', 
                                                  adsk.core.DropDownStyles.TextListDropDownStyle)
    for file in config_files:
        if file.endswith(('.csv', '.json', '.txt')):
            fileDropdown.listItems.add(file, False)
    
    # Size group selector
    inputs.addIntegerSpinnerCommandInput('size_group', 'Size Group (0=All)', 0, 5, 1, 2)
