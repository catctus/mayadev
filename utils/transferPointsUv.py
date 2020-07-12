import maya.api.OpenMaya as om

driver = 'pSphereShape2'
driven = 'pSphereShape1'

mSel = om.MSelectionList()
mSel.add(driver)
mSel.add(driven)


driverDag = mSel.getDagPath(0)
drivenDag = mSel.getDagPath(1)

driverMFnMesh = om.MFnMesh(driverDag)
driverVtxMIt = om.MItMeshVertex(driverDag)

drivenMFnMesh = om.MFnMesh(drivenDag)
drivenVtxMIt = om.MItMeshVertex(drivenDag)

driverUvs = driverMFnMesh.getUVs()
sortedDriverUvs = map(list, zip(driverUvs[0], driverUvs[1]))

transferSpace = om.MSpace.kObject

# mapped - driven - driver
mapped_vertices = []
while not drivenVtxMIt.isDone():
    if drivenVtxMIt.getUV() in sortedDriverUvs:

        while not driverVtxMIt.isDone():

            if drivenVtxMIt.getUV() == driverVtxMIt.getUV():
                drivenIndex = int(drivenVtxMIt.index())
                driverIndex = int(driverVtxMIt.index())
                mapped_vertices.append([driverIndex, drivenIndex])

                pos = driverVtxMIt.position(om.MSpace.kWorld)
                drivenVtxMIt.setPosition(pos, om.MSpace.kWorld)

            driverVtxMIt.next()

        driverVtxMIt.reset()

    drivenVtxMIt.next()
