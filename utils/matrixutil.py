import maya.cmds as cmds
import maya.api.OpenMaya as om

def getLocalRotationHoldMatrix(wsTransform, wsInvTransform, name):
    """Creates a holdMatrix node, and sets the local rotateMatrix
    returns holdMatrix node
    """
    holdmat = cmds.createNode('holdMatrix', n='_%s_HMAT'%name)

    MList = om.MSelectionList()
    MList.add(wsTransform)

    mplug = om.MFnDependencyNode(MList.getDependNode(0)).findPlug('worldMatrix', 0)
    mat = om.MFnMatrixData(mplug.elementByLogicalIndex( 0 ).asMObject()).matrix()

    if wsInvTransform:
        MList.add(wsInvTransform)

        mplug = om.MFnDependencyNode(MList.getDependNode(1)).findPlug('worldInverseMatrix', 0)
        invmat = om.MFnMatrixData(mplug.elementByLogicalIndex( 0 ).asMObject()).matrix()

        mtmat = om.MTransformationMatrix(mat * invmat)

        cmds.setAttr(holdmat + '.inMatrix', mtmat.asRotateMatrix(), type='matrix')

    else:
        mtmat = om.MTransformationMatrix(mat)
        cmds.setAttr(holdmat + '.inMatrix', mtmat.asRotateMatrix(), type='matrix')

    return holdmat
