import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
import radiomics
from radiomics import featureextractor, getFeatureClasses


#
# SlicerRadiomics
#

class SlicerRadiomics(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = 'SlicerRadiomics'
    self.parent.categories = ['Informatics']
    self.parent.dependencies = []
    self.parent.contributors = ['Nicole Aucion (BWH)']
    self.parent.helpText = """
    This is a scripted loadable module bundled in the SlicerRadomics extension.
    It gives access to the radiomics feature calculation classes.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Nicole Aucoin, BWH, and was  partially funded by  grant .
    """


#
# SlicerRadiomicsWidget
#

class SlicerRadiomicsWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = 'Parameters'
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
    self.inputVolumeSelector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.inputVolumeSelector.selectNodeUponCreation = True
    self.inputVolumeSelector.addEnabled = False
    self.inputVolumeSelector.removeEnabled = False
    self.inputVolumeSelector.noneEnabled = False
    self.inputVolumeSelector.showHidden = False
    self.inputVolumeSelector.showChildNodeTypes = False
    self.inputVolumeSelector.setMRMLScene(slicer.mrmlScene)
    self.inputVolumeSelector.setToolTip('Pick the input image for the feature calculation.')
    parametersFormLayout.addRow('Input Image Volume: ', self.inputVolumeSelector)

    #
    # input mask volume selector
    #
    self.inputMaskSelector = slicer.qMRMLNodeComboBox()
    self.inputMaskSelector.nodeTypes = ['vtkMRMLLabelMapVolumeNode']
    self.inputMaskSelector.selectNodeUponCreation = True
    self.inputMaskSelector.addEnabled = False
    self.inputMaskSelector.removeEnabled = False
    self.inputMaskSelector.noneEnabled = False
    self.inputMaskSelector.showHidden = False
    self.inputMaskSelector.showChildNodeTypes = False
    self.inputMaskSelector.setMRMLScene(slicer.mrmlScene)
    self.inputMaskSelector.setToolTip('Pick the input mask for the feature calclation.')
    parametersFormLayout.addRow('Input Mask Volume: ', self.inputMaskSelector)

    #
    # Feature class selection
    #
    self.featuresLayout = qt.QHBoxLayout()
    parametersFormLayout.addRow('Features:', self.featuresLayout)

    self.featuresButtonGroup = qt.QButtonGroup(self.featuresLayout)
    self.featuresButtonGroup.exclusive = False

    # Get the feature classes dynamically
    self.features = getFeatureClasses().keys()
    # Create a checkbox for each feature
    featureButtons = {}
    for feature in self.features:
      featureButtons[feature] = qt.QCheckBox(feature)
      # TODO: decide which features to enable by default
      featureButtons[feature].checked = False
      if feature == 'firstorder':
        featureButtons[feature].checked = True
      self.featuresButtonGroup.addButton(featureButtons[feature])
      self.featuresLayout.layout().addWidget(featureButtons[feature])
      # set the ID to be the index of this feature in the list
      self.featuresButtonGroup.setId(featureButtons[feature], self.features.index(feature))

    # Add buttons to select all or none
    self.buttonsLayout = qt.QHBoxLayout()
    parametersFormLayout.addRow('Toggle Features:', self.buttonsLayout)

    self.calculateAllFeaturesButton = qt.QPushButton('All Features')
    self.calculateAllFeaturesButton.toolTip = 'Calcualte all feature classes.'
    self.calculateAllFeaturesButton.enabled = True
    self.buttonsLayout.addWidget(self.calculateAllFeaturesButton)
    self.calculateNoFeaturesButton = qt.QPushButton('No Features')
    self.calculateNoFeaturesButton.toolTip = 'Calculate no feature classes.'
    self.calculateNoFeaturesButton.enabled = True
    self.buttonsLayout.addWidget(self.calculateNoFeaturesButton)

    #
    # Feature calculation options
    #
    optionsCollapsibleButton = ctk.ctkCollapsibleButton()
    optionsCollapsibleButton.text = 'Options'
    optionsCollapsibleButton.collapsed = True
    self.layout.addWidget(optionsCollapsibleButton)

    # Layout within the dummy collapsible button
    optionsFormLayout = qt.QFormLayout(optionsCollapsibleButton)

    # bin width, defaults to 25
    self.binWidthSliderWidget = ctk.ctkSliderWidget()
    self.binWidthSliderWidget.singleStep = 1
    self.binWidthSliderWidget.decimals = 0
    self.binWidthSliderWidget.minimum = 1
    self.binWidthSliderWidget.maximum = 100
    self.binWidthSliderWidget.value = 25
    self.binWidthSliderWidget.toolTip = 'Set the bin width'
    optionsFormLayout.addRow('Bin Width', self.binWidthSliderWidget)

    # symmetricalGLCM flag, defaults to false
    self.symmetricalGLCMCheckBox = qt.QCheckBox()
    self.symmetricalGLCMCheckBox.checked = 0
    self.symmetricalGLCMCheckBox.toolTip = 'Use a symmetrical GLCM matrix'
    optionsFormLayout.addRow('Enforce Symmetrical GLCM', self.symmetricalGLCMCheckBox)

    # label for the mask, defaults to 1
    self.labelSliderWidget = ctk.ctkSliderWidget()
    self.labelSliderWidget.singleStep = 1
    self.labelSliderWidget.decimals = 0
    self.labelSliderWidget.minimum = 0
    self.labelSliderWidget.maximum = 255
    self.labelSliderWidget.value = 1
    self.labelSliderWidget.toolTip = 'Set the label to use for masking the image'
    optionsFormLayout.addRow('Label', self.labelSliderWidget)

    # verbose flag, defaults to false
    self.verboseCheckBox = qt.QCheckBox()
    self.verboseCheckBox.checked = 0
    optionsFormLayout.addRow('Verbose', self.verboseCheckBox)

    # debug logging flag, defaults to false
    self.debuggingCheckBox = qt.QCheckBox()
    self.debuggingCheckBox.checked = 0
    self.debuggingCheckBox.toolTip = \
      'If checked, PyRadiomics log messages from level DEBUG and higher will be added to the slicer log'
    optionsFormLayout.addRow('Store debug log', self.debuggingCheckBox)

    #
    # Output table
    #
    outputCollapsibleButton = ctk.ctkCollapsibleButton()
    outputCollapsibleButton.text = 'Output'
    self.layout.addWidget(outputCollapsibleButton)
    outputFormLayout = qt.QFormLayout(outputCollapsibleButton)

    self.outputTableSelector = slicer.qMRMLNodeComboBox()
    self.outputTableSelector.nodeTypes = ['vtkMRMLTableNode']
    self.outputTableSelector.addEnabled = True
    self.outputTableSelector.selectNodeUponCreation = True
    self.outputTableSelector.renameEnabled = True
    self.outputTableSelector.removeEnabled = True
    self.outputTableSelector.noneEnabled = False
    self.outputTableSelector.setMRMLScene(slicer.mrmlScene)
    self.outputTableSelector.toolTip = \
      'Select the table where features will be saved, resets feature values on each run.'
    outputFormLayout.addRow('Output table:', self.outputTableSelector)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton('Apply')
    self.applyButton.toolTip = 'Run the algorithm.'
    self.applyButton.enabled = False
    self.layout.addWidget(self.applyButton)

    # connections
    self.calculateAllFeaturesButton.connect('clicked(bool)', self.onCalculateAllFeaturesButton)
    self.calculateNoFeaturesButton.connect('clicked(bool)', self.onCalculateNoFeaturesButton)
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSelect)
    self.inputMaskSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSelect)
    self.outputTableSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputVolumeSelector.currentNode() and self.inputMaskSelector.currentNode() and (
      self.outputTableSelector.currentNode() is not None)
    if self.outputTableSelector.currentNode():
      self.outputTableSelector.baseName = self.inputMaskSelector.currentNode().GetName() + ' features'

  def getCheckedFeatureClasses(self):
    checkedFeatures = []
    featureButtons = self.featuresButtonGroup.buttons()
    for featureButton in featureButtons:
      if featureButton.checked:
        featureIndex = self.featuresButtonGroup.id(featureButton)
        feature = self.features[featureIndex]
        checkedFeatures.append(feature)
    return checkedFeatures

  def onCalculateAllFeaturesButton(self):
    featureButtons = self.featuresButtonGroup.buttons()
    for featureButton in featureButtons:
      featureButton.checked = True

  def onCalculateNoFeaturesButton(self):
    featureButtons = self.featuresButtonGroup.buttons()
    for featureButton in featureButtons:
      featureButton.checked = False

  def onApplyButton(self):
    if self.debuggingCheckBox.checked:
      # Setup debug logging for the pyradiomics toolbox
      # PyRadiomics logs to stderr by default, which is picked up by slicer and added to the slicer log.
      rlogger = radiomics.logger
      rlogger.setLevel(logging.DEBUG)

      # Get child logger from pyradiomics logger for log messages of this extension
      logger = logging.getLogger(rlogger.name + '.slicer')
      logger.setLevel(logging.DEBUG)

      # Uncomment this section to restrict logging to stderr (level WARNING) and store a separate log (level DEBUG)

      # logfile = os.path.expanduser(r'~\PyRadiomicsLog.txt')  # store the log in user root
      # if len(rlogger.handlers) > 0:
      #  rlogger.handlers[0].setLevel(logging.WARNING)  # The default handler for radiomics logging prints to stderr
      # handler = logging.FileHandler(filename=logfile, mode='w')
      # handler.setLevel(logging.DEBUG)
      # rlogger.addHandler(handler)

    logic = SlicerRadiomicsLogic()
    featureClasses = self.getCheckedFeatureClasses()

    # Lock GUI
    self.applyButton.text = 'Working...'
    self.applyButton.setEnabled(False)
    slicer.app.processEvents()

    # Compute features
    kwargs = {}
    kwargs['binWidth'] = int(self.binWidthSliderWidget.value)
    kwargs['symmetricalGLCM'] = self.symmetricalGLCMCheckBox.checked
    kwargs['verbose'] = self.verboseCheckBox.checked
    kwargs['label'] = int(self.labelSliderWidget.value)

    logic.run(self.inputVolumeSelector.currentNode(), self.inputMaskSelector.currentNode(), featureClasses, **kwargs)
    logic.exportToTable(self.outputTableSelector.currentNode())

    # Unlock GUI
    self.applyButton.setEnabled(True)
    self.applyButton.text = 'Apply'

    # Show results
    logic.showTable(self.outputTableSelector.currentNode())


#
# SlicerRadiomicsLogic
#

class SlicerRadiomicsLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    self.featureValues = {}

    self.logger = logging.getLogger('radiomics.slicer')

    self.logger.debug('Slicer Radiomics logic initialized')

  def hasImageData(self, volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    self.logger.debug('Checking if volume has image data')

    if not volumeNode:
      self.logger.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      self.logger.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def calculateFeatures(self, inputVolume, inputMaskVolume, featureClasses, **kwargs):
    """
    Calculate a single feature on the input MRML volume nodes
    """
    self.logger.debug('Calculating features for %s', featureClasses)

    volumeName = inputVolume.GetName()
    maskName = inputMaskVolume.GetName()

    self.logger.debug('Instantiating the extractor')

    extractor = featureextractor.RadiomicsFeaturesExtractor(**kwargs)
    extractor.disableAllFeatures()
    for feature in featureClasses:
      extractor.enableFeatureClassByName(feature)

    self.logger.debug('Loading image and mask as SimpleITK objects')
    import sitkUtils
    testImage = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(volumeName))
    # TODO: debug why the maskName works in the test, but not from the GUI, it tries to read the table node
    testMask = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(inputMaskVolume.GetID()))

    self.delayDisplay(
      'Calculating %s for volume %s and mask %s' % (featureClasses, inputVolume.GetName(), inputMaskVolume.GetName()),
      200)

    # Calculate features
    self.logger.debug('Extracting features')
    self.featureValues = extractor.execute(testImage, testMask)
    self.logger.debug('Extraction finished')

  def exportToTable(self, table):
    """
    Export features to table node
    """
    self.logger.debug('Exporting to table')
    tableWasModified = table.StartModify()
    table.RemoveAllColumns()

    # Define table columns
    for k in ['Feature Class', 'Feature Name', 'Value']:
      col = table.AddColumn()
      col.SetName(k)
    # Fill columns
    for featureKey, featureValue in self.featureValues.items():
      inputImage, featureClass, featureName = str(featureKey).split("_", 3)
      rowIndex = table.AddEmptyRow()
      table.SetCellText(rowIndex, 0, featureClass)
      table.SetCellText(rowIndex, 1, featureName)
      table.SetCellText(rowIndex, 2, str(featureValue))

    table.Modified()
    table.EndModify(tableWasModified)

  def showTable(self, table):
    """
    Switch to a layout where tables are visible and show the selected one.
    """
    self.logger.debug('Showing table')
    currentLayout = slicer.app.layoutManager().layout
    layoutWithTable = slicer.modules.tables.logic().GetLayoutWithTable(currentLayout)
    slicer.app.layoutManager().setLayout(layoutWithTable)
    slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveTableID(table.GetID())
    slicer.app.applicationLogic().PropagateTableSelection()

  def run(self, inputVolume, inputMaskVolume, featureClasses, **kwargs):
    """
    Run the actual algorithm
    """

    self.logger.info('Processing started')

    self.calculateFeatures(inputVolume, inputMaskVolume, featureClasses, **kwargs)

    self.logger.info('Processing completed, feature values:')

    self.logger.info(self.featureValues)

    return True


class SlicerRadiomicsTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SlicerRadiomics1()

  def test_SlicerRadiomics1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay('Starting the test')
    #
    # first, get some data
    #
    import urllib
    downloads = (
      ('http://slicer.kitware.com/midas3/download/item/269197/lung1_image.nrrd', 'lung1_image.nrrd',
       slicer.util.loadVolume),
      ('http://slicer.kitware.com/midas3/download/item/269198/lung1_label.nrrd', 'lung1_label.nrrd',
       slicer.util.loadLabelVolume),
    )

    for url, name, loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay(
      'Finished with download and loading %d volumes' % (slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLVolumeNode')))

    volumeNode = slicer.util.getNode(pattern='lung1_image')
    maskNode = slicer.util.getNode(pattern='lung1_label')
    logic = SlicerRadiomicsLogic()
    self.assertIsNotNone(logic.hasImageData(volumeNode))
    self.assertIsNotNone(logic.hasImageData(maskNode))

    featureClasses = ['firstorder', 'shape']
    kwargs = {}
    kwargs['binWidth'] = 25
    kwargs['symmetricalGLCM'] = False
    kwargs['verbose'] = False
    kwargs['label'] = 1
    logic.calculateFeatures(volumeNode, maskNode, featureClasses, **kwargs)

    tableNode = slicer.vtkMRMLTableNode()
    tableNode.SetName(maskNode.GetName())
    slicer.mrmlScene.AddNode(tableNode)
    logic.exportToTable(tableNode)
    logic.showTable(tableNode)

    self.delayDisplay('Test passed!')
