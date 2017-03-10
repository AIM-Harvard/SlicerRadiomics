import os
import vtk, qt, ctk, slicer, logging
from slicer.ScriptedLoadableModule import *
import SimpleITK as sitk
import radiomics
from radiomics import featureextractor, getFeatureClasses
import sitkUtils


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
    self.parent.contributors = ['Nicole Aucoin (BWH), Andrey Fedorov (BWH)']
    self.parent.contributors = ["Nicole Aucoin (BWH), Joost van Griethuysen (AVL-NKI), Andrey Fedorov (BWH)"]
    self.parent.helpText = """
    This is a scripted loadable module bundled in the SlicerRadomics extension.
    It gives access to the radiomics feature calculation classes implemented in pyradiomics library.
    See more details at http://pyradiomics.readthedocs.io/.
    """
    self.parent.acknowledgementText = """
    This work was partially supported by NIH/NCI ITCR program grant U24 CA194354.
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
    self.inputMaskSelector.noneEnabled = True
    self.inputMaskSelector.showHidden = False
    self.inputMaskSelector.showChildNodeTypes = False
    self.inputMaskSelector.setMRMLScene( slicer.mrmlScene )
    self.inputMaskSelector.setToolTip( 'Pick the input mask for the feature calculation.')
    parametersFormLayout.addRow('Input LabelMap: ', self.inputMaskSelector)

    #
    # input segmentation selector
    #
    self.inputSegmentationSelector = slicer.qMRMLNodeComboBox()
    self.inputSegmentationSelector.nodeTypes = ['vtkMRMLSegmentationNode']
    self.inputSegmentationSelector.selectNodeUponCreation = True
    self.inputSegmentationSelector.addEnabled = False
    self.inputSegmentationSelector.removeEnabled = False
    self.inputSegmentationSelector.noneEnabled = True
    self.inputSegmentationSelector.showHidden = False
    self.inputSegmentationSelector.showChildNodeTypes = False
    self.inputSegmentationSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSegmentationSelector.setToolTip('Pick the input segmentation for the feature calculation.')
    parametersFormLayout.addRow('Input Segmentation: ', self.inputSegmentationSelector)

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
    self.calculateAllFeaturesButton.toolTip = 'Calculate all feature classes.'
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
    self.inputSegmentationSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputVolumeSelector.currentNode() and \
                               (self.inputMaskSelector.currentNode() or \
                                self.inputSegmentationSelector.currentNode())

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

    if not self.outputTableSelector.currentNode():
      tableNode = slicer.vtkMRMLTableNode()
      slicer.mrmlScene.AddNode(tableNode)
      self.outputTableSelector.setCurrentNode(tableNode)

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

    imageNode = self.inputVolumeSelector.currentNode()
    labelNode = self.inputMaskSelector.currentNode()
    segmentationNode = self.inputSegmentationSelector.currentNode()

    try:
      featuresDict = logic.run(imageNode, labelNode, segmentationNode, featureClasses, **kwargs)
      logic.exportToTable(featuresDict, self.outputTableSelector.currentNode())
    except:
      logging.error("Feature calculation failed.")

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

  def prepareLabelsFromLabelmap(self, labelmapNode, grayscaleImage, labelsDict):

    combinedLabelImage = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(labelmapNode.GetName()))
    resampledLabelImage = self.resampleITKLabel(combinedLabelImage, grayscaleImage)

    ls = sitk.LabelStatisticsImageFilter()
    ls.Execute(resampledLabelImage,resampledLabelImage)
    th = sitk.BinaryThresholdImageFilter()
    th.SetInsideValue(1)
    th.SetOutsideValue(0)

    for l in ls.GetLabels()[1:]:
      th.SetUpperThreshold(l)
      th.SetLowerThreshold(l)
      labelsDict[labelmapNode.GetName()+"_label_"+str(l)] = th.Execute(combinedLabelImage)

    return labelsDict

  def prepareLabelsFromSegmentation(self, segmentationNode, grayscaleImage, labelsDict):
    import vtkSegmentationCorePython as vtkSegmentationCore
    segLogic = slicer.modules.segmentations.logic()

    segmentation = segmentationNode.GetSegmentation()
    binaryRepresentationDef = vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName()
    if not segmentation.ContainsRepresentation(binaryRepresentationDef):
      segmentation.CreateRepresentation(binaryRepresentationDef)

    segmentLabelmapNode = slicer.vtkMRMLLabelMapVolumeNode()
    slicer.mrmlScene.AddNode(segmentLabelmapNode)

    for segmentID in range(segmentation.GetNumberOfSegments()):
      segment = segmentation.GetNthSegment(segmentID)
      segmentLabelmap = segment.GetRepresentation(
        vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationBinaryLabelmapRepresentationName())
      if not segLogic.CreateLabelmapVolumeFromOrientedImageData(segmentLabelmap, segmentLabelmapNode):
        self.logger.error("Failed to convert label map")
        return labelsDict
      labelmapImage = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(segmentLabelmapNode.GetName()))
      labelmapImage = self.resampleITKLabel(labelmapImage, grayscaleImage)
      labelsDict[segmentationNode.GetName()+"_segment_"+segment.GetName()] = labelmapImage

    displayNode = segmentLabelmapNode.GetDisplayNode()
    if displayNode:
      slicer.mrmlScene.RemoveNode(displayNode)
    slicer.mrmlScene.RemoveNode(segmentLabelmapNode)

    return labelsDict

  def calculateFeatures(self, grayscaleImage, labelImage, featureClasses, **kwargs):
    # type: (object, object, object, object) -> object
    """
    Calculate a single feature on the input MRML volume nodes
    """
    self.logger.debug('Calculating features for %s', featureClasses)

    self.logger.debug('Instantiating the extractor')

    extractor = featureextractor.RadiomicsFeaturesExtractor(**kwargs)

    extractor.disableAllFeatures()
    for feature in featureClasses:
      extractor.enableFeatureClassByName(feature)

    self.logger.debug('Starting feature calculation')

    featureValues = {}
    try:
      featureValues = extractor.execute(grayscaleImage, labelImage)
    except:
      self.logger.error('pyradiomics feature extractor failed')

    self.logger.debug('Features calculated')

    return featureValues

  def exportToTable(self, featuresDict, table):
    """
    Export features to table node
    """
    self.logger.debug('Exporting to table')
    tableWasModified = table.StartModify()
    table.RemoveAllColumns()

    # Define table columns
    for k in ['Label', 'Input image type', 'Feature Class', 'Feature Name', 'Value']:
      col = table.AddColumn()
      col.SetName(k)
    # Fill columns
    for label,features in featuresDict.items():
      for featureKey, featureValue in features.items():
        processingType, featureClass, featureName = str(featureKey).split("_", 3)
        rowIndex = table.AddEmptyRow()
        table.SetCellText(rowIndex, 0, label)
        table.SetCellText(rowIndex, 1, processingType)
        table.SetCellText(rowIndex, 2, featureClass)
        table.SetCellText(rowIndex, 3, featureName)
        table.SetCellText(rowIndex, 4, str(featureValue))

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

  def resampleITKLabel(self, image, reference):
    resampler = sitk.ResampleImageFilter()
    resampler.SetInterpolator(sitk.sitkNearestNeighbor)
    resampler.SetReferenceImage(reference)
    return resampler.Execute(image)

  def run(self, imageNode, labelNode, segmentationNode, featureClasses, **kwargs):
    """
    Run the actual algorithm
    """

    self.logger.info('Processing started')

    grayscaleImage = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(imageNode.GetName()))

    #sitkUtils.PushToSlicer(label, labelNode.GetName(), overwrite=True, compositeView=2)

    labelsDict = {}
    if labelNode:
      labelsDict = self.prepareLabelsFromLabelmap(labelNode, grayscaleImage, labelsDict)
    if segmentationNode:
      labelsDict = self.prepareLabelsFromSegmentation(segmentationNode, grayscaleImage, labelsDict)

    #self.featureValues = extractor.execute(grayscaleImage, labelImage, image, **kwargs)

    featuresDict = {}
    for l in labelsDict.keys():
      self.logger.debug("Calculating features for "+l)
      featuresDict[l] = self.calculateFeatures(grayscaleImage, labelsDict[l], featureClasses, **kwargs)

    return featuresDict

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
    #https://github.com/Radiomics/SlicerRadiomics/releases/download/TestData-v1.0.0/lung1_binary.seg.nrrd
    import urllib
    dataRelease = 'v1.0.0'
    dataURLPrefix = 'https://github.com/Radiomics/SlicerRadiomics/releases/download/TestData'
    dataItems = (('lung1_image.nrrd', slicer.util.loadVolume),
                 ('lung1_label.nrrd', slicer.util.loadLabelVolume),
                 ('lung1_binary.seg.nrrd', slicer.util.loadSegmentation),
                 ('lung1.seg_0.vtp', None),
                 ('lung1.seg_1.vtp', None),
                 ('lung1_surface.seg.vtm', slicer.util.loadSegmentation))

    for item, loader in dataItems:
      url = dataURLPrefix+'-'+dataRelease+'/'+item
      filePath = slicer.app.temporaryPath + '/' + item
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (item, url))
        self.assertTrue(urllib.urlretrieve(url, filePath),'Failed to download from '+url)
      if loader:
        logging.info('Loading %s from %s...' % (item,filePath))
        self.assertTrue(loader(filePath),'Failed to load '+item)

    self.delayDisplay(
      'Finished with download and loading %d volumes' % (slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLVolumeNode')))

    grayscaleNode = slicer.util.getNode(pattern='lung1_image')
    labelmapNode = slicer.util.getNode(pattern='lung1_label')
    binaryNode = slicer.util.getNode(pattern='lung1_binary')
    surfaceNode = slicer.util.getNode(pattern='lung1_surface')

    logic = SlicerRadiomicsLogic()
    self.assertIsNotNone(logic.hasImageData(grayscaleNode))
    self.assertIsNotNone(logic.hasImageData(labelmapNode))

    featureClasses = ['firstorder']
    kwargs = {}
    kwargs['binWidth'] = 25
    kwargs['symmetricalGLCM'] = False
    kwargs['verbose'] = False
    kwargs['label'] = 1

    for segNode in [binaryNode, surfaceNode]:

      featuresDict = logic.run(grayscaleNode, labelmapNode, segNode, featureClasses, **kwargs)

      tableNode = slicer.vtkMRMLTableNode()
      tableNode.SetName('lung1_label and '+segNode.GetName())
      slicer.mrmlScene.AddNode(tableNode)
      logic.exportToTable(featuresDict, tableNode)
      logic.showTable(tableNode)

    self.delayDisplay('Test passed!')
