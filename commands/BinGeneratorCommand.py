import adsk.core
import adsk.fusion
import os
import traceback
from ..lib import fusion360utils as futil
from .. import config

app = adsk.core.Application.get()
ui = app.userInterface

# Get active grid configuration
grid_config = config.GRID_CONFIG[config.ACTIVE_GRID]

class BinGeneratorCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        try:
            command = args.firingEvent.sender
            inputs = command.commandInputs
            
            # Get input values
            bin_width = inputs.itemById('bin_width').value
            bin_length = inputs.itemById('bin_length').value
            bin_height = inputs.itemById('bin_height').value
            compartments_x = inputs.itemById('compartments_x').value
            compartments_y = inputs.itemById('compartments_y').value
            has_scoop = inputs.itemById('has_scoop').value
            has_label = inputs.itemById('has_label').value
            
            # Generate bin with 10mm grid
            generate_bin(
                width_units=bin_width,
                length_units=bin_length,
                height_units=bin_height,
                compartments=(compartments_x, compartments_y),
                features={'scoop': has_scoop, 'label': has_label}
            )
            
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def generate_bin(width_units, length_units, height_units, compartments=(1,1), features={}):
    """Generate a Gridfinity bin with 10mm grid units"""
    
    design = adsk.fusion.Design.cast(app.activeProduct)
    rootComp = design.rootComponent
    
    # Calculate actual dimensions based on grid
    base_unit = grid_config['base_unit']
    height_unit = grid_config['height_unit']
    wall_thickness = grid_config['wall_thickness']
    
    width = width_units * base_unit
    length = length_units * base_unit
    height = height_units * height_unit
    
    # Create new component for bin
    occ = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = f"Bin_{width_units}x{length_units}x{height_units}"
    
    # Create base sketch
    sketches = comp.sketches
    xyPlane = comp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    
    # Draw outer rectangle
    lines = sketch.sketchCurves.sketchLines
    rect = lines.addCenterRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(width/2, length/2, 0)
    )
    
    # Create base extrusion
    prof = sketch.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    extInput = extrudes.createInput(prof, adsk.core.FeatureOperations.NewBodyFeatureOperation)
    distance = adsk.core.ValueInput.createByReal(height)
    extInput.setDistanceExtent(False, distance)
    baseExtrude = extrudes.add(extInput)
    
    # Shell to create hollow bin
    shells = comp.features.shellFeatures
    shellInput = shells.createInput()
    shellInput.insideThickness = adsk.core.ValueInput.createByReal(wall_thickness/10.0)
    
    # Select top face for shell opening
    body = baseExtrude.bodies.item(0)
    topFace = None
    for face in body.faces:
        if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
            if face.boundingBox.maxPoint.z > height * 0.9:
                topFace = face
                break
    
    if topFace:
        shellInput.inputEntities.add(topFace)
        shells.add(shellInput)
    
    # Add compartment dividers if specified
    if compartments[0] > 1 or compartments[1] > 1:
        add_compartments(comp, width, length, height, compartments, wall_thickness)
    
    # Add features
    if features.get('scoop'):
        add_scoop_feature(comp, width, length, height)
    if features.get('label'):
        add_label_feature(comp, width, length, height)
    
    return comp

def add_compartments(comp, width, length, height, compartments, wall_thickness):
    """Add internal dividers for compartments"""
    sketches = comp.sketches
    xyPlane = comp.xYConstructionPlane
    
    # X-direction dividers
    if compartments[0] > 1:
        for i in range(1, compartments[0]):
            x_pos = -width/2 + (width/compartments[0]) * i
            sketch = sketches.add(xyPlane)
            lines = sketch.sketchCurves.sketchLines
            lines.addByTwoPoints(
                adsk.core.Point3D.create(x_pos - wall_thickness/2, -length/2, 0),
                adsk.core.Point3D.create(x_pos - wall_thickness/2, length/2, 0)
            )
            lines.addByTwoPoints(
                adsk.core.Point3D.create(x_pos + wall_thickness/2, -length/2, 0),
                adsk.core.Point3D.create(x_pos + wall_thickness/2, length/2, 0)
            )
            # Close the rectangle
            lines.addByTwoPoints(
                adsk.core.Point3D.create(x_pos - wall_thickness/2, -length/2, 0),
                adsk.core.Point3D.create(x_pos + wall_thickness/2, -length/2, 0)
            )
            lines.addByTwoPoints(
                adsk.core.Point3D.create(x_pos - wall_thickness/2, length/2, 0),
                adsk.core.Point3D.create(x_pos + wall_thickness/2, length/2, 0)
            )
            
            # Extrude divider
            prof = sketch.profiles.item(0)
            extrudes = comp.features.extrudeFeatures
            extInput = extrudes.createInput(prof, adsk.core.FeatureOperations.JoinFeatureOperation)
            distance = adsk.core.ValueInput.createByReal(height * 0.8)  # 80% height for dividers
            extInput.setDistanceExtent(False, distance)
            extrudes.add(extInput)
    
    # Y-direction dividers (similar logic)
    if compartments[1] > 1:
        for i in range(1, compartments[1]):
            y_pos = -length/2 + (length/compartments[1]) * i
            sketch = sketches.add(xyPlane)
            lines = sketch.sketchCurves.sketchLines
            # Create divider rectangle
            rect = lines.addCenterRectangle(
                adsk.core.Point3D.create(0, y_pos, 0),
                adsk.core.Point3D.create(width/2, y_pos + wall_thickness/2, 0)
            )
            
            # Extrude divider
            prof = sketch.profiles.item(0)
            extrudes = comp.features.extrudeFeatures
            extInput = extrudes.createInput(prof, adsk.core.FeatureOperations.JoinFeatureOperation)
            distance = adsk.core.ValueInput.createByReal(height * 0.8)
            extInput.setDistanceExtent(False, distance)
            extrudes.add(extInput)

def command_created(args: adsk.core.CommandCreatedEventArgs):
    """Set up the command dialog"""
    
    futil.log(f'{CMD_NAME}: Command created event')
    
    cmd = args.command
    cmd.isRepeatable = False
    onExecute = BinGeneratorCommandExecuteHandler()
    cmd.execute.add(onExecute)
    
    # Create command inputs
    inputs = cmd.commandInputs
    
    # Bin dimensions (in grid units)
    inputs.addIntegerSpinnerCommandInput('bin_width', 'Width (units)', 1, 20, 1, 4)
    inputs.addIntegerSpinnerCommandInput('bin_length', 'Length (units)', 1, 20, 1, 4)
    inputs.addIntegerSpinnerCommandInput('bin_height', 'Height (units)', 1, 10, 1, 3)
    
    # Compartments
    inputs.addIntegerSpinnerCommandInput('compartments_x', 'Compartments X', 1, 10, 1, 1)
    inputs.addIntegerSpinnerCommandInput('compartments_y', 'Compartments Y', 1, 10, 1, 1)
    
    # Features
    inputs.addBoolValueInput('has_scoop', 'Add Scoop', True, '', False)
    inputs.addBoolValueInput('has_label', 'Add Label Area', True, '', False)
    
    # Grid system selector
    gridSystemInput = inputs.addDropDownCommandInput('grid_system', 'Grid System', 
                                                     adsk.core.DropDownStyles.TextListDropDownStyle)
    gridSystemInput.listItems.add('10mm Micro Grid', config.ACTIVE_GRID == 'micro_10mm')
    gridSystemInput.listItems.add('42mm Standard Gridfinity', config.ACTIVE_GRID == 'standard')

CMD_NAME = 'Gridfinity Bin Generator'
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_binGenerator'
CMD_Description = 'Generate Gridfinity bins with 10mm or 42mm grid'
IS_PROMOTED = True
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
COMMAND_BESIDE_ID = ''
ICON_FOLDER = os.path.join(os.path.dirname(__file__), 'resources', '')

def start():
    """Create the command definition"""
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER
    )
    
    futil.add_handler(cmd_def.commandCreated, command_created)
    
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED

def stop():
    """Clean up the command"""
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    
    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()
