import math, sys
import maya.OpenMaya as om
import maya.OpenMayaMPx as OpenMayaMPx

kPluginNodeTypeName = "blendCurve"
blendCurveNodeId = om.MTypeId(0x1002)

# Node definition
class BlendCurveNode(OpenMayaMPx.MPxNode):

    # class variables
    inputCurveA = om.MObject()
    inputCurveB = om.MObject()
    outCurve = om.MObject()
    curveRamp = om.MObject()

    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)

    def compute(self, plug, dataBlock):
        if ( plug == BlendCurveNode.outCurve ):

            # check position and blend based on curve ramp
            curveADataHandle = dataBlock.inputValue(BlendCurveNode.inputCurveA)
            curveBDataHandle = dataBlock.inputValue(BlendCurveNode.inputCurveB)
            outCurveDataHandle = dataBlock.outputValue(BlendCurveNode.outCurve)
            mCurveA = curveADataHandle.asNurbsCurveTransformed()
            mCurveB = curveBDataHandle.asNurbsCurveTransformed()

            oThis = self.thisMObject();
            curveAttr = om.MRampAttribute(oThis, BlendCurveNode.curveRamp)

            # calculate output
            if not mCurveA.isNull() and not mCurveB.isNull():

                mfnCurveA = om.MFnNurbsCurve(mCurveA)
                countA = mfnCurveA.numCVs()

                mfnCurveA = om.MFnNurbsCurve(mCurveB)
                countB = mfnCurveA.numCVs()

                if countA != countB:
                    sys.stderr.write("inputCurve1 and inputCurve2 doesn't have the same amount of cvs!")
                    return

                dataCreator = om.MFnNurbsCurveData()
                nurbCurveData = dataCreator.create()

                mfnCurveOut = om.MFnNurbsCurve()
                mpointarray = om.MPointArray(countA, om.MPoint(0,0,0))

                span = mpointarray.length() - 1
                nknots    = span + 2*1 - 1;
                knots = om.MDoubleArray()

                for i in xrange(nknots): knots.append(i)

                mfnCurveOut.create(mpointarray, knots, 1, om.MFnNurbsCurve.kOpen, False, False, nurbCurveData)
                mCurveACvItrA = om.MItCurveCV(mCurveA)
                mCurveACvItrB = om.MItCurveCV(mCurveB)

                add = 1.0/(countA -1)
                tot = 0.0
                i = 0;
                while not mCurveACvItrA.isDone():

                    # get positions
                    posA = om.MVector(mCurveACvItrA.position())
                    posB = om.MVector(mCurveACvItrB.position())

                    # get the ramp value
                    val_util = om.MScriptUtil(0.0)
                    val_ptr = val_util.asFloatPtr()
                    curveAttr.getValueAtPosition(tot, val_ptr)
                    ramp_val = val_util.getFloat(val_ptr)

                    newVector = posB-posA
                    weighted =  newVector * ramp_val
                    outpos = weighted + posA

                    mfnCurveOut.setCV(i, om.MPoint(outpos))

                    i +=1
                    tot += add

                    mCurveACvItrA.next()
                    mCurveACvItrB.next()

                mCurveACvItrA.reset()
                mCurveACvItrB.reset()
                outCurveDataHandle.setMObject(nurbCurveData)
                dataBlock.setClean(plug);


            return

def nodeCreator():
    return OpenMayaMPx.asMPxPtr( BlendCurveNode() )

# initializer
def nodeInitializer():

    rampAttr = om.MRampAttribute()
    typedAttr = om.MFnTypedAttribute()

    BlendCurveNode.curveRamp = rampAttr.createCurveRamp( "curveRamp", "cr")

    BlendCurveNode.outCurve = typedAttr.create( "outCurve", "ocurve", om.MFnData.kNurbsCurve)
    typedAttr.setStorable(1)
    typedAttr.setWritable(1)

    BlendCurveNode.inputCurveA = typedAttr.create( "inputCurve1", "inc1", om.MFnData.kNurbsCurve)
    typedAttr.setStorable(1)
    typedAttr.setWritable(1)

    BlendCurveNode.inputCurveB = typedAttr.create( "inputCurve2", "inc2", om.MFnData.kNurbsCurve)
    typedAttr.setStorable(1)
    typedAttr.setWritable(1)


    # add attributes
    BlendCurveNode.addAttribute( BlendCurveNode.curveRamp )
    BlendCurveNode.addAttribute( BlendCurveNode.outCurve )
    BlendCurveNode.addAttribute( BlendCurveNode.inputCurveA )
    BlendCurveNode.addAttribute( BlendCurveNode.inputCurveB )

    BlendCurveNode.attributeAffects( BlendCurveNode.curveRamp, BlendCurveNode.outCurve )
    BlendCurveNode.attributeAffects( BlendCurveNode.inputCurveA, BlendCurveNode.outCurve )
    BlendCurveNode.attributeAffects( BlendCurveNode.inputCurveB, BlendCurveNode.outCurve )

# initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerNode( kPluginNodeTypeName, blendCurveNodeId, nodeCreator, nodeInitializer )
    except:
        sys.stderr.write( "Failed to register node: %s" % kPluginNodeTypeName )
        raise

# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( blendCurveNodeId )
    except:
        sys.stderr.write( "Failed to register node: %s" % kPluginNodeTypeName )
        raise


"""
import maya.cmds as cmds

curve1 = cmds.curve(p=[[0,0,0], [1,2,3], [4,5,6], [5,8,9]], d=1)
curve2 = cmds.curve(p=[[0,0,0], [3,2,1], [6,5,4], [9,8,9]], d=1)
curveOut = cmds.curve(p=[[0,0,0], [1,1,1], [2,2,2]], d=1)

bc = cmds.createNode('blendCurve')

shpA = cmds.listRelatives(curve1, s=True)[0]
shpB = cmds.listRelatives(curve2, s=True)[0]
shpOut = cmds.listRelatives(curveOut, s=True)[0]


cmds.connectAttr(shpA + ".worldSpace", bc + ".inputCurve1")
cmds.connectAttr(shpB + ".worldSpace", bc + ".inputCurve2")
cmds.connectAttr(bc + ".outCurve", shpOut + ".create")
"""
