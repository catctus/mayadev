import sys
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.api.OpenMayaAnim as oma
import maya.api.OpenMayaRender as omr

"""
import maya.cmds as mc
mc.loadPlugin('D:/development/maya/python/nodes/speedTracker.py')
"""

maya_useNewAPI = True

class speedTracker(omui.MPxLocatorNode):
    drawDbClassification = "drawdb/geometry/speedtracker"
    drawRegistrantId = "SpeedTrackerNodePlugin"
    id = om.MTypeId(0x80007)


    size = om.MObject()
    input = om.MObject()
    output = om.MObject()
    parentPosition = om.MObject()

    fps = om.MObject()
    scaleUnits = om.MObject()
    timeUnits = om.MObject()
    workingUnits = om.MObject()


    @staticmethod
    def creator():
        return speedTracker()

    @staticmethod
    def initialize():

        numFn = om.MFnNumericAttribute()
        speedTracker.size = numFn.create( "fontSize", "fs", om.MFnNumericData.kInt)
        numFn.default = 12.0
        numFn.storable = True
        numFn.readable = True
        numFn.writable = True
        numFn.keyable = True

        om.MPxNode.addAttribute(speedTracker.size)

        vectorFn = om.MFnNumericAttribute()
        speedTracker.input = vectorFn.createPoint('input', 'i')
        om.MPxNode.addAttribute(speedTracker.input)

        vectorFn = om.MFnNumericAttribute()
        speedTracker.parentPosition = vectorFn.createPoint('parentPosition', 'pp')
        om.MPxNode.addAttribute(speedTracker.parentPosition)

        numFn = om.MFnNumericAttribute()
        speedTracker.output = numFn.create( "output", "out", om.MFnNumericData.kFloat)
        om.MPxNode.addAttribute(speedTracker.output)

        speedTracker.attributeAffects(speedTracker.input, speedTracker.output)

        numFn = om.MFnNumericAttribute()
        speedTracker.fps = numFn.create( "framesPerSecond", "fps", om.MFnNumericData.kFloat)
        numFn.default = 24.0
        numFn.storable = True
        numFn.readable = True
        numFn.writable = True
        numFn.keyable = True

        om.MPxNode.addAttribute(speedTracker.fps)
        speedTracker.attributeAffects(speedTracker.fps, speedTracker.output)

        enumAttr = om.MFnEnumAttribute()
        speedTracker.workingUnits = enumAttr.create( "workingUnits", "wu" )
        enumAttr.addField("cm", 0)
        enumAttr.addField("meter", 1)
        enumAttr.storable = True
        enumAttr.readable = True
        enumAttr.writable = True
        enumAttr.default = 0
        enumAttr.keyable = True
        om.MPxNode.addAttribute(speedTracker.workingUnits)
        speedTracker.attributeAffects(speedTracker.workingUnits, speedTracker.output)

        enumAttr = om.MFnEnumAttribute()
        speedTracker.timeUnits = enumAttr.create( "timeUnits", "tu" )
        enumAttr.addField("sec", 0)
        enumAttr.addField("min", 1)
        enumAttr.addField("hour", 2)
        enumAttr.storable = True
        enumAttr.readable = True
        enumAttr.writable = True
        enumAttr.default = 0
        enumAttr.keyable = True
        om.MPxNode.addAttribute(speedTracker.timeUnits)
        speedTracker.attributeAffects(speedTracker.timeUnits, speedTracker.output)

        enumAttr = om.MFnEnumAttribute()
        speedTracker.scaleUnits = enumAttr.create( "scaleUnits", "su" )
        enumAttr.addField("mm", 0)
        enumAttr.addField("cm", 1)
        enumAttr.addField("m", 2)
        enumAttr.addField("km", 3)
        enumAttr.default = 1
        enumAttr.storable = True
        enumAttr.readable = True
        enumAttr.writable = True
        enumAttr.keyable = True

        om.MPxNode.addAttribute(speedTracker.scaleUnits)
        speedTracker.attributeAffects(speedTracker.scaleUnits, speedTracker.output)

    def __init__(self):
        omui.MPxLocatorNode.__init__(self)

        self._prevPosition = None

    def compute(self, plug, dataBlock):

        if ( plug == speedTracker.output ):

            inputVector = dataBlock.inputValue(speedTracker.input).asFloat3()
            currentPosition = om.MVector(inputVector)

            fps = dataBlock.inputValue(speedTracker.fps).asFloat()

            workingUnits = dataBlock.inputValue(speedTracker.workingUnits).asShort()
            scaleUnits = dataBlock.inputValue(speedTracker.scaleUnits).asShort()
            timeUnits = dataBlock.inputValue(speedTracker.timeUnits).asShort()

            if not self._prevPosition:
                self._prevPosition = currentPosition

            vdistance = self._prevPosition - currentPosition

            distance = vdistance.length()

            # calculate in cm (which is usually default )
            if workingUnits == 1:
                distance *= 100

            if scaleUnits == 0:
                # mm
                distance *= 10
            elif scaleUnits == 2:
                # meter
                distance = distance / 100.0
            elif scaleUnits == 3:
                # km
                meter = distance / 100.0
                distance = meter / 1000.0

            if timeUnits == 0:
                # seconds
                speed = distance / (1.0/fps)
            elif timeUnits == 1:
                # min
                speed = distance / ((1.0/fps) * 60)
            elif timeUnits == 2:
                # hour
                speed = distance / ((1.0/fps) * 3600)

            outputHandle = dataBlock.outputValue(speedTracker.output)
            outputHandle.setFloat(speed)
            dataBlock.setClean( plug )

            self._prevPosition = currentPosition
    """
    def boundingBox(self):
        self.boundingBox
        corner1 = om.MPoint( -0.17, 0.0, -0.7 )
        corner2 = om.MPoint( 0.17, 0.0, 0.3 )
        return om.MBoundingBox( corner1, corner2 )
    """
    def draw(self, view, path, style, status):

        # Getting the OpenGL renderer
        glRenderer = omr.MHardwareRenderer.theRenderer()
        # Getting all classes from the renderer
        glFT = glRenderer.glFunctionTable()

        # Pushed current state
        #glFT.glPushAttrib( omr.MGL_CURRENT_BIT )
        # Defined Blend function
        #glFT.glBlendFunc( omr.MGL_SRC_ALPHA, omr.MGL_ONE_MINUS_SRC_ALPHA )
        # create x-ray view and will be seen always
        #glFT.glDisable( omr.MGL_DEPTH_TEST )

        # Starting the OpenGL drawing

        view.beginGL()

        activeView = view.active3dView()

        view.drawText("3D SPACE TEXT", OpenMaya.MPoint(0,1,0), OpenMayaUI.M3dView.kCenter )

        view.endGL()

    def isBounded(self):
        return True

class speedTrackerData(om.MUserData):
    def __init__(self):
        om.MUserData.__init__(self, False)

        self.size = 12.0
        self.speed = 0.0
        self.scaleUnits = 0
        self.timeUnits = 0
        self.position = om.MPoint(0,0,0)

class speedTrackerDrawOverride(omr.MPxDrawOverride):

    @staticmethod
    def creator(mobject):
        return speedTrackerDrawOverride(mobject)

    @staticmethod
    def draw(context, data):
        return

    def __init__(self, obj):
        omr.MPxDrawOverride.__init__(self, obj, speedTrackerDrawOverride.draw)
        self.mCustomBoxDraw = False

    def supportedDrawAPIs(self):
        return omr.MRenderer.kOpenGL | omr.MRenderer.kDirectX11 | omr.MRenderer.kOpenGLCoreProfile

    def isBounded(self, objPath, cameraPath):
        return False

    def boundingBox(self, objPath, cameraPath):
        corner1 = om.MPoint( -0.17, 0.0, -0.7 )
        corner2 = om.MPoint( 0.17, 0.0, 0.3 )

        self.mCurrentBoundingBox.clear()
        self.mCurrentBoundingBox.expand( corner1 )
        self.mCurrentBoundingBox.expand( corner2 )

        return self.mCurrentBoundingBox

    def disableInternalBoundingBoxDraw(self):
        return self.mCustomBoxDraw

    def prepareForDraw(self, objPath, cameraPath, frameContext, data):


        if not isinstance(data, speedTrackerData):
			data = speedTrackerData()

        node = objPath.node()
        data.size = om.MPlug(node, speedTracker.size).asInt()
        data.speed = om.MPlug(node, speedTracker.output).asFloat()
        data.scaleUnits = om.MPlug(node, speedTracker.scaleUnits).asShort()
        data.timeUnits = om.MPlug(node, speedTracker.timeUnits).asShort()

        posData = om.MPlug(node, speedTracker.parentPosition).asMDataHandle()
        data.position = om.MPoint(posData.asFloat3())

        return data

    def hasUIDrawables(self):
        return True

    def addUIDrawables(self, objPath, drawManager, frameContext, data):
        if not isinstance(data, speedTrackerData): return

        speedTextRaw = "{speed} {meterUnits}/{timeUnits}"

        scaleUnit = 'cm'
        if data.scaleUnits == 0:
            scaleUnit = 'mm'
        elif data.scaleUnits == 2:
            scaleUnit = 'm'
        elif data.scaleUnits == 3:
            scaleUnit = 'km'

        timeUnit = 'sec'
        if data.timeUnits == 1:
            timeUnit = 'min'
        elif data.timeUnits == 2:
            timeUnit = 'hour'

        speedText = speedTextRaw.format(speed=round(data.speed, 3),
                                        meterUnits=scaleUnit,
                                        timeUnits=timeUnit)

        drawManager.beginDrawable(omr.MUIDrawManager.kAutomatic, False)
        drawManager.setFontSize(data.size)
        drawManager.text(data.position, speedText, omr.MUIDrawManager.kLeft)
        drawManager.endDrawable()

    def getMultiplier(self, objPath):
        ## Retrieve value of the size attribute from the node
        node = objPath.node()
        plug = om.MPlug(node, speedTracker.size)
        if not plug.isNull:
            sizeVal = plug.asMDistance()
            return sizeVal.asCentimeters()

        return 1.0

def initializePlugin(mobject):
    plugin = om.MFnPlugin(mobject, "Autodesk", "3.0", "Any")

    try:
        plugin.registerNode("speedTracker", speedTracker.id, speedTracker.creator, speedTracker.initialize, om.MPxNode.kLocatorNode, speedTracker.drawDbClassification)
    except:
        sys.stderr.write("Failed to register node\n")
        raise

    try:
        omr.MDrawRegistry.registerDrawOverrideCreator(speedTracker.drawDbClassification, speedTracker.drawRegistrantId, speedTrackerDrawOverride.creator)
    except:
        sys.stderr.write("Failed to register override\n")
        raise

def uninitializePlugin(mobject):
    plugin = om.MFnPlugin(mobject)

    try: plugin.deregisterNode(speedTracker.id)
    except:
        sys.stderr.write("Failed to deregister node\n")
        pass

    try: omr.MDrawRegistry.deregisterDrawOverrideCreator(speedTracker.drawDbClassification, speedTracker.drawRegistrantId)
    except:
        sys.stderr.write("Failed to deregister override\n")
        pass
