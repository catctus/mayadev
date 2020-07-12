import math, sys
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx

import numpy as np
from scipy.interpolate import Rbf


# name of deformer
kPluginNodeTypeName = "rbfWrapDeformer"

#id
rbfWrapDeformerID = OpenMaya.MTypeId(0x1002)

class rbfWrapDeformer(OpenMayaMPx.MPxDeformerNode):
    # the driver mesh
    driver_mesh = OpenMaya.MObject()

    # let's us rebind the mesh
    initialized_data = OpenMaya.MObject()

    # store deltas
    deltaData = OpenMaya.MObject()
    #deltaList = OpenMaya.MObject()
    bindData = OpenMaya.MObject()
    #bindList = OpenMaya.MObject()

    def __init__(self):
        OpenMayaMPx.MPxDeformerNode.__init__(self)

    def deform( self, data, iter, localToWorldMatrix, mIndex ):
        # init origin
        initialized_mapping = data.inputValue( self.initialized_data ).asShort();
        if( initialized_mapping == 1 ):
            self.initOrigin(data, iter, localToWorldMatrix, mIndex)
            initialized_mapping = data.inputValue( self.initialized_data ).asShort()


        # intilized data and we are good to goo
        if( initialized_mapping == 2 ):
            # get data from data block:
            envelope = OpenMayaMPx.cvar.MPxGeometryFilter_envelope
            envelopeHandle = data.inputValue( envelope )
            env = envelopeHandle.asFloat()

            # get delta and bind data
            deltaArrayData  = data.inputArrayValue( self.deltaData )
            bindArrayData  = data.inputArrayValue( self.bindData )

            # get the driver mesh
            meshAttrHandle = data.inputValue( self.driver_mesh )

            meshMobj = meshAttrHandle.asMesh()
            meshVerItFn = OpenMaya.MItMeshVertex( meshMobj )

            deform_points = []
            bind_points = []
            while not meshVerItFn.isDone():
                wsPoint = meshVerItFn.position(OpenMaya.MSpace.kWorld)
                deform_points.append(np.array([wsPoint.x, wsPoint.y, wsPoint.z]))

                bindArrayData.jumpToElement( meshVerItFn.index() )
                origin_pos = bindArrayData.inputValue().asFloat3()
                bind_points.append(np.array([origin_pos[0], origin_pos[1], origin_pos[2]]))

                meshVerItFn.next()

            meshVerItFn.reset()

            deform_points_m = np.array(deform_points)
            bind_points_m = np.array(bind_points)

            # shuffle array
            inputdata = []
            for value_A in deform_points_m.T:
                sort_array = []
                for value_B in bind_points_m.T:
                    sort_array.append(value_B)
                sort_array.append(value_A)
                inputdata.append(np.array([sort_array]))

            # calculate RBFs
            rbfs = [Rbf(value[0][0], value[0][1],value[0][2], value[0][3]) for value in inputdata]

            i = 0
            while not iter.isDone():
                weight = self.weightValue( data, mIndex, iter.index() )

                iterPt = iter.position() * localToWorldMatrix
                target = np.array([iterPt.x, iterPt.y, iterPt.z])
                output = [rbf(*target) for rbf in rbfs]

                deltaArrayData.jumpToElement( i )
                delta = deltaArrayData.inputValue().asFloat3()

                pos = target + (output - (np.array([delta[0], delta[1], delta[2]])) - target)

                iter.setPosition(OpenMaya.MPoint(pos[0], pos[1], pos[2]))

                iter.next()

            iter.reset()




    def initOrigin(self, data, iter, localToWorldMatrix, mIndex):
        # get the handle for the driver mesh
        meshAttrHandle = data.inputValue( self.driver_mesh  )

        # get mfnmesh
        meshMobj = meshAttrHandle.asMesh()

        meshVerItFn = OpenMaya.MItMeshVertex( meshMobj )
        meshVerItFn.reset()


        bind_count = meshVerItFn.count()
        bindOutArrayData = data.outputArrayValue( self.bindData )
        bindOutArrayBuilder = OpenMaya.MArrayDataBuilder( self.bindData, bind_count )

        # get the origin points
        origin_points = []
        i = 0
        while not meshVerItFn.isDone():
            wsPoint = meshVerItFn.position(OpenMaya.MSpace.kWorld)# * localToWorldMatrix #
            origin_points.append(np.array([wsPoint.x, wsPoint.y, wsPoint.z]))

            bindDataHnd = bindOutArrayBuilder.addElement(i)
            bindDataHnd.set3Float(wsPoint.x, wsPoint.y, wsPoint.z)
            bindDataHnd.setClean()

            i += 1
            meshVerItFn.next()

        bindOutArrayData.set(bindOutArrayBuilder)

        origin_m = np.array(origin_points)

        # shuffle array
        inputdata = []
        for value_A in origin_m.T:
            sort_array = []
            for value_B in origin_m.T:
                sort_array.append(value_B)
            sort_array.append(value_A)
            inputdata.append(np.array([sort_array]))

        # create rbfs
        rbfs = [Rbf(value[0][0], value[0][1],value[0][2], value[0][3]) for value in inputdata]

        # get target points
        target_points = []
        while not iter.isDone():
            wsPoint = iter.position() * localToWorldMatrix #localToWorldMatrix
            target_points.append(np.array([wsPoint.x, wsPoint.y, wsPoint.z]))
            iter.next()

        target_m = np.array(target_points)


        delta_count = iter.count()
        deltaOutArrayData = data.outputArrayValue( self.deltaData )
        deltaOutArrayBuilder = OpenMaya.MArrayDataBuilder( self.deltaData, delta_count )

        for i, target in enumerate(target_m):
            output = [rbf(*target) for rbf in rbfs]
            delta =  np.round((output - target), 4)

            deltaDataHnd = deltaOutArrayBuilder.addElement(i)
            deltaDataHnd.set3Float(float(delta[0]), float(delta[1]), float(delta[2]))
            deltaDataHnd.setClean()

        deltaOutArrayData.set(deltaOutArrayBuilder)

        tObj  =  self.thisMObject()
        setInitMode = OpenMaya.MPlug( tObj, self.initialized_data  )
        setInitMode.setShort( 2 )

        iter.reset()

def nodeCreator():
    return OpenMayaMPx.asMPxPtr( rbfWrapDeformer() )

def nodeInitializer():

    polyMeshAttr = OpenMaya.MFnTypedAttribute()
    enumAttr = OpenMaya.MFnEnumAttribute()
    nAttr = OpenMaya.MFnNumericAttribute ()

    rbfWrapDeformer.driver_mesh = polyMeshAttr.create( "driverInput", "dinput", OpenMaya.MFnData.kMesh )
    polyMeshAttr.setStorable(False)
    polyMeshAttr.setConnectable(True)
    rbfWrapDeformer.addAttribute( rbfWrapDeformer.driver_mesh )
    rbfWrapDeformer.attributeAffects( rbfWrapDeformer.driver_mesh, OpenMayaMPx.cvar.MPxGeometryFilter_outputGeom )

    rbfWrapDeformer.initialized_data = enumAttr.create( "initialize", "ini" )
    enumAttr.addField(	"Off", 0)
    enumAttr.addField(	"Re-Set Bind", 1)
    enumAttr.addField(	"Bound", 2)
    enumAttr.setKeyable(True)
    enumAttr.setStorable(True)
    enumAttr.setReadable(True)
    enumAttr.setWritable(True)
    enumAttr.setDefault(0)
    rbfWrapDeformer.addAttribute( rbfWrapDeformer.initialized_data )
    rbfWrapDeformer.attributeAffects( rbfWrapDeformer.initialized_data, OpenMayaMPx.cvar.MPxGeometryFilter_outputGeom )

    # deltas
    rbfWrapDeformer.deltaData = nAttr.createPoint('deltaData','dData')
    nAttr.setKeyable(False)
    nAttr.setArray(True)
    nAttr.setStorable(True)
    nAttr.setReadable(True)
    nAttr.setWritable(True)
    rbfWrapDeformer.addAttribute( rbfWrapDeformer.deltaData)
    rbfWrapDeformer.attributeAffects( rbfWrapDeformer.deltaData, OpenMayaMPx.cvar.MPxGeometryFilter_outputGeom  )

    # bind
    rbfWrapDeformer.bindData = nAttr.createPoint('bindData','bdata')
    nAttr.setKeyable(False)
    nAttr.setArray(True)
    nAttr.setStorable(True)
    nAttr.setReadable(True)
    nAttr.setWritable(True)
    rbfWrapDeformer.addAttribute( rbfWrapDeformer.bindData)
    rbfWrapDeformer.attributeAffects( rbfWrapDeformer.bindData, OpenMayaMPx.cvar.MPxGeometryFilter_outputGeom  )

    # make weights paintable
    cmds.makePaintable( kPluginNodeTypeName, 'weights', attrType='multiFloat' )

def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject, "RBF wrap test", "1.0.1")
    try:
        mplugin.registerNode( kPluginNodeTypeName, rbfWrapDeformerID, nodeCreator, nodeInitializer, OpenMayaMPx.MPxNode.kDeformerNode )
    except:
        sys.stderr.write( "Failed to register node: %s\n" % kPluginNodeTypeName )

# uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( rbfWrapDeformerID )
    except:
        sys.stderr.write( "Failed to unregister node: %s\n" % kPluginNodeTypeName )
