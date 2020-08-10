"""
import maya.cmds as mc
import maya.mel as mel


mc.file(new=True, f=True)

mc.unloadPlugin('ligamentNode')
mc.loadPlugin('/ice/shared/anst/maya/dev/nodes/python/ligamentNode.py')

mel.eval('curve -d 3 -p 0 0 0 -p -3 0 -3 -p -6 0 -7 -p -7 0 -10 -p -5 0 -11 -p -3 0 -13 -k 0 -k 0 -k 0 -k 1 -k 2 -k 3 -k 3 -k 3;')
mel.eval('curve -d 3 -p 0 0 0 -p -3 0 -3 -p -6 0 -7 -p -7 0 -10 -p -5 0 -11 -p -3 0 -13 -k 0 -k 0 -k 0 -k 1 -k 2 -k 3 -k 3 -k 3;')

node = mc.createNode('ligamentNode')

mc.connectAttr('curveShape1.worldSpace', node + '.inCurve')
mc.connectAttr('curveShape2.worldSpace', node + '.refCurve')

mc.setAttr(node + '.initialize', 1)
"""
import math, sys
import maya.api.OpenMaya as om
#import maya.api.OpenMayaMPx as ommpx

kPluginNodeTypeName = "ligamentNode"
nodeId = om.MTypeId(0x8700)

maya_useNewAPI = True



# Node definition
class ligamentNode(om.MPxNode):
    
    # class variables
    inCurve = om.MObject()
    refCurve = om.MObject()
    stiffness = om.MObject()
    output = om.MObject()
    initilize = om.MObject()

    def __init__(self):
        om.MPxNode.__init__(self)

    def compute(self,plug,dataBlock):

        initilizeVal = dataBlock.inputValue(self.initilize).asShort()

        if initilizeVal == 1:
            self.initilizeStiffness(dataBlock)
            initilizeVal = dataBlock.inputValue( self.initilize ).asShort()

        if initilizeVal == 2:
            if plug == ligamentNode.output:
                return
    
    def initilizeStiffness(self, dataBlock):
        """
        sets up the default stiffness params
        """
        
        inCurveDataHandle = dataBlock.inputValue(self.inCurve)

        mCurve = inCurveDataHandle.asNurbsCurveTransformed()
        if not mCurve: return

        # stiffness
        mfnCrv = om.MFnNurbsCurve(mCurve)
        stiffnessArrayData = dataBlock.outputArrayValue(self.stiffness)
        stiffnessDataBuilder = om.MArrayDataBuilder(dataBlock, self.stiffness, int(mfnCrv.numCVs))

        # outputs
        outputArrayData = dataBlock.outputArrayValue(self.output)
        outputDataBuilder = om.MArrayDataBuilder(dataBlock, self.output, int(mfnCrv.numCVs))

        
        for i in xrange(mfnCrv.numCVs):
            stiffnessHandler = stiffnessDataBuilder.addElement(i)
            stiffnessHandler.setFloat(0.5)
            stiffnessHandler.setClean()

            outputHandler = outputDataBuilder.addElement(i)
            outputHandler.setMVector(om.MVector(0,0,0))
            outputHandler.setClean()
            
        
        stiffnessArrayData.set(stiffnessDataBuilder)
        outputArrayData.set(outputDataBuilder)
        
        setInitMode = om.MPlug(self.thisMObject(), self.initilize )
        setInitMode.setShort(2)


# creator
def nodeCreator():
    return ligamentNode()

# initializer
def nodeInitializer():


    numAttr = om.MFnNumericAttribute()
    ligamentNode.output = numAttr.createPoint('output', 'output')	
    numAttr.keyable = False
    #numAttr.hidden = True
    numAttr.array = True
    numAttr.storable = True
    numAttr.readable = True
    numAttr.writable = True
    om.MPxNode.addAttribute(ligamentNode.output)

    enumAttr = om.MFnEnumAttribute()
    ligamentNode.initilize = enumAttr.create( "initialize", "init" )
    enumAttr.addField("off", 0)
    enumAttr.addField("initialize", 1)
    enumAttr.addField("initialized", 2)
    enumAttr.keyable = True
    enumAttr.storable = True
    enumAttr.readable = True
    om.MPxNode.addAttribute(ligamentNode.initilize)
    ligamentNode.attributeAffects(ligamentNode.initilize, ligamentNode.output)
    
    typedAttr = om.MFnTypedAttribute()
    ligamentNode.inCurve = typedAttr.create( "inCurve", "inCurve", om.MFnData.kNurbsCurve)
    typedAttr.storable = True
    typedAttr.readable = True
    om.MPxNode.addAttribute(ligamentNode.inCurve)
    ligamentNode.attributeAffects(ligamentNode.inCurve, ligamentNode.output)

    typedAttr = om.MFnTypedAttribute()
    ligamentNode.refCurve = typedAttr.create( "refCurve", "refCurve", om.MFnData.kNurbsCurve)
    typedAttr.storable = True
    typedAttr.readable = True
    om.MPxNode.addAttribute(ligamentNode.refCurve)
    ligamentNode.attributeAffects(ligamentNode.refCurve, ligamentNode.output)

    nAttr = om.MFnNumericAttribute()
    ligamentNode.stiffness = nAttr.create( "stiffness", "stiff", om.MFnNumericData.kFloat, 1.0 )
    nAttr.setMin(0)
    nAttr.keyable = False
    nAttr.array = True
    nAttr.storable = True
    nAttr.readable = True
    nAttr.writable = True
    om.MPxNode.addAttribute(ligamentNode.stiffness)
    ligamentNode.attributeAffects(ligamentNode.stiffness, ligamentNode.output)


# initialize the script plug-in
def initializePlugin(mobject):
    mplugin = om.MFnPlugin(mobject)
    try:
        mplugin.registerNode( kPluginNodeTypeName, nodeId, nodeCreator, nodeInitializer )
    except:
        sys.stderr.write( "Failed to register node: %s" % kPluginNodeTypeName )
        raise

# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = om.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( nodeId )
    except:
        sys.stderr.write( "Failed to register node: %s" % kPluginNodeTypeName )
        raise
