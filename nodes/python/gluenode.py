import math, sys
import maya.api.OpenMaya as om
#import maya.api.OpenMayaMPx as ommpx

kPluginNodeTypeName = "glueNode"
nodeId = om.MTypeId(0x8700)

maya_useNewAPI = True


# Node definition
class glueNode(om.MPxNode):
    # class variables
    origin = om.MObject()
    goal = om.MObject()
    output = om.MObject()
    inTime = om.MObject()
    attractDistance = om.MObject()
    lockDistance = om.MObject()
    stiffness = om.MObject()

    def __init__(self):
        om.MPxNode.__init__(self)

        self._initilized = False
        self._prevPosition = None
        self._prevDistance = None
        self._lockPosition = None
        self._locked = False
        self._lockWeight = 0.0
        self._previousTime = om.MTime()

    def compute(self,plug,dataBlock):

        if plug == glueNode.output:
            origin = dataBlock.inputValue(glueNode.origin).asFloat3()
            originPos = om.MVector(origin)

            goal = dataBlock.inputValue(glueNode.goal).asFloat3()
            goalPos = om.MVector(goal)

            currentTime = dataBlock.inputValue(glueNode.inTime).asTime()

            attractDistance = dataBlock.inputValue(glueNode.attractDistance).asFloat()
            lockDistance = dataBlock.inputValue(glueNode.lockDistance).asFloat()
            stiffness = dataBlock.inputValue(glueNode.stiffness).asFloat()

            if not self._initilized:
                self._previousTime = currentTime
                self._prevPosition = originPos
                self._prevDistance = (goalPos - originPos).length()
                self._initilized = True

            timeDiff = currentTime.value - self._previousTime.value

            if timeDiff > 1.0 or timeDiff < 0.0:
                #self._initilized = False
                self._previousTime = currentTime
                return


            finalPosition = originPos
            distance = (goalPos - originPos).length()

            if distance < lockDistance:
                self._locked = True

            if distance <= attractDistance and self._locked:
                goalVector = ((goalPos - self._prevPosition) * self._lockWeight) * stiffness
                finalPosition = originPos + goalVector
                self._lockWeight = 1.0-(distance/attractDistance)
            else:
                self._locked = False
                finalPosition = originPos

            """
            if distance <= attractDistance:
                if distance <= self._prevDistance and not self._locked:
                    if distance != 0:
                        self._lockWeight = 1.0-(distance/attractDistance)
                else:

                    if not self._locked:
                        self._lockPosition = goalPos

                    self._locked = True
                    goalVector = ((goalPos - self._lockPosition) * self._lockWeight) * stiffness
                    finalPosition = originPos + goalVector
                    self._lockWeight = 1.0-(distance/attractDistance)
            else:
                self._locked = False
                self._lockWeight = 0.0
                finalPosition = originPos
            """

            # remember positions
            #self._prevDistance = distance
            self._prevPosition = finalPosition

            output = dataBlock.outputValue(glueNode.output)
            finalPos = om.MFloatVector(finalPosition.x, finalPosition.y, finalPosition.z)
            output.setMFloatVector(finalPos)
            output.setClean()
            dataBlock.setClean(plug)










# creator
def nodeCreator():
    return glueNode()

# initializer
def nodeInitializer():

    numattr = om.MFnNumericAttribute()
    glueNode.output = numattr.createPoint('output', 'output')
    om.MPxNode.addAttribute(glueNode.output)

    uAttr = om.MFnUnitAttribute()
    glueNode.inTime = uAttr.create('time', 'time', om.MFnUnitAttribute.kTime, 0.0)
    om.MPxNode.addAttribute(glueNode.inTime)
    glueNode.attributeAffects(glueNode.inTime, glueNode.output)

    nAttr = om.MFnNumericAttribute()
    glueNode.attractDistance = nAttr.create( "attractDistance", "ad", om.MFnNumericData.kFloat, 1.0 )
    nAttr.setMin(0.001)
    om.MPxNode.addAttribute(glueNode.attractDistance)
    glueNode.attributeAffects(glueNode.attractDistance, glueNode.output)

    nAttr = om.MFnNumericAttribute()
    glueNode.lockDistance = nAttr.create( "lockDistance", "ld", om.MFnNumericData.kFloat, 0.5 )
    nAttr.setMin(0.001)
    om.MPxNode.addAttribute(glueNode.lockDistance)
    glueNode.attributeAffects(glueNode.lockDistance, glueNode.output)

    nAttr = om.MFnNumericAttribute()
    glueNode.stiffness = nAttr.create( "stiffness", "stiff", om.MFnNumericData.kFloat, 1.0 )
    nAttr.setMin(0)
    om.MPxNode.addAttribute(glueNode.stiffness)
    glueNode.attributeAffects(glueNode.stiffness, glueNode.output)



    numattr = om.MFnNumericAttribute()
    glueNode.origin = numattr.createPoint('origin', 'origin')
    om.MPxNode.addAttribute(glueNode.origin)
    glueNode.attributeAffects(glueNode.origin, glueNode.output)

    numattr = om.MFnNumericAttribute()
    glueNode.goal = numattr.createPoint('goal', 'goal')
    om.MPxNode.addAttribute(glueNode.goal)
    glueNode.attributeAffects(glueNode.goal, glueNode.output)


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
