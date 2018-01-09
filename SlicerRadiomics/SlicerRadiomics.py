import os
import vtk, qt, ctk, slicer, logging
from slicer.ScriptedLoadableModule import *
import SimpleITK as sitk
from radiomics import featureextractor, getFeatureClasses, setVerbosity
import sitkUtils
import traceback


#
# SlicerRadiomics
#

class SlicerRadiomics(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = 'Radiomics'
    self.parent.categories = ['Informatics']
    self.parent.dependencies = []
    self.parent.contributors = ["Andrey Fedorov (BWH), Nicole Aucoin (BWH), Jean-Christophe Fillion-Robin (Kitware), "
                                "Joost van Griethuysen (AVL-NKI), Hugo Aerts (DFCI)"]
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

    # Setup a logger for the extension log messages (child logger of pyradiomics)
    self.logger = logging.getLogger('radiomics.slicer')

    # Instantiate and connect widgets ...

    #
    # Volume and segmentation input
    #
    self._addInputVolumeSection()

    #
    # Extraction Customization Area
    #
    self._addCustomizationSection()

    #
    # Output section
    #
    self._addOutputSection()

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton('Apply')
    self.applyButton.toolTip = 'Run the algorithm.'
    self.applyButton.enabled = False
    self.layout.addWidget(self.applyButton)

    #
    # Connections
    #

    # Input Section
    self.inputVolumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSelect)
    self.inputMaskSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSelect)
    self.inputSegmentationSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSelect)

    # Customization Section
    self.manualCustomizationRadioButton.connect('toggled(bool)', self.onCustomizationTypeCheckedChanged)

    self.calculateAllFeaturesButton.connect('clicked(bool)', self.onCalculateAllFeaturesButton)
    self.calculateNoFeaturesButton.connect('clicked(bool)', self.onCalculateNoFeaturesButton)

    self.parameterFilePathLineEdit.connect('currentPathChanged(QString)', self.onSelect)

    # General Section
    self.applyButton.connect('clicked(bool)', self.onApplyButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def _addInputVolumeSection(self):
    inputVolumeCollapsibleButton = ctk.ctkCollapsibleButton()
    inputVolumeCollapsibleButton.text = 'Select Input Volume and Segmentation'
    self.layout.addWidget(inputVolumeCollapsibleButton)

    # Layout within the dummy collapsible button
    inputVolumeFormLayout = qt.QFormLayout(inputVolumeCollapsibleButton)

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
    inputVolumeFormLayout.addRow('Input Image Volume: ', self.inputVolumeSelector)

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
    self.inputMaskSelector.setMRMLScene(slicer.mrmlScene)
    self.inputMaskSelector.setToolTip('Pick the input mask for the feature calculation.')
    inputVolumeFormLayout.addRow('Input LabelMap: ', self.inputMaskSelector)

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
    self.inputSegmentationSelector.setMRMLScene(slicer.mrmlScene)
    self.inputSegmentationSelector.setToolTip('Pick the input segmentation for the feature calculation.')
    inputVolumeFormLayout.addRow('Input Segmentation: ', self.inputSegmentationSelector)

  def _addCustomizationSection(self):
    customizationCollapsibleButton = ctk.ctkCollapsibleButton()
    customizationCollapsibleButton.text = 'Extraction Customization'
    customizationCollapsibleButton.collapsed = True
    self.layout.addWidget(customizationCollapsibleButton)

    customizationFormLayout = qt.QFormLayout(customizationCollapsibleButton)

    #
    # Radiobuttons to select customization Type
    #

    self.manualCustomizationRadioButton = qt.QRadioButton()
    self.manualCustomizationRadioButton.text = 'Manual Customization'
    self.manualCustomizationRadioButton.checked = True
    customizationFormLayout.layout().addWidget(self.manualCustomizationRadioButton)

    self.parameterFileCustomizationRadioButton = qt.QRadioButton()
    self.parameterFileCustomizationRadioButton.text = 'Parameter File Customization'
    self.parameterFileCustomizationRadioButton.checked = False
    customizationFormLayout.layout().addWidget(self.parameterFileCustomizationRadioButton)

    #
    # Manual Customization
    #
    self.manualCustomizationGroupBox = qt.QGroupBox('Manual Customization')
    self.manualCustomizationGroupBox.visible = True
    # self.manualCustomizationGroupBox.checkable = True
    customizationFormLayout.addWidget(self.manualCustomizationGroupBox)

    manualCustomizationFormLayout = qt.QFormLayout(self.manualCustomizationGroupBox)

    # Feature Class section
    featureClassCollapsibleButton = ctk.ctkCollapsibleButton()
    featureClassCollapsibleButton.text = 'Feature Classes'
    featureClassCollapsibleButton.collapsed = False
    manualCustomizationFormLayout.addWidget(featureClassCollapsibleButton)

    featureClassLayout = qt.QFormLayout(featureClassCollapsibleButton)

    self.featuresLayout = qt.QHBoxLayout()
    featureClassLayout.addRow('Features:', self.featuresLayout)

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
    featureClassLayout.addRow('Toggle Features:', self.buttonsLayout)

    self.calculateAllFeaturesButton = qt.QPushButton('All Features')
    self.calculateAllFeaturesButton.toolTip = 'Calculate all feature classes.'
    self.calculateAllFeaturesButton.enabled = True
    self.buttonsLayout.addWidget(self.calculateAllFeaturesButton)
    self.calculateNoFeaturesButton = qt.QPushButton('No Features')
    self.calculateNoFeaturesButton.toolTip = 'Calculate no feature classes.'
    self.calculateNoFeaturesButton.enabled = True
    self.buttonsLayout.addWidget(self.calculateNoFeaturesButton)

    # Resampling and Filtering
    filteringCollapsibleButton = ctk.ctkCollapsibleButton()
    filteringCollapsibleButton.text = 'Resampling and Filtering'
    filteringCollapsibleButton.collapsed = False
    manualCustomizationFormLayout.addRow(filteringCollapsibleButton)
    # Layout within the dummy collapsible button
    filteringFormLayout = qt.QFormLayout(filteringCollapsibleButton)

    # Resampling
    self.resampledVoxelSize = qt.QLineEdit()
    self.resampledVoxelSize.toolTip = 'Three floating-point numbers separated by comma defining the resampled pixel ' \
                                      'size (mm).'
    filteringFormLayout.addRow('Resampled voxel size', self.resampledVoxelSize)

    # LoG kernel sizes. default to 5 (?)
    self.logKernelSizes = qt.QLineEdit()
    self.logKernelSizes.toolTip = 'Laplacian of Gaussian filter kernel sizes (mm), separated by comma. ' \
                                  'If empty, no LoG filtering will be applied.'
    filteringFormLayout.addRow('LoG kernel sizes', self.logKernelSizes)

    # Wavelet
    self.waveletCheckBox = qt.QCheckBox()
    self.waveletCheckBox.checked = 0
    self.waveletCheckBox.toolTip = 'If checked, PyRadiomics will calculate features on the image after applying ' \
                                   'wavelet transformation'
    filteringFormLayout.addRow('Wavelet-based features', self.waveletCheckBox)

    #
    # Feature calculation settings
    #
    settingsCollapsibleButton = ctk.ctkCollapsibleButton()
    settingsCollapsibleButton.text = 'Settings'
    settingsCollapsibleButton.collapsed = False
    manualCustomizationFormLayout.addWidget(settingsCollapsibleButton)

    # Layout within the dummy collapsible button
    settingsFormLayout = qt.QFormLayout(settingsCollapsibleButton)

    # bin width, defaults to 25
    self.binWidthSliderWidget = ctk.ctkSliderWidget()
    self.binWidthSliderWidget.singleStep = 1
    self.binWidthSliderWidget.decimals = 2
    self.binWidthSliderWidget.minimum = 0.01
    self.binWidthSliderWidget.maximum = 100
    self.binWidthSliderWidget.value = 25
    self.binWidthSliderWidget.toolTip = 'Set the bin width'
    settingsFormLayout.addRow('Bin Width', self.binWidthSliderWidget)

    # symmetricalGLCM flag, defaults to false
    self.symmetricalGLCMCheckBox = qt.QCheckBox()
    self.symmetricalGLCMCheckBox.checked = 1
    self.symmetricalGLCMCheckBox.toolTip = 'Use a symmetrical GLCM matrix'
    settingsFormLayout.addRow('Enforce Symmetrical GLCM', self.symmetricalGLCMCheckBox)

    #
    # Parameter File Customization
    #

    self.parameterCustomizationGroupBox = qt.QGroupBox('Parameter File Customization')
    self.parameterCustomizationGroupBox.visible = False
    # self.parameterCustomizationGroupBox.checkable = True
    customizationFormLayout.addWidget(self.parameterCustomizationGroupBox)

    parameterCustomizationFormLayout = qt.QFormLayout(self.parameterCustomizationGroupBox)

    # Pathe edit to select parameter file
    self.parameterFilePathLineEdit = ctk.ctkPathLineEdit(filters=ctk.ctkPathLineEdit.Files)
    parameterCustomizationFormLayout.addRow("Parameter File", self.parameterFilePathLineEdit)

  def _addOutputSection(self):
    outputCollapsibleButton = ctk.ctkCollapsibleButton()
    outputCollapsibleButton.text = 'Output'
    self.layout.addWidget(outputCollapsibleButton)

    outputFormLayout = qt.QFormLayout(outputCollapsibleButton)

    # verbose logging flag, defaults to false
    self.verboseCheckBox = qt.QCheckBox()
    self.verboseCheckBox.checked = 0
    self.verboseCheckBox.toolTip = 'If checked, PyRadiomics outputs log messages from level DEBUG and higher ' \
                                   '(instead of INFO and higher)'
    outputFormLayout.addRow('Verbose Output', self.verboseCheckBox)

    # Output Table
    self.outputTableSelector = slicer.qMRMLNodeComboBox()
    self.outputTableSelector.nodeTypes = ['vtkMRMLTableNode']
    self.outputTableSelector.addEnabled = True
    self.outputTableSelector.selectNodeUponCreation = True
    self.outputTableSelector.renameEnabled = True
    self.outputTableSelector.removeEnabled = True
    self.outputTableSelector.noneEnabled = False
    self.outputTableSelector.setMRMLScene(slicer.mrmlScene)
    self.outputTableSelector.toolTip = 'Select the table where features will be saved, resets feature values on ' \
                                       'each run.'
    outputFormLayout.addRow('Output table:', self.outputTableSelector)

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = (
                                self.inputVolumeSelector.currentNode()  # Input volume selected
                                and (self.inputMaskSelector.currentNode()  # Some form of segmentation selected
                                     or self.inputSegmentationSelector.currentNode())
                                and (self.manualCustomizationRadioButton.checked  # Customization defined
                                     or os.path.isfile(self.parameterFilePathLineEdit.currentPath))
                                )

  def onCustomizationTypeCheckedChanged(self):
    self.manualCustomizationGroupBox.visible = self.manualCustomizationRadioButton.checked
    self.parameterCustomizationGroupBox.visible = self.parameterFileCustomizationRadioButton.checked

    self.onSelect()  # Refresh state of the apply button

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
    if self.verboseCheckBox.checked:
      # Setup debug logging for the pyradiomics toolbox
      # PyRadiomics logs to stderr by default, which is picked up by slicer and added to the slicer log.
      setVerbosity(logging.DEBUG)
    else:
      setVerbosity(logging.WARNING)

    if not self.outputTableSelector.currentNode():
      tableNode = slicer.vtkMRMLTableNode()
      slicer.mrmlScene.AddNode(tableNode)
      self.outputTableSelector.setCurrentNode(tableNode)

    logic = SlicerRadiomicsLogic()

    # Lock GUI
    self.applyButton.text = 'Working...'
    self.applyButton.setEnabled(False)
    slicer.app.processEvents()

    imageNode = self.inputVolumeSelector.currentNode()
    labelNode = self.inputMaskSelector.currentNode()
    segmentationNode = self.inputSegmentationSelector.currentNode()

    if self.manualCustomizationRadioButton.checked:
      # Set up customization
      featureClasses = self.getCheckedFeatureClasses()
      settings = {}
      settings['binWidth'] = self.binWidthSliderWidget.value
      settings['symmetricalGLCM'] = self.symmetricalGLCMCheckBox.checked

      enabledImageTypes = {'Original': {}}

      logKernelSizesValue = self.logKernelSizes.text
      if logKernelSizesValue:
        try:
          enabledImageTypes['LoG'] = {'sigma': [float(i) for i in logKernelSizesValue.split(',')]}
        except:
          self.logger.error('Failed to parse LoG sigma value from string \"' + logKernelSizesValue + '\"')
          traceback.print_exc()
          return

      resampledVoxelSizeValue = self.resampledVoxelSize.text
      if resampledVoxelSizeValue:
        try:
          settings['resampledPixelSpacing'] = [float(i) for i in resampledVoxelSizeValue.split(',')]
        except:
          self.logger.error('Failed to parse resampled voxel spacing from string \"' + resampledVoxelSizeValue + '\"')
          settings['resampledPixelSpacing'] = None
          traceback.print_exc()
          return

      if self.waveletCheckBox.checked:
        enabledImageTypes['Wavelet'] = {}

      # Compute features
      try:
        featuresDict = logic.run(imageNode, labelNode, segmentationNode, featureClasses, settings, enabledImageTypes)
        logic.exportToTable(featuresDict, self.outputTableSelector.currentNode())
      except:
        self.logger.error("Feature calculation failed.")
        traceback.print_exc()

    else:
      # Compute Features
      try:
        parameterFile = self.parameterFilePathLineEdit.currentPath
        featuresDict = logic.runWithParameterFile(imageNode, labelNode, segmentationNode, parameterFile)
        logic.exportToTable(featuresDict, self.outputTableSelector.currentNode())
      except:
        self.logger.error("Feature calculation failed.")
        traceback.print_exc()

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
    ls.Execute(resampledLabelImage, resampledLabelImage)
    th = sitk.BinaryThresholdImageFilter()
    th.SetInsideValue(1)
    th.SetOutsideValue(0)

    for l in ls.GetLabels()[1:]:
      th.SetUpperThreshold(l)
      th.SetLowerThreshold(l)
      labelsDict[labelmapNode.GetName() + "_label_" + str(l)] = th.Execute(combinedLabelImage)

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
      labelsDict[segmentationNode.GetName() + "_segment_" + segment.GetName()] = labelmapImage

    displayNode = segmentLabelmapNode.GetDisplayNode()
    if displayNode:
      slicer.mrmlScene.RemoveNode(displayNode)
    slicer.mrmlScene.RemoveNode(segmentLabelmapNode)

    return labelsDict

  def calculateFeatures(self, imageNode, labelNode, segmentationNode, extractor):
    """
    Calculate the feature on the image node for each ROI contained in the labelNode and/or the segmentation node, using
    an instantiated RadiomicsFeatureExtractor (with customization already configured).
    """
    # Prepare the input volume
    self.logger.debug('Read the input image node')
    grayscaleImage = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(imageNode.GetName()))

    # Prepare the input label map
    self.logger.debug('Read and prepare the input ROI(s)')
    labelsDict = {}
    if labelNode:
      labelsDict = self.prepareLabelsFromLabelmap(labelNode, grayscaleImage, labelsDict)
    if segmentationNode:
      labelsDict = self.prepareLabelsFromSegmentation(segmentationNode, grayscaleImage, labelsDict)

    # Calculate the features
    featuresDict = {}
    for l in labelsDict.keys():
      self.logger.debug("Calculating features for " + l)
      try:
        self.logger.debug('Starting feature calculation')
        featuresDict[l] = extractor.execute(grayscaleImage, labelsDict[l])
        self.logger.debug('Features calculated')
      except:
        self.logger.error('calculateFeatures() failed')
        traceback.print_exc()

    return featuresDict

  def exportToTable(self, featuresDict, table):
    """
    Export features to table node
    """
    self.logger.debug('Exporting to table')
    tableWasModified = table.StartModify()
    table.RemoveAllColumns()

    # Define table columns
    for k in ['Label', 'Image type', 'Feature Class', 'Feature Name', 'Value']:
      col = table.AddColumn()
      col.SetName(k)
    # Fill columns
    for label, features in featuresDict.items():
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

  def run(self, imageNode, labelNode, segmentationNode, featureClasses, settings, enabledImageTypes):
    """
    Run the actual algorithm
    """
    self.logger.info('Feature extraction started')

    self.logger.debug('Instantiating the extractor')

    extractor = featureextractor.RadiomicsFeaturesExtractor(**settings)

    self.logger.debug('Setting the enabled feature classes')
    extractor.disableAllFeatures()
    for feature in featureClasses:
      extractor.enableFeatureClassByName(feature)

    self.logger.debug('Setting the enabled image types')
    extractor.disableAllImageTypes()
    for imageType in enabledImageTypes:
      extractor.enableImageTypeByName(imageType, customArgs=enabledImageTypes[imageType])

    return self.calculateFeatures(imageNode, labelNode, segmentationNode, extractor)

  def runWithParameterFile(self, imageNode, labelNode, segmentationNode, parameterFilePath):
    """
    Run the actual algorithm using the provided customization file and provided image and region of interest(s) (ROIs)

    :param imageNode: Slicer Volume node representing the image from which features should be extracted
    :param labelNode: Slicer Labelmap node containing the ROIs as integer encoded volume (voxel value indicates ROI id)
    :param segmentationNode: Slicer segmentation node containing the segments of the ROIs (will be converted to binary
    label maps)
    :param parameterFilePath: String file path pointing to the parameter file used to customize the extraction
    :return: Dictionary containing the extracted features for each ROI
    """
    self.logger.info('Feature extraction started')

    self.logger.debug('Instantiating the extractor')

    # Instantiate the extractor with the specified customization file. If this file is invalid in any way, this call
    # will raise an error.
    extractor = featureextractor.RadiomicsFeaturesExtractor(parameterFilePath)

    return self.calculateFeatures(imageNode, labelNode, segmentationNode, extractor)


# noinspection PyAttributeOutsideInit
class SlicerRadiomicsTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    self.logger = logging.getLogger('radiomics.slicer')

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
    # https://github.com/Radiomics/SlicerRadiomics/releases/download/TestData-v1.0.0/lung1_binary.seg.nrrd
    import urllib
    dataRelease = 'v1.0.0'
    dataURLPrefix = 'https://github.com/Radiomics/SlicerRadiomics/releases/download/TestData'
    dataItems = (('lung1_image.nrrd', slicer.util.loadVolume),
                 ('lung1_label.nrrd', slicer.util.loadLabelVolume),
                 ('lung1_binary.seg.nrrd', slicer.util.loadSegmentation),
                 ('lung1.seg_0.vtp', None),
                 ('lung1.seg_1.vtp', None),
                 ('lung1_surface.seg.vtm', slicer.util.loadSegmentation),
                 ('Params.yaml', None))

    for item, loader in dataItems:
      url = dataURLPrefix + '-' + dataRelease + '/' + item
      filePath = os.path.join(slicer.app.temporaryPath, item)
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        self.logger.info('Requesting download %s from %s...\n' % (item, url))
        self.assertTrue(urllib.urlretrieve(url, filePath), 'Failed to download from ' + url)
      if loader:
        self.logger.info('Loading %s from %s...' % (item, filePath))
        self.assertTrue(loader(filePath), 'Failed to load ' + item)

    self.delayDisplay(
      'Finished with download and loading %d volumes' % (slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLVolumeNode')))

    grayscaleNode = slicer.util.getNode(pattern='lung1_image')
    labelmapNode = slicer.util.getNode(pattern='lung1_label')
    binaryNode = slicer.util.getNode(pattern='lung1_binary')
    surfaceNode = slicer.util.getNode(pattern='lung1_surface')

    parameterFile = os.path.join(slicer.app.temporaryPath, 'Params.yaml')

    logic = SlicerRadiomicsLogic()
    self.assertIsNotNone(logic.hasImageData(grayscaleNode))
    self.assertIsNotNone(logic.hasImageData(labelmapNode))

    featureClasses = ['firstorder']
    settings = {}
    settings['binWidth'] = 25
    settings['symmetricalGLCM'] = False
    settings['label'] = 1

    enabledImageTypes = {"Original": {}}

    for segNode in [binaryNode, surfaceNode]:
      featuresDict = logic.run(grayscaleNode, labelmapNode, segNode, featureClasses, settings, enabledImageTypes)

      tableNode = slicer.vtkMRMLTableNode()
      tableNode.SetName('lung1_label and ' + segNode.GetName())
      slicer.mrmlScene.AddNode(tableNode)
      logic.exportToTable(featuresDict, tableNode)
      logic.showTable(tableNode)

    featuresDict = logic.runWithParameterFile(grayscaleNode, labelmapNode, binaryNode, parameterFile)

    tableNode = slicer.vtkMRMLTableNode()
    tableNode.SetName('lung1_label and ' + binaryNode.GetName() + ' customized with Params.yaml')
    slicer.mrmlScene.AddNode(tableNode)
    logic.exportToTable(featuresDict, tableNode)
    logic.showTable(tableNode)

    self.delayDisplay('Test passed!')
