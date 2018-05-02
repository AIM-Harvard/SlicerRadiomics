import csv
from itertools import chain
import json
import os
import vtk, qt, ctk, slicer, logging
import numpy
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

    # Path edit to select parameter file
    self.parameterFilePathLineEdit = ctk.ctkPathLineEdit()
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
        logic.runCLI(imageNode,
                     labelNode,
                     segmentationNode,
                     self.outputTableSelector.currentNode(),
                     featureClasses,
                     settings,
                     enabledImageTypes,
                     self.onFinished)
      except:
        self.logger.error("Feature calculation failed.")
        traceback.print_exc()

    else:
      # Compute Features
      try:
        parameterFile = self.parameterFilePathLineEdit.currentPath
        logic.runCLIWithParameterFile(imageNode,
                                      labelNode,
                                      segmentationNode,
                                      self.outputTableSelector.currentNode(),
                                      parameterFile,
                                      self.onFinished)
      except:
        self.logger.error("Feature calculation failed.")
        traceback.print_exc()

    logic.showTable(self.outputTableSelector.currentNode())

  def onFinished(self):
    # Column containing the applied settings usually has a very long value, causing the width of that column to be very large
    # Therefore, resize all columns that have size > 200
    lm = slicer.app.layoutManager()
    for i in range(lm.tableViewCount):
      tv_header = lm.tableWidget(i).tableView().horizontalHeader()  # .setSectionResizeMode(qt.QHeaderView.Interactive)
      for j in range(tv_header.count()):
        if tv_header.sectionSize(j) > 200:
          tv_header.resizeSection(j, 200)
    # Unlock GUI
    self.applyButton.setEnabled(True)
    self.applyButton.text = 'Apply'


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

    self.cliNode = None  # Reference to the CLI Node that executes the extraction
    self.outTable = None  # Output table which will hold calculated features

    # Variables to hold observers and status for asynchronous processing
    self._onStatusObserverTag = None
    self._cli_running = False

    # Variables to hold the input image/label nodes and the parameter file for customization
    self._labelGenerators = None
    self._parameterFile = None
    self._labelName = None
    self._cli_output = None  # Temporary table to hold the results of the CLI script

    # If manual customization is used, a temporary parameter file will be generated. However, this must also be deleted upon completion
    self._delete_parameterFile = False

    # Variable to hold the calculated feature names
    # This is set on the first time results are returned and used to fill the table for subsequent results
    self._featureNames = {}

    # If set, this function will be called upon completion of extraction
    # Once per call to runCLI or runCLIWithParameterFile
    self.callback = None

    # Set this to true to run synchronously (blocks UI thread until CLI is done)
    self.runSync = False

  # Label generators to generate single ROI labels from either labelmapNode or segmentationNode input
  def _getLabelGeneratorFromLabelMap(self, labelNode, imageNode):
    combinedLabelImage = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(labelNode.GetName()))
    combinedLabelArray = sitk.GetArrayFromImage(combinedLabelImage)
    labels = numpy.unique(combinedLabelArray)

    for l in labels:
      if l == 0:
        continue
      yield '%s_label_%d' % (labelNode.GetName(), l), labelNode, int(l), imageNode

  def _getLabelGeneratorFromSegmentationNode(self, segmentationNode, imageNode):
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
        continue
      if not segmentLabelmapNode:
        self.logger.warning('no node')
        continue
      yield '%s_segment_%s' % (segmentationNode.GetName(), segment.GetName()), segmentLabelmapNode, 1, imageNode

    displayNode = segmentLabelmapNode.GetDisplayNode()
    if displayNode:
      slicer.mrmlScene.RemoveNode(displayNode)
    slicer.mrmlScene.RemoveNode(segmentLabelmapNode)

  # CLI interface functions for starting, observing progress and processing results
  def _startCLI(self, firstRun=False):
    try:
      # Get the next segmentation ROI
      labelName, labelNode, label_idx, imageNode = self._labelGenerators.next()

      self.logger.info('Starting RadiomicsCLI for %s', labelName)

      self._labelName = labelName

      parameters = {}
      parameters['Image'] = imageNode.GetID()
      parameters['Mask'] = labelNode.GetID()
      parameters['param'] = self._parameterFile
      parameters['out'] = self._cli_output.GetID()
      parameters['label'] = label_idx

      RadiomicsCLI = slicer.modules.slicerradiomicscli

      self.logger.debug('Starting...')
      self.cliNode = slicer.cli.run(RadiomicsCLI, self.cliNode, parameters, wait_for_completion=self.runSync)

      if self.runSync:
        # process the result. If running asynchronously, this will function is called from _onStatus (triggered by ModifiedEvent)
        self._cli_done(self.cliNode.GetStatusString())
      elif firstRun:
        # Observer is only needed when running in asynchronous mode
        # They only need to be added when the CLI is initialized and started for the first time
        self.logger.debug('Adding observer')
        self._onStatusObserverTag = self.cliNode.AddObserver('ModifiedEvent', self._onStatus)
    except StopIteration:
      # finished extracting features
      self.logger.info("Extraction complete")
      self._onFinished()

  def _onStatus(self, caller, event):
    if caller.IsA('vtkMRMLCommandLineModuleNode'):
      status = caller.GetStatusString()
      if self._cli_running:
        print('.'),
        if not caller.IsBusy():
          self._cli_running = False
          self._cli_done(status)
      elif status == 'Running':
        # CLI has started
        self._cli_running = True

  def _cli_done(self, status):
    print("Done")
    errorText = self.cliNode.GetErrorText()
    if errorText != '':
      errorText = str(errorText).replace('RadiomicsCLI standard error:\n\n', '')
      print(errorText)

    if status == 'Completed':  # Completed without errors
      # Read the results out of the temp table and store them in the output table
      self._processResults(self.cliNode.GetOutputText())

    # Start the next extraction (when all extractions are done, this will clean up the CLI)
    self._startCLI()

  def _onFinished(self):
    self.logger.info('Cleaning up...')

    # Remove the observer if set
    if self._onStatusObserverTag is not None:
      slicer.mrmlScene.RemoveObserver(self._onStatusObserverTag)
      self._onStatusObserverTag = None

    # Dispose CLI node
    self.cliNode = None

    # Clean up!

    # If a temporary parameter file was used, delete it.
    if self._delete_parameterFile and os.path.isfile(self._parameterFile):
      os.remove(self._parameterFile)
    self._delete_parameterFile = False

    self._imageNode = None
    self._parameterFile = None
    self._labelGenerators = None
    self.outTable = None
    self._featureNames = {}

    # Remove the temporary table
    slicer.mrmlScene.RemoveNode(self._cli_output)
    self._cli_output = None

    self._labelName = None

    self.logger.debug('Cleanup finished')
    # Signal the widget you're done
    if self.callback is not None:
      self.callback()

    # Clean up the callback too
    self.callback = None

  # Output table functions: initializing the output table and filling it with processed results
  def _initOutputTable(self):
    if not self.outTable:
      self.logger.warning('Output table not set!')
      return

    tableWasModified = self.outTable.StartModify()
    self.outTable.RemoveAllColumns()

    self.logger.info('Initializing output table')

    # Define table columns
    for k in ['Image type', 'Feature Class', 'Feature Name']:  #  ['Label', 'Image type', 'Feature Class', 'Feature Name', 'Value']:
      col = self.outTable.AddColumn()
      col.SetName(k)

    self.outTable.Modified()
    self.outTable.EndModify(tableWasModified)

  def _processResults(self, outputText=None):
    self.logger.debug('Processing results...')
    if not self.outTable:
      self.logger.warning('Output table not set!')
      return
    if not self._cli_output:
      self.logger.warning('CLI output table not set!')
      return

    tableWasModified = self.outTable.StartModify()
    self.logger.debug('adding column')
    col = self.outTable.AddColumn()
    col.SetName(self._labelName)

    for columnIndex in range(self._cli_output.GetNumberOfColumns()):
      featureKey = self._cli_output.GetColumnName(columnIndex)
      featureValue = self._cli_output.GetCellText(0, columnIndex)

      key_parts = featureKey.split('_', 3)
      if len(key_parts) < 3:
        # We expect keys Image and Mask to be in there, and are skipped
        # However, we need not warn the user about this as it is expected...
        if featureKey != 'Image' and featureKey != 'Mask':
          self.logger.warning('Skipping key %s', featureKey)
        continue

      if featureKey not in self._featureNames:
        self.logger.debug('Adding featurekey %s', featureKey)
        rowIndex = self.outTable.AddEmptyRow()
        self.outTable.SetCellText(rowIndex, 0, key_parts[0])
        self.outTable.SetCellText(rowIndex, 1, key_parts[1])
        self.outTable.SetCellText(rowIndex, 2, key_parts[2])
        self._featureNames[featureKey] = rowIndex

      self.logger.debug('Setting column value to %s (key %s) at row %i', featureValue, featureKey, self._featureNames[featureKey])
      col.SetValue(self._featureNames[featureKey], featureValue)

    self.outTable.Modified()
    self.outTable.EndModify(tableWasModified)

  # Interaction functions
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

  def runCLI(self, imageNode, labelNode, segmentationNode, tableNode, featureClasses, settings, enabledImageTypes, callback=None):
    """
    Run the actual algorithm
    """
    if self.cliNode is not None:
      self.logger.warning('Already running an extraction!')
      return

    self.logger.info('Generating customization file')
    settings['correctMask'] = True

    json_configuration = {}
    json_configuration['setting'] = settings
    json_configuration['featureClass'] = {cls: None for cls in featureClasses}
    json_configuration['imageType'] = enabledImageTypes

    tempDir = slicer.app.temporaryPath
    parameterFile = os.path.join(tempDir, 'RadiomicsLogicParams.json')
    self._delete_parameterFile = True  # Delete this file once we're done

    with open(parameterFile, mode='w') as parameterFileFP:
      json.dump(json_configuration, parameterFileFP)

    self.runCLIWithParameterFile(imageNode, labelNode, segmentationNode, tableNode, parameterFile, callback)

  def runCLIWithParameterFile(self, imageNode, labelNode, segmentationNode, tableNode, parameterFilePath, callback=None):
    """
    Run the actual algorithm using the provided customization file and provided image and region of interest(s) (ROIs)

    :param imageNode: Slicer Volume node representing the image from which features should be extracted
    :param labelNode: Slicer Labelmap node containing the ROIs as integer encoded volume (voxel value indicates ROI id)
    :param segmentationNode: Slicer segmentation node containing the segments of the ROIs (will be converted to binary
    label maps)
    :param tableNode: Slicer Table node which will hold the calculated results
    :param parameterFilePath: String file path pointing to the parameter file used to customize the extraction
    :param callback: Function which is invoked when the CLI is done (can be used to unlock the GUI)
    """
    if self.cliNode is not None:
      self.logger.warning('Already running an extraction!')
      return

    self.logger.info('Feature extraction started')

    self._parameterFile = parameterFilePath

    self._labelGenerators = []
    if labelNode:
      self._labelGenerators = chain(self._labelGenerators, self._getLabelGeneratorFromLabelMap(labelNode, imageNode))
    if segmentationNode:
      self._labelGenerators = chain(self._labelGenerators, self._getLabelGeneratorFromSegmentationNode(segmentationNode, imageNode))

    self._cli_output = slicer.vtkMRMLTableNode()
    slicer.mrmlScene.AddNode(self._cli_output)

    self.outTable = tableNode
    self._initOutputTable()

    self.callback = callback

    self._startCLI(firstRun=True)


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
    logic.runSync = True  # Block Thread until each extraction is done (i.e. run synchronously)
    self.assertIsNotNone(logic.hasImageData(grayscaleNode))
    self.assertIsNotNone(logic.hasImageData(labelmapNode))

    featureClasses = ['firstorder']
    settings = {}
    settings['binWidth'] = 25
    settings['symmetricalGLCM'] = False
    settings['label'] = 1
    settings['correctMask'] = True

    enabledImageTypes = {"Original": {}}

    for segNode in [binaryNode, surfaceNode]:
      tableNode = slicer.vtkMRMLTableNode()
      tableNode.SetName('lung1_label and ' + segNode.GetName())
      slicer.mrmlScene.AddNode(tableNode)
      # No callback needed as tests are run synchronously
      logic.runCLI(grayscaleNode, labelmapNode, segNode, tableNode, featureClasses, settings, enabledImageTypes)
      logic.showTable(tableNode)

    tableNode = slicer.vtkMRMLTableNode()
    tableNode.SetName('lung1_label and ' + binaryNode.GetName() + ' customized with Params.yaml')
    slicer.mrmlScene.AddNode(tableNode)
    # No callback needed as tests are run synchronously
    logic.runCLIWithParameterFile(grayscaleNode, labelmapNode, binaryNode, tableNode, parameterFile)
    logic.showTable(tableNode)
    self.delayDisplay('Test passed!')
