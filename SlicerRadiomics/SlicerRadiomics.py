import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import SimpleITK as sitk
from radiomics import imageoperations, firstorder, glcm, glrlm, shape, glszm, gldm, ngtdm, gldzm

#
# SlicerRadiomics
#

class SlicerRadiomics(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "SlicerRadiomics" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Informatics"]
    self.parent.dependencies = []
    self.parent.contributors = ["Nicole Aucion (BWH)"]
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
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputVolumeSelector = slicer.qMRMLNodeComboBox()
    self.inputVolumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputVolumeSelector.selectNodeUponCreation = True
    self.inputVolumeSelector.addEnabled = False
    self.inputVolumeSelector.removeEnabled = False
    self.inputVolumeSelector.noneEnabled = False
    self.inputVolumeSelector.showHidden = False
    self.inputVolumeSelector.showChildNodeTypes = False
    self.inputVolumeSelector.setMRMLScene( slicer.mrmlScene )
    self.inputVolumeSelector.setToolTip( "Pick the input image for the feature calculation." )
    parametersFormLayout.addRow("Input Image Volume: ", self.inputVolumeSelector)

    #
    # input mask volume selector
    #
    self.inputMaskSelector = slicer.qMRMLNodeComboBox()
    self.inputMaskSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
    self.inputMaskSelector.selectNodeUponCreation = True
    self.inputMaskSelector.addEnabled = False
    self.inputMaskSelector.removeEnabled = False
    self.inputMaskSelector.noneEnabled = False
    self.inputMaskSelector.showHidden = False
    self.inputMaskSelector.showChildNodeTypes = False
    self.inputMaskSelector.setMRMLScene( slicer.mrmlScene )
    self.inputMaskSelector.setToolTip( "Pick the input mask for the feature calclation." )
    parametersFormLayout.addRow("Input Mask Volume: ", self.inputMaskSelector)

    #
    # Feature class selection, defaults to all
    #
    self.featuresGroupBox = ctk.ctkCollapsibleGroupBox(self.parent)
    self.layout.addWidget(self.featuresGroupBox)
    self.featuresGroupBox.collapsed = False
    self.featuresGroupBox.title = "Features"
#    layout = qt.QHBoxLayout(self.featuresGroupBox)
    self.featuresGroupBox.setLayout(qt.QHBoxLayout())


    self.featuresButtonGroup = qt.QButtonGroup(self.featuresGroupBox)
    self.featuresButtonGroup.exclusive = False

    # create a checkbox for each feature, checked by default
    self.features = ["firstorder", "glcm", "glrlm", "shape", "glszm", "gldm", "ngtdm", "gldzm"]
    featureButtons = {}
    for feature in self.features:
      featureButtons[feature] = qt.QCheckBox(feature)
      print 'Making a button for ', feature, ' = ', featureButtons[feature]
      # TODO: enable all features by default
      featureButtons[feature].checked = False
      if feature == 'firstorder':
        featureButtons[feature].checked = True
      self.featuresButtonGroup.addButton(featureButtons[feature])
      self.featuresGroupBox.layout().addWidget(featureButtons[feature])
      # set the ID to be the index of this feature in the list
      self.featuresButtonGroup.setId(featureButtons[feature], self.features.index(feature))

    print 'Feature buttons group buttons = ',self.featuresButtonGroup.buttons()
    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.inputMaskSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputVolumeSelector.currentNode() and self.inputMaskSelector.currentNode()

  def getCheckedFeatureClasses(self):
    checkedFeatures = []
    featureButtons = self.featuresButtonGroup.buttons()
    for featureButton in featureButtons:
      if featureButton.checked:
        featureIndex = self.featuresButtonGroup.id(featureButton);
        feature = self.features[featureIndex]
        checkedFeatures.append(feature)
    return checkedFeatures

  def onApplyButton(self):
    logic = SlicerRadiomicsLogic()
    featureClasses = self.getCheckedFeatureClasses()
    logic.run(self.inputVolumeSelector.currentNode(), self.inputMaskSelector.currentNode(), featureClasses)

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

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def calculateFeature(self, inputVolume, inputMaskVolume, feature):
    """
    Calculate a single feature on the input MRML volume nodes
    """
    # TBD: get itk image
    # testImage = inputVolume.GetImageData()
    # testMask = inputMaskVolume.GetImageData()

    volumeFileName = inputVolume.GetStorageNode().GetFileName()
    maskFileName = inputMaskVolume.GetStorageNode().GetFileName()
    testImage = sitk.ReadImage(volumeFileName)
    testMask = sitk.ReadImage(maskFileName)

    # TBD: update form default arguments
    kwargs = {}
    kwargs['binWidth'] = 25
    kwargs['symmetricalGLCM'] = False  # Current baseline is based upon assymetrical GLCM
    kwargs['verbose'] = False

    if feature == 'firstorder':
      featureClass = firstorder.RadiomicsFirstOrder(testImage, testMask, **kwargs)
    elif feature == 'glcm':
      featureClass = glcm.RadiomicsGLCM(testImage, testMask, **kwargs)
    elif feature == 'glrlm':
      featureClass = glrlm.RadiomicsGLRLM(testImage, testMask, **kwargs)
    elif feature == 'shape':
      featureClass = shape.RadiomicsShape(testImage, testMask, **kwargs)
    elif feature == 'glszm':
      featureClass = glszm.RadiomicsGLSZM(testImage, testMask, **kwargs)
    elif feature == 'gldm':
      featureClass = gldm.RadiomicsGLDM(testImage, testMask, **kwargs)
    elif feature == 'ngtdm':
      featureClass = ngtdm.RadiomicsNGTDM(testImage, testMask, **kwargs)
    elif feature == 'gldzm':
      featureClass = gldzm.RadiomicsGLDZM(testImage, testMask, **kwargs)

    featureClass.enableAllFeatures()
    featureClass.calculateFeatures()
    # get the result
    self.featureValues[feature] = featureClass.featureValues

  def run(self, inputVolume, inputMaskVolume, featureClasses):
    """
    Run the actual algorithm
    """

    logging.info('Processing started')
    logging.debug('featureClasses = %s' % (featureClasses))
    logging.debug('input volume file name = %s' % (inputVolume.GetStorageNode().GetFileName()))


    self.featureValues = {}

    for feature in featureClasses:
      self.calculateFeature(inputVolume, inputMaskVolume, feature)

    logging.info('Processing completed')

    logging.info(self.featureValues)

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

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('https://github.com/Radiomics/pyradiomics/blob/master/data/lung1_image.nrrd', 'lung1_image.nrrd', sitk.ReadImage),
        ('https://github.com/Radiomics/pyradiomics/blob/master/data/lung1_label.nrrd', 'lung1_label.nrrd', sitk.ReadImage),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="lung1_image")
    maskNode = slicer.util.getNode(pattern="lung1_label")
    logic = SlicerRadiomicsLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.assertIsNotNone( logic.hasImageData(maskNode) )

    features = self.getCheckedFeatureClasses()
    for feature in features:
       logic.calculateFeature(volumeNode, maskNode, feature)

    self.delayDisplay('Test passed!')
