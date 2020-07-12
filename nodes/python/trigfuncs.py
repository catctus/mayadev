import math, sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx

kPluginNodeTypeName = "TrigNode"
TrigNodeId = OpenMaya.MTypeId(0x1001)

# Node definition
class TrigNode(OpenMayaMPx.MPxNode):

    # class variables
    input = OpenMaya.MObject()
    output = OpenMaya.MObject()
    operation = OpenMaya.MObject()
    outputtype = OpenMaya.MObject()

    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)

    def compute(self, plug, dataBlock):
        if ( plug == TrigNode.output):

            dataHandle = dataBlock.inputValue( TrigNode.input )


            inputFloat = dataHandle.asFloat()

            dataHandle = dataBlock.inputValue( TrigNode.operation)
            op = dataHandle.asShort()

            if op == 0: radians = math.acos(inputFloat)
            elif op == 1: radians = math.asin(inputFloat)
            else: radians = math.atan(inputFloat)

            outputtype_dataHandle = dataBlock.inputValue( TrigNode.outputtype)
            ot = outputtype_dataHandle.asShort()

            if ot == 0:
                degrees = math.degrees(radians)
                outputHandle = dataBlock.outputValue(TrigNode.output)
                outputHandle.setFloat(degrees)
            else:
                outputHandle = dataBlock.outputValue(TrigNode.output)
                outputHandle.setFloat(radians)

            dataBlock.setClean(plug)


def nodeCreator():
    return OpenMayaMPx.asMPxPtr( TrigNode() )

# initializer
def nodeInitializer():
    # input
    nAttr = OpenMaya.MFnNumericAttribute()
    TrigNode.input = nAttr.create( "input", "in", OpenMaya.MFnNumericData.kFloat, 0.0 )
    nAttr.setStorable(1)
    # output
    nAttr = OpenMaya.MFnNumericAttribute()
    TrigNode.output = nAttr.create( "output", "out", OpenMaya.MFnNumericData.kFloat, 0.0 )
    nAttr.setStorable(1)
    nAttr.setWritable(1)

    # enum for choosing operation
    nAttr = OpenMaya.MFnEnumAttribute()
    TrigNode.operation = nAttr.create( "operation", "op", 0)

    nAttr.addField("arccos", 0)
    nAttr.addField("arcsin", 1)
    nAttr.addField("arctan", 2)

    nAttr.setStorable(1)
    nAttr.setWritable(1)


    # enum for choosing operation
    TrigNode.outputtype = nAttr.create( "outputType", "ot", 0)

    nAttr.addField("degrees", 0)
    nAttr.addField("radians", 1)

    nAttr.setStorable(1)
    nAttr.setWritable(1)


    # add attributes
    TrigNode.addAttribute( TrigNode.input )
    TrigNode.addAttribute( TrigNode.output )
    TrigNode.addAttribute( TrigNode.operation )
    TrigNode.addAttribute( TrigNode.outputtype )

    TrigNode.attributeAffects( TrigNode.input, TrigNode.output)
    TrigNode.attributeAffects( TrigNode.operation, TrigNode.output)
    TrigNode.attributeAffects( TrigNode.outputtype, TrigNode.output)

# initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerNode( kPluginNodeTypeName, TrigNodeId, nodeCreator, nodeInitializer )
    except:
        sys.stderr.write( "Failed to register node: %s" % kPluginNodeTypeName )
        raise

# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( TrigNodeId )
    except:
        sys.stderr.write( "Failed to register node: %s" % kPluginNodeTypeName )
        raise
