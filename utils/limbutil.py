import maya.cmds as cmds

def placePoleVector(start, mid, end, ctl, multiplier=2.0):
    """ Place polevector control
    """

    apos = cmds.xform(start, q=True, t=True, ws=True)
    midpos = cmds.xform(mid, q=True, t=True, ws=True)
    bpos = cmds.xform(end, q=True, t=True, ws=True)

    # vector calculations
    vec = [a-b for a,b in zip(bpos, apos)]
    mid = [a+(b/2.0) for a,b in zip(apos, vec)]
    mvec = [a-b for a,b in zip(midpos, mid)]

    final = [a+(b*multiplier) for a,b in zip(mid, mvec)]

    cmds.xform(ctl, t=final, ws=True)



def elbowLock(polevector, posA, posB, startjnt, midjnt, name="elbowLock", gotStretch=True):
    """
        Creates a elbow lock setup
        :param polevector: polevector control
        :type polevector: str
        :param posA: transform to calculate start of chain
        :type posA: str
        :param posB: transform to calculate end of chain
        :type posB: str
        :param startjnt: startjoint
        :type startjnt: str
        :param midjnt: the joint in the middle of the chain
        :type midjnt: str
        :param gotStretch: if stretch is already implemented then consider it.
        :type gotStretch: bool
    """

    distanceA = cmds.createNode("distanceBetween", n="_{}_startToPV_DISTANCE".format(name))
    distanceB = cmds.createNode("distanceBetween", n="_{}_midToPV_DISTANCE".format(name))

    cmds.connectAttr(posA + ".worldMatrix", distanceA + ".inMatrix1")
    cmds.connectAttr(polevector + ".worldMatrix", distanceA + ".inMatrix2")

    cmds.connectAttr(posB + ".worldMatrix", distanceB + ".inMatrix1")
    cmds.connectAttr(polevector + ".worldMatrix", distanceB + ".inMatrix2")

    lenA = mjoint.getChainLength([startjnt, midjnt]) # start to mid
    lenB = mjoint.getChainLength([midjnt, posB]) # mid to end

    conditionA = cmds.createNode("condition", n="_{}_checkLengthA_COND".format(name))
    conditionB = cmds.createNode("condition", n="_{}_checkLengthB_COND".format(name))

    divA = cmds.createNode("multiplyDivide", n="_{}_getMultA_DIV".format(name))
    cmds.setAttr(divA + ".operation", 2)
    divB = cmds.createNode("multiplyDivide", n="_{}_getMultB_DIV".format(name))
    cmds.setAttr(divB + ".operation", 2)

    # set to 'if not equal'
    cmds.setAttr(conditionA + ".operation", 1)
    cmds.setAttr(conditionB + ".operation", 1)

    cmds.setAttr(conditionA + ".secondTerm", lenA)
    cmds.setAttr(conditionB + ".secondTerm", lenB)

    cmds.connectAttr(distanceA + ".distance",conditionA + ".firstTerm")
    cmds.connectAttr(distanceB + ".distance",conditionB + ".firstTerm")

    cmds.connectAttr(distanceA + ".distance",divA + ".input1X")
    cmds.connectAttr(distanceB + ".distance",divB + ".input1X")

    cmds.setAttr(divA + ".input2X", lenA)
    cmds.setAttr(divB + ".input2X", lenB)

    cmds.connectAttr(divA + ".outputX", conditionA + ".colorIfTrueR")
    cmds.connectAttr(divB + ".outputX", conditionB + ".colorIfTrueR")

    blender = cmds.createNode("blendColors", n="_{}_lock_BLENDER".format(name))

    cmds.addAttr(polevector, ln='lock', max=1.0, min=0.0, dv=0.0)
    cmds.setAttr(polevector + '.lock', cb=True)
    cmds.connectAttr(polevector + '.lock', blender + ".blender")

    cmds.setAttr(blender + ".color2", 1,1,1)
    cmds.connectAttr(conditionA + ".outColorR", blender + ".color1R")
    cmds.connectAttr(conditionB + ".outColorR", blender + ".color1G")

    if gotStretch:
        stretchOut = cmds.listConnections(startjnt + ".sx", p=True)[0]

        adlA = cmds.createNode("addDoubleLinear", n="_{}_addLockStretchA_ADL".format(name))
        adlMinA = cmds.createNode("addDoubleLinear", n="_{}_minusOneA_ADL".format(name))

        adlB = cmds.createNode("addDoubleLinear", n="_{}_addLockStretchB_ADL".format(name))
        adlMinB = cmds.createNode("addDoubleLinear", n="_{}_minusOneB_ADL".format(name))

        cmds.connectAttr(blender + ".outputR", adlA + ".input1" )
        cmds.connectAttr(stretchOut, adlA + ".input2" )

        cmds.connectAttr(blender + ".outputG", adlB + ".input1")
        cmds.connectAttr(stretchOut, adlB + ".input2" )

        cmds.connectAttr(adlA + ".output", adlMinA + ".input1")
        cmds.connectAttr(adlB + ".output", adlMinB + ".input1")

        cmds.setAttr(adlMinA + ".input2", -1)
        cmds.setAttr(adlMinB + ".input2", -1)

        cmds.connectAttr(adlMinA + ".output", startjnt + ".sx", f=True)
        cmds.connectAttr(adlMinB + ".output", midjnt + ".sx", f=True)

    else:
        cmds.connectAttr(blender + ".outputR", startjnt + ".sx")
        cmds.connectAttr(blender + ".outputG", midjnt + ".sx")

    return {"blender":blender}


def softIK(ctrlName, ikhName, stretch=True, upAxis=2, primaryAxis=1, name="softIK", switch=None):
    """ Creates a soft IK setup
        borrowed from nickmillergenuine, thanks!
        TODO: clean up code
        :param ctrlName: name of control
        :type ctrlName: str
        :param ikhName: name of ik handle
        :type ikhName: str
        :param stretch: add stretch
        :type stretch: bool
        :param upAxis: x:1, y:2, z:3
        :type upAxis: int
        :param primaryAxis: x:1, y:2, z:3
        :type primaryAxis: int
        :param name: name of setup
        :type name: str
    """

    #primary axis options
    if( primaryAxis == 1):
    	primaryAxis = 'X'
    if( primaryAxis == 2):
    	primaryAxis = 'Y'
    if( primaryAxis == 3):
    	primaryAxis = 'Z'

    #finds name for joints
    startJoint = cmds.listConnections( ikhName + ".startJoint" )
    endEffector = cmds.listConnections( ikhName + ".endEffector" )
    endJoint = cmds.listConnections( endEffector, d = False, s = True )

    #selects joint chain effected by IKH
    cmds.select( startJoint, hi = True )
    cmds.select( endJoint, hi = True, d = True )
    cmds.select( endEffector, d = True )
    cmds.select( endJoint, tgl = True )

    #lists the joints
    joints = []
    joints = cmds.ls( sl = True )
    n = len(joints)

    #gives position value for joints
    firstPos = cmds.xform( joints[0], q = True, piv = True, ws = True )
    lastPos = cmds.xform( joints[n - 1], q = True, piv = True, ws = True )
    fPoints  = firstPos[0:3]
    lPoints = lastPos[0:3]

    #up axis options
    if( upAxis == 1):
        upAxis = 'X'
        gPoint = ( 0, lPoints[1], lPoints[2] )
    if( upAxis == 2):
        upAxis = 'Y'
        gPoint = (lPoints[0], 0, lPoints[2])
    if( upAxis == 3):
        upAxis = 'Z'
        gPoint = ( lPoints[0], lPoints[1], 0)

    #find the dchain = sum of bone lengths
    i = 0
    dChain = 0
    while ( i < n - 1 ):
        a = cmds.xform( joints[i], q = True, piv = True, ws = True )
        b = cmds.xform( joints[ i + 1 ], q = True, piv = True, ws = True )
        x = b[0] - a[0]
        y = b[1] - a[1]
        z = b[2] - a[2]
        v = [x,y,z]
        dChain += mag(v)
        i += 1

    #get the distance from 0 to the ikh
    x = lPoints[0] - gPoint[0]
    y = lPoints[1] - gPoint[1]
    z = lPoints[2] - gPoint[2]
    v = [x,y,z]
    defPos = mag(v)
    if( ( upAxis == 'X' ) and ( lastPos[0] < 0 ) ):
        defPos = defPos * -1
    if( ( upAxis == 'Y' ) and ( lastPos[1] < 0 ) ):
        defPos = defPos * -1
    if( ( upAxis == 'Z' ) and ( lastPos[2] < 0 ) ):
        defPos = defPos * -1

    #create the distance node, otherwise know as x(distance between root and ik)
    cmds.spaceLocator( n = '%s_start_dist_loc' % name )
    cmds.xform( '%s_start_dist_loc' % name, t = fPoints, ws = True )
    cmds.spaceLocator( n = '%s_end_dist_loc' % name )
    cmds.xform( '%s_end_dist_loc' % name, t = lPoints, ws = True )


    mmatrix.constraint(ctrlName, '%s_end_dist_loc' % name,  mo = True, name=name + "EndDist_MTX")

    startDistShp = cmds.listRelatives('%s_start_dist_loc' % name, s=True)[0]
    endDistShp = cmds.listRelatives('%s_end_dist_loc' % name, s=True)[0]


    cmds.createNode( 'distanceBetween', n = '%s_x_distance' % name )
    cmds.connectAttr( startDistShp + ".worldPosition[0]", '%s_x_distance.point1' % name )
    cmds.connectAttr( endDistShp + ".worldPosition[0]", '%s_x_distance.point2' % name )


    cmds.addAttr( ctrlName, ln = 'dSoft', at = "double", min = 0.001, max = 2, dv = 0.001, k = True )

    #make softIK drive dSoft
    if switch:
        cmds.setDrivenKeyframe( '%s.dSoft' % ctrlName, currentDriver = '%s.softIK' % switch )
    else:
        if not cmds.attributeQuery("softIK", node=ctrlName, exists=True):
            cmds.addAttr( ctrlName, ln = 'softIK', at = "double", min = 0, max = 20, dv = 0, k = True )


        cmds.setDrivenKeyframe( '%s.dSoft' % ctrlName, currentDriver = '%s.softIK' % ctrlName )

    cmds.setAttr( '%s.softIK' % ctrlName, 20 )
    cmds.setAttr( '%s.dSoft' % ctrlName, 2 )

    if switch:
        cmds.setDrivenKeyframe( '%s.dSoft' % ctrlName, currentDriver = '%s.softIK' % switch)
    else:
        cmds.setDrivenKeyframe( '%s.dSoft' % ctrlName, currentDriver = '%s.softIK' % ctrlName)

    cmds.setAttr( '%s.softIK' % ctrlName, 0 )
    #lock and hide dSoft
    cmds.setAttr( '%s.dSoft' % ctrlName, lock = True, keyable = False, cb = False )


    cmds.createNode ('plusMinusAverage', n = '%s_da_cmdsa' % name )
    cmds.createNode ('plusMinusAverage', n = '%s_x_minus_da_cmdsa' % name )
    cmds.createNode ('multiplyDivide', n = '%s_negate_x_minus_md' % name )
    cmds.createNode ('multiplyDivide', n = '%s_divBy_dSoft_md' % name )
    cmds.createNode ('multiplyDivide', n = '%s_pow_e_md' % name )
    cmds.createNode ('plusMinusAverage', n = '%s_one_minus_pow_e_cmdsa' % name )
    cmds.createNode ('multiplyDivide', n = '%s_times_dSoft_md' % name )
    cmds.createNode ('plusMinusAverage', n = '%s_plus_da_cmdsa' % name )
    cmds.createNode ('condition', n = '%s_da_cond' % name )
    cmds.createNode ('plusMinusAverage', n = '%s_dist_diff_cmdsa' % name )
    cmds.createNode ('plusMinusAverage', n = '%s_defaultPos_cmdsa' % name )

    #set operations
    cmds.setAttr ('%s_da_cmdsa.operation' % name, 2 )
    cmds.setAttr ('%s_x_minus_da_cmdsa.operation' % name, 2 )
    cmds.setAttr ('%s_negate_x_minus_md.operation' % name, 1 )
    cmds.setAttr ('%s_divBy_dSoft_md.operation' % name, 2 )
    cmds.setAttr ('%s_pow_e_md.operation' % name, 3 )
    cmds.setAttr ('%s_one_minus_pow_e_cmdsa.operation' % name, 2 )
    cmds.setAttr ('%s_times_dSoft_md.operation' % name, 1 )
    cmds.setAttr ('%s_plus_da_cmdsa.operation' % name, 1 )
    cmds.setAttr ('%s_da_cond.operation' % name, 5 )
    cmds.setAttr ('%s_dist_diff_cmdsa.operation' % name, 2 )
    cmds.setAttr ('%s_defaultPos_cmdsa.operation' % name, 2 )
    if( ( upAxis == 'X' ) and ( defPos > 0 ) ):
        cmds.setAttr ('%s_defaultPos_cmdsa.operation' % name, 1 )
    if( upAxis == 'Y'):
        cmds.setAttr ('%s_defaultPos_cmdsa.operation' % name, 2 )
    if( ( upAxis == 'Z' ) and ( defPos < 0 ) ):
        cmds.setAttr ('%s_defaultPos_cmdsa.operation' % name, 1 )


    cmds.setAttr( '%s_da_cmdsa.input1D[0]' % name, dChain )
    cmds.connectAttr( '%s.dSoft' % ctrlName, '%s_da_cmdsa.input1D[1]' % name )

    cmds.connectAttr( '%s_x_distance.distance' % name, '%s_x_minus_da_cmdsa.input1D[0]' % name )
    cmds.connectAttr( '%s_da_cmdsa.output1D' % name, '%s_x_minus_da_cmdsa.input1D[1]' % name )

    cmds.connectAttr( '%s_x_minus_da_cmdsa.output1D' % name, '%s_negate_x_minus_md.input1X' % name )
    cmds.setAttr( '%s_negate_x_minus_md.input2X' % name, -1 )

    cmds.connectAttr( '%s_negate_x_minus_md.outputX' % name, '%s_divBy_dSoft_md.input1X' % name )
    cmds.connectAttr( '%s.dSoft' % ctrlName, '%s_divBy_dSoft_md.input2X' % name )

    cmds.setAttr( '%s_pow_e_md.input1X' % name, 2.718281828 )
    cmds.connectAttr( '%s_divBy_dSoft_md.outputX' % name, '%s_pow_e_md.input2X' % name )

    cmds.setAttr( '%s_one_minus_pow_e_cmdsa.input1D[0]' % name, 1 )
    cmds.connectAttr( '%s_pow_e_md.outputX' % name, '%s_one_minus_pow_e_cmdsa.input1D[1]' % name )

    cmds.connectAttr('%s_one_minus_pow_e_cmdsa.output1D' % name, '%s_times_dSoft_md.input1X' % name )
    cmds.connectAttr( '%s.dSoft' % ctrlName, '%s_times_dSoft_md.input2X' % name )

    cmds.connectAttr( '%s_times_dSoft_md.outputX' % name, '%s_plus_da_cmdsa.input1D[0]' % name )
    cmds.connectAttr( '%s_da_cmdsa.output1D' % name, '%s_plus_da_cmdsa.input1D[1]' % name )

    cmds.connectAttr( '%s_da_cmdsa.output1D' % name, '%s_da_cond.firstTerm' % name )
    cmds.connectAttr( '%s_x_distance.distance' % name, '%s_da_cond.secondTerm' % name )
    cmds.connectAttr( '%s_x_distance.distance' % name, '%s_da_cond.colorIfFalseR' % name )
    cmds.connectAttr( '%s_plus_da_cmdsa.output1D' % name, '%s_da_cond.colorIfTrueR' % name )

    cmds.connectAttr( '%s_da_cond.outColorR' % name, '%s_dist_diff_cmdsa.input1D[0]' % name )
    cmds.connectAttr( '%s_x_distance.distance' % name, '%s_dist_diff_cmdsa.input1D[1]' % name )

    cmds.setAttr( '%s_defaultPos_cmdsa.input1D[0]' % name, defPos )
    cmds.connectAttr( '%s_dist_diff_cmdsa.output1D' % name, '%s_defaultPos_cmdsa.input1D[1]' % name )

    #cmds.connectAttr('%s_defaultPos_cmdsa.output1D' % name, '%s.translate%s' % (ikhName, upAxis) )


    if(stretch):


        cmds.createNode ('multiplyDivide', n = '%s_soft_ratio_md' % name )
        cmds.createNode ('blendColors', n = '%s_stretch_blend' % name )
        cmds.createNode ('multDoubleLinear', n = '%s_stretch_switch_mdl' % name )

        cmds.setAttr ('%s_soft_ratio_md.operation' % name, 2 )
        cmds.setAttr ('%s_stretch_blend.color2R' % name, 1 )
        cmds.setAttr ('%s_stretch_blend.color1G' % name, defPos )
        cmds.setAttr ('%s_stretch_switch_mdl.input2' % name, 0.1 )

        if switch:
            cmds.connectAttr ( '%s.stretchSwitch' % switch, '%s_stretch_switch_mdl.input1' % name )
        else:
            #add attribute to switch between stretchy and non-stretchy
            if not cmds.attributeQuery("stretchSwitch", node=ctrlName, exists=True):
                cmds.addAttr( ctrlName, ln = 'stretchSwitch', at = "double", min = 0, max = 10, dv = 10, k = True )

            cmds.connectAttr ( '%s.stretchSwitch' % ctrlName, '%s_stretch_switch_mdl.input1' % name )

        cmds.connectAttr ( '%s_stretch_switch_mdl.output' % name, '%s_stretch_blend.blender' % name )
        cmds.connectAttr( '%s_x_distance.distance' % name, '%s_soft_ratio_md.input1X' % name )
        cmds.connectAttr( '%s_da_cond.outColorR' % name, '%s_soft_ratio_md.input2X' % name )
        cmds.connectAttr( '%s_defaultPos_cmdsa.output1D' % name, '%s_stretch_blend.color2G' % name )
        cmds.connectAttr( '%s_soft_ratio_md.outputX' % name, '%s_stretch_blend.color1R' % name )

        #cmds.connectAttr('%s_stretch_blend.outputG' % name, '%s.translate%s' % (ikhName, upAxis), force = True )

        i = 0
        while ( i < n - 1 ):
            cmds.connectAttr( '%s_stretch_blend.outputR' % name, '%s.scale%s' % (joints[i], primaryAxis), force = True )
            i += 1


    return {"startLoc":'%s_start_dist_loc' % name,
            "endLoc":'%s_end_dist_loc' % name}


def mag( v ):
    return( math.sqrt( pow( v[0], 2) + pow( v[1], 2) + pow( v[2], 2)))



def streatchyIK(chain, transformA, transformB, name="Streatchy"):
    """ creates a streatchy setup
        :param chain: joint chain that is going to streatch
        :type chain: list
        :param transformA: distance pos A
        :type transformA: transform
        :param transformB: distance pos B
        :type transformB: transform
        :param name: setup name
        :type name: str
    """
    #TODO: add a main scaler multiply

    length = mjoint.getChainLength(chain)

    # create Nodes
    distance = cmds.createNode("distanceBetween", n="_{}_DISTANCE".format(name))

    blender = cmds.createNode("blendTwoAttr", n="_{}_BLENDER".format(name))
    cond = cmds.createNode("condition", n="_{}_IFstreatching".format(name))
    cmds.setAttr(cond + ".operation", 2)

    div = cmds.createNode("multiplyDivide", n="_{}_DIV".format(name))
    cmds.setAttr(div + ".operation", 2)

    # calculate distance
    cmds.connectAttr(transformA + ".worldMatrix[0]",distance + ".inMatrix1")
    cmds.connectAttr(transformB + ".worldMatrix[0]",distance + ".inMatrix2")

    # setup condition if we are streatching or not..
    cmds.connectAttr(distance + ".distance",cond + ".firstTerm")
    cmds.setAttr(cond + ".secondTerm", length)

    cmds.connectAttr(distance + ".distance", div + ".input1X")
    cmds.setAttr(div + ".input2X", length)

    cmds.connectAttr(div + ".outputX", cond + ".colorIfTrueR")

    cmds.setAttr(blender + ".input[0]", 1)
    cmds.connectAttr(cond + ".outColorR", blender + ".input[1]")

    for jnt in chain:
        cmds.connectAttr(blender + ".output", jnt + ".sx")

    cmds.setAttr(blender + ".attributesBlender", 1.0)

    return {"blender":blender + ".attributesBlender", "con":cond,
            "distance":distance}


def ikfk(chain, pvctl=None, name="ikfk", softik=True, elbowlock=True):

    maingrp = cmds.group(em=True, n="{}Setup_GRP".format(name))
    driven_grp = cmds.group(em=True, n="{}Driven_GRP".format(name))
    fk_grp = cmds.group(em=True, n="{}FK_GRP".format(name))
    ik_grp = cmds.group(em=True, n="{}IK_GRP".format(name))

    cmds.setAttr(ik_grp + ".v", 0)
    cmds.setAttr(fk_grp + ".v", 0)

    cmds.parent([driven_grp, fk_grp, ik_grp], maingrp)

    alpha = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    parents = None
    wtmats = []
    ik_joints = []
    fk_transforms=[]
    out_transforms = []
    for i, transform in enumerate(chain):
        cmds.select(clear=True)
        ik_jnt = cmds.joint(n="{}IK{}_DRIVER".format(name, alpha[i]))
        fk_t = cmds.group(em=True, n="{}FK{}_DRIVER".format(name, alpha[i]))
        driv_grp = cmds.group(em=True, n="{}{}_DRIVEN".format(name, alpha[i]))
        out_t = cmds.group(em=True, n="{}Driven{}_OUT".format(name, alpha[i]))

        cmds.parent(out_t, driv_grp)
        cmds.parent(fk_t, fk_grp)
        cmds.parent(ik_jnt, ik_grp)
        cmds.parent(driv_grp, driven_grp)

        if parents:
            cmds.parent(ik_jnt, parents[0])
            cmds.parent(fk_t, parents[1])

        parents = [ik_jnt, fk_t]

        cmds.delete(cmds.parentConstraint(transform, ik_jnt, mo=False))
        cmds.delete(cmds.parentConstraint(transform, fk_t, mo=False))
        cmds.delete(cmds.parentConstraint(transform, driv_grp, mo=False))
        cmds.makeIdentity(ik_jnt, a=True)

        decomp, wtMat = mmatrix.constraint(ik_jnt, fk_t, driv_grp, mo=True, name=name + "_MTX")

        wtmats.append(wtMat)
        ik_joints.append(ik_jnt)
        out_transforms.append(out_t)
        fk_transforms.append(fk_t)

    ikhandle = cmds.ikHandle(sj=ik_joints[0], ee=ik_joints[len(ik_joints)-1], n=name + "_IKHandle")
    buff = cmds.group(em=True, n=name + "IkHandle_BUFF")

    cmds.delete(cmds.parentConstraint(chain[len(chain)-1], buff, mo=False))

    cmds.setAttr(ikhandle[0] +".v", 0)
    cmds.parent(ikhandle[0], buff)
    cmds.parent(buff, maingrp)

    cmds.addAttr(maingrp, ln="IkFkBlend", k=True, max=1.0, min=0.0)
    rev = cmds.createNode("reverse", n="{}Blend_REV".format(name))

    cmds.connectAttr(maingrp + ".IkFkBlend", rev + ".inputX")

    for wtmat in wtmats:
        cmds.connectAttr(rev + ".outputX", wtmat  + ".wtMatrix[0].weightIn")
        cmds.connectAttr(maingrp + ".IkFkBlend", wtmat +".wtMatrix[1].weightIn")

    dist_grp = None
    if softik:
        dist_grp = cmds.group(em=True, n=name + "ikSoftIkDist_GRP")
        cmds.delete(cmds.parentConstraint(buff, dist_grp, mo=False))
        cmds.parent(dist_grp, buff)
        softIkData = softIK(dist_grp, ikhandle[0], stretch=True, upAxis=2, primaryAxis=1, name=name+"SoftIK", switch=None)
        cmds.parent([softIkData["startLoc"], softIkData["endLoc"]], maingrp)

        cmds.setAttr(softIkData["startLoc"] + ".v", 0)
        cmds.setAttr(softIkData["endLoc"] + ".v", 0)

        if elbowlock and pvctl:
            elbowLock(pvctl, softIkData["startLoc"], softIkData["endLoc"], ik_joints[0], ik_joints[1], name=name+"ElbowLock")

    for node in [driven_grp, fk_grp, ik_grp]:
        for attr in ["scale", "rotate", "translate"]:
            cmds.setAttr("{}.{}".format(node, attr), l=True, k=False)

    return {"maingrp":maingrp, "outs":out_transforms, "blendrev":rev + ".outputX", "blend":maingrp + ".IkFkBlend",
            "ikChain":ik_joints, "ikhandle":ikhandle[0], "fks":fk_transforms, "attrgrp":dist_grp}
