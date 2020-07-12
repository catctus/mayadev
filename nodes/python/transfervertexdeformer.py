"""
import maya.cmds as mc

mc.loadPlugin('D:/development/maya/python/nodes/transfervertexdeformer.py')


a = mc.listRelatives(mc.polySphere(ch=False)[0], s=True)[0]
b = mc.listRelatives(mc.polySphere(ch=False)[0], s=True)[0]

mc.select(a)
node = mc.deformer(type='TransferVertexDeformer')[0]

mc.connectAttr(b + '.outMesh', node  + '.inputMesh')

mc.setAttr(node + '.initialize', 1)

"""
import math, sys
import maya.cmds as mc
import maya.OpenMaya as om
import maya.OpenMayaMPx as omMPx

# name of deformer
kPluginNodeTypeName = "TransferVertexDeformer"

#maya_useNewAPI = True

#id
transferVertexDeformerID = om.MTypeId(0x1002)

class TransferVertexDeformer( omMPx.MPxDeformerNode ):

    # the input mesh
    inputMesh  = om.MObject()

    # rebind
    initilizeData = om.MObject()
    transferType = om.MObject()

    # mapping
    vertexMapping = om.MObject()


    def __init__(self):
        omMPx.MPxDeformerNode.__init__(self)

    def deform(self, data, iter, localToWorldMatrix, mIndex ):

        initializedMapping = data.inputValue(self.initilizeData).asShort()

        if( initializedMapping == 1):
            self.remap(data, iter, localToWorldMatrix, mIndex)
            initializedMapping = data.inputValue( self.initilizeData ).asShort()

        if(initializedMapping == 2):
            envelope = omMPx.cvar.MPxGeometryFilter_envelope
            envelopeHandle = data.inputValue( envelope )
            env = envelopeHandle.asFloat()

            vtxMapArrayData  = data.inputArrayValue(self.vertexMapping)

            meshAttrHandle = data.inputValue(self.inputMesh)
            driverMesh = meshAttrHandle.asMesh()
            driverMFnMesh = om.MFnMesh(driverMesh)
            driverVtxIter = om.MItMeshVertex(driverMesh)

            while not iter.isDone():
                weight = self.weightValue( data, mIndex, iter.index())
                totalWeight = weight * env;

                if totalWeight != 0:
                    vtxMapArrayData.jumpToElement(iter.index())
                    mappedIndex = vtxMapArrayData.inputValue().asInt()

                    if mappedIndex != -1:
                        util = om.MScriptUtil()
                        prevInt = util.asIntPtr()
                        driverVtxIter.setIndex(mappedIndex, prevInt)

                        iterPt = iter.position() * localToWorldMatrix

                        mappedPt = driverVtxIter.position( om.MSpace.kWorld )

                        pt = iterPt + ((mappedPt - iterPt) * totalWeight )
                        pt = pt * localToWorldMatrix.inverse()

                        iter.setPosition(pt)

                iter.next()





    def remap(self, data, iter, localToWorldMatrix, mIndex):

        # check what kind of bind we want to perform
        # worldspace or uv based
        transferType = data.inputValue(self.transferType).asShort()

        meshAttrHandle = data.inputValue(self.inputMesh)
        driverMesh = meshAttrHandle.asMesh()


        driverVtxIter = om.MItMeshVertex(driverMesh)
        driverMFnMesh = om.MFnMesh(driverMesh)

        vtxMappingArrayData = data.outputArrayValue(self.vertexMapping)
        vtxMapOutArrayBuilder = om.MArrayDataBuilder(self.vertexMapping,
                                                     iter.count())

        indexArray = om.MPointArray()

        inputAttribute = omMPx.cvar.MPxGeometryFilter_input
        inputGeometryAttribute = omMPx.cvar.MPxGeometryFilter_inputGeom
        inputHandle = data.outputArrayValue( inputAttribute )
        inputHandle.jumpToElement( mIndex )
        drivenMesh = inputHandle.outputValue().child( inputGeometryAttribute ).asMesh()

        drivenVtxIter = om.MItMeshVertex(drivenMesh)

        driven = om.MFnMesh(drivenMesh)

        if transferType == 0:

            u, v = om.MFloatArray(), om.MFloatArray()
            driverUvs = driverMFnMesh.getUVs(u, v)
            sortedDriverUvs = map(list, zip(u, v))

            while not drivenVtxIter.isDone():
                drivenIndex = drivenVtxIter.index()
                vtxMapDataHandler = vtxMapOutArrayBuilder.addElement(drivenIndex)
                vtxMapDataHandler.setInt(-1)
                vtxMapDataHandler.setClean()

                drivenVtxIter.next()

            drivenVtxIter.reset()

            driverMapped = {}
            while not driverVtxIter.isDone():

                u, v = self.getMeshUVAtIndex(driverVtxIter)
                driverIndex = int(driverVtxIter.index())
                uvKey = str([u,v])
                driverMapped.update({uvKey:driverIndex})
                driverVtxIter.next()

            drivenVtxIter.reset()

            while not drivenVtxIter.isDone():

                drivenIndex = drivenVtxIter.index()

                d_u, d_v = self.getMeshUVAtIndex(drivenVtxIter)
                driven_uv = [d_u, d_v]

                if driven_uv in sortedDriverUvs:
                    if driverMapped.has_key(str(driven_uv)):
                        driverIndex = driverMapped[str(driven_uv)]
                        vtxMapDataHandler = vtxMapOutArrayBuilder.addElement(drivenIndex)
                        vtxMapDataHandler.setInt(driverIndex)
                        vtxMapDataHandler.setClean()

                drivenVtxIter.next()
            drivenVtxIter.reset()

            vtxMappingArrayData.set(vtxMapOutArrayBuilder)


        elif transferType == 1:
            return


        setInitMode = om.MPlug(self.thisMObject(), self.initilizeData )
        setInitMode.setShort( 2 )

    def getMeshUVAtIndex(self, iter):

        uv_util = om.MScriptUtil()
        uv_ptr = uv_util.asFloat2Ptr()

        d_v_util = om.MScriptUtil()
        d_v_ptr = d_v_util.asFloatPtr()

        iter.getUV(uv_ptr)

        return uv_util.getFloat2ArrayItem(uv_ptr,0,0), uv_util.getFloat2ArrayItem(uv_ptr,0,1)


    @staticmethod
    def nodeCreator():
        return omMPx.asMPxPtr( TransferVertexDeformer() )

    @staticmethod
    def nodeInitializer():
        numericAttr =  om.MFnNumericAttribute ()
        polyMeshAttr = om.MFnTypedAttribute()
        enumAttr = om.MFnEnumAttribute()

        TransferVertexDeformer.inputMesh = polyMeshAttr.create( "inputMesh", "inMesh", om.MFnData.kMesh)
        polyMeshAttr.setStorable(False)
        polyMeshAttr.setConnectable(True)
        TransferVertexDeformer.addAttribute( TransferVertexDeformer.inputMesh )
        TransferVertexDeformer.attributeAffects( TransferVertexDeformer.inputMesh,
                                             omMPx.cvar.MPxGeometryFilter_outputGeom )


        TransferVertexDeformer.initilizeData = enumAttr.create( "initialize", "init" )
        enumAttr.addField(	"Off", 0)
        enumAttr.addField(	"Re-Set Bind", 1)
        enumAttr.addField(	"Bound", 2)
        enumAttr.setKeyable(True)
        enumAttr.setStorable(True)
        enumAttr.setReadable(True)
        enumAttr.setWritable(True)
        enumAttr.setDefault(0)

        TransferVertexDeformer.addAttribute(TransferVertexDeformer.initilizeData )
        TransferVertexDeformer.attributeAffects(TransferVertexDeformer.initilizeData,
                                                omMPx.cvar.MPxGeometryFilter_outputGeom )


        TransferVertexDeformer.transferType = enumAttr.create( "transferType", "trs" )
        enumAttr.addField(	"uv", 0)
        enumAttr.addField(	"worldSpace", 1)
        enumAttr.setKeyable(True)
        enumAttr.setStorable(True)
        enumAttr.setReadable(True)
        enumAttr.setWritable(True)
        enumAttr.setDefault(0)

        TransferVertexDeformer.addAttribute(TransferVertexDeformer.transferType )
        TransferVertexDeformer.attributeAffects(TransferVertexDeformer.transferType,
                                                omMPx.cvar.MPxGeometryFilter_outputGeom )


        TransferVertexDeformer.vertexMapping = numericAttr.create('vertexMapping','vtxMap', om.MFnNumericData.kInt)
        numericAttr.setKeyable(False)
        numericAttr.setArray(True)
        numericAttr.setStorable(True)
        numericAttr.setReadable(True)
        numericAttr.setWritable(True)
        TransferVertexDeformer.addAttribute(TransferVertexDeformer.vertexMapping)
        TransferVertexDeformer.attributeAffects(TransferVertexDeformer.vertexMapping,
                                                omMPx.cvar.MPxGeometryFilter_outputGeom  )

        #mc.makePaintable( kPluginNodeTypeName, 'weights', attrType='multiFloat' )
        om.MGlobal.executeCommand( "makePaintable -attrType multiFloat -sm deformer %s weights"%kPluginNodeTypeName )

def initializePlugin(mobject):
    mplugin = omMPx.MFnPlugin(mobject, "something", "1.0.1")

    try:
        mplugin.registerNode( kPluginNodeTypeName, transferVertexDeformerID, TransferVertexDeformer.nodeCreator,
                              TransferVertexDeformer.nodeInitializer, omMPx.MPxNode.kDeformerNode )
    except:
        sys.stderr.write( "Failed to register node: %s\n" % kPluginNodeTypeName )

# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = omMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( transferVertexDeformerID )
    except:
        sys.stderr.write( "Failed to unregister node: %s\n" % kPluginNodeTypeName )



"""
driver = 'pSphereShape2'
driven = 'pSphereShape1'

mSel = om.MSelectionList()
mSel.add(driver)
mSel.add(driven)


driverDag = mSel.getDagPath(0)
drivenDag = mSel.getDagPath(1)

driverMFnMesh = om.MFnMesh(driverDag)

drivenMFnMesh = om.MFnMesh(drivenDag)
drivenVtxMIt = om.MItMeshVertex(drivenDag)

driverUvs = driverMFnMesh.getUVs()
sortedDriverUvs = map(list, zip(driverUvs[0], driverUvs[1]))

transferSpace = om.MSpace.kObject

# mapped - driven - driver
mapped_vertices = []
while not drivenVtxMIt.isDone():
    if drivenVtxMIt.getUV() in sortedDriverUvs:

        driverIndex = sortedDriverUvs.index(drivenVtxMIt.getUV())
        drivenIndex = int(drivenVtxMIt.index())

        mapped_vertices.append([driverIndex, drivenIndex])

        driverId = sortedDriverUvs.index(drivenVtxMIt.getUV())

        pos = driverMFnMesh.getPoint(driverId, transferSpace)
        drivenVtxMIt.setPosition(pos)

    drivenVtxMIt.next()
"""
