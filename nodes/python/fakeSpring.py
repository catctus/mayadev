import math, sys
import maya.api.OpenMaya as om
#import maya.api.OpenMayaMPx as ommpx

kPluginNodeTypeName = "fakeSpring"
nodeId = om.MTypeId(0x8700)

maya_useNewAPI = True


# Node definition
class fakeSpring(om.MPxNode):

    outputA = om.MObject()
    outputB = om.MObject()

    start = om.MObject()
    end = om.MObject()
    stiffness = om.MObject()

    length = om.MObject()

    def __init__(self):
        om.MPxNode.__init__(self)


    def compute(self,plug,dataBlock):

        if plug == fakeSpring.outputA or plug == fakeSpring.outputB:

            start = dataBlock.inputValue(fakeSpring.start).asFloat3()
            startPos = om.MVector(start)

            end = dataBlock.inputValue(fakeSpring.end).asFloat3()
            endPos = om.MVector(end)

            stiffness = dataBlock.inputValue(fakeSpring.stiffness).asFloat()
            length = dataBlock.inputValue(fakeSpring.length).asFloat()


            directionalVector = endPos - startPos

            offset = (directionalVector.length() - length)/2.0
            scalor = (offset / directionalVector.length()) * stiffness

            outputAPos = startPos + (directionalVector * scalor)
            outputBPos = endPos - (directionalVector * scalor)


            outputA = dataBlock.outputValue(fakeSpring.outputA)
            outputAPosition = om.MFloatVector(outputAPos.x, outputAPos.y, outputAPos.z)
            outputA.setMFloatVector(outputAPosition)
            outputA.setClean()

            outputB = dataBlock.outputValue(fakeSpring.outputB)
            outputBPosition = om.MFloatVector(outputBPos.x, outputBPos.y, outputBPos.z)
            outputB.setMFloatVector(outputBPosition)
            outputB.setClean()

            dataBlock.setClean(plug)



# creator
def nodeCreator():
    return fakeSpring()

# initializer
def nodeInitializer():

    numattr = om.MFnNumericAttribute()
    fakeSpring.outputA = numattr.createPoint('output1', 'output1')
    om.MPxNode.addAttribute(fakeSpring.outputA)

    numattr = om.MFnNumericAttribute()
    fakeSpring.outputB = numattr.createPoint('output2', 'output2')
    om.MPxNode.addAttribute(fakeSpring.outputB)

    numattr = om.MFnNumericAttribute()
    fakeSpring.start = numattr.createPoint('start', 'start')
    om.MPxNode.addAttribute(fakeSpring.start)
    fakeSpring.attributeAffects(fakeSpring.start, fakeSpring.outputA)
    fakeSpring.attributeAffects(fakeSpring.start, fakeSpring.outputB)

    numattr = om.MFnNumericAttribute()
    fakeSpring.end = numattr.createPoint('end', 'end')
    om.MPxNode.addAttribute(fakeSpring.end)
    fakeSpring.attributeAffects(fakeSpring.end, fakeSpring.outputA)
    fakeSpring.attributeAffects(fakeSpring.end, fakeSpring.outputB)

    nAttr = om.MFnNumericAttribute()
    fakeSpring.stiffness = nAttr.create( "stiffness", "stiff", om.MFnNumericData.kFloat, 1.0 )
    nAttr.setMin(0.001)
    nAttr.keyable = True
    om.MPxNode.addAttribute(fakeSpring.stiffness)
    fakeSpring.attributeAffects(fakeSpring.stiffness, fakeSpring.outputA)
    fakeSpring.attributeAffects(fakeSpring.stiffness, fakeSpring.outputB)

    nAttr = om.MFnNumericAttribute()
    fakeSpring.length = nAttr.create( "length", "length", om.MFnNumericData.kFloat, 1.0 )
    nAttr.keyable = True
    nAttr.setMin(0)
    om.MPxNode.addAttribute(fakeSpring.length)
    fakeSpring.attributeAffects(fakeSpring.length, fakeSpring.outputA)
    fakeSpring.attributeAffects(fakeSpring.length, fakeSpring.outputB)



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
