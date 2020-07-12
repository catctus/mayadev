"""
This module contains methods to create different type of matrix constraints
Some can be faster/more light weight then mayas built in constraints.
almost all of the constraints have a prevent beigncycle argument,
This will connect the parents worldmatrix instead of the
parentInverseMatrix attribute of the input node and skip the beign cycle.
"""
import pymel.core as pm


def aimConstraint(driver, driven, **kwargs):
	""" Craetes a aim constraint with maya matrix nodes
	"""

	# grab keyword arguments
	name = kwargs.get('n', kwargs.get('name', 'constraint_mtx'))
	mo = kwargs.get('mo', kwargs.get('maintanoffset', True))
	upObject = kwargs.get('upObject', kwargs.get('uo', None))
	upVector = kwargs.get('upVector', kwargs.get('uvec', [0,1,0]))
	beigncycle = kwargs.get('beigncycle', kwargs.get('bc', False))
	negaim = kwargs.get('negativeAim', kwargs.get('neg', False))

	invParMult = pm.createNode("multMatrix", n='_%sInv_mtx'%name)
	decomposeMat = pm.createNode("decomposeMatrix", n='_%s_DcmpMtx'%name)

	# prevent begin cycle or create it
	if beigncycle:
		pm.connectAttr("%s.parentInverseMatrix"%driven,
						 "%s.matrixIn[1]"%invParMult)
	else:
		parent = pm.listRelatives(driven, p=True)

		if parent:
			pm.connectAttr("%s.worldInverseMatrix"%parent[0],
							 "%s.matrixIn[1]"%invParMult)
		else: pm.delete(invParMult)

	pnt = pm.spaceLocator(n= '_' + name + 'AimVector_POINT')
	pm.delete(pm.parentConstraint(driven, pnt, mo=False))
	pm.parent(pnt, driven)

	pm.setAttr(pnt + '.v', 0)
	for attr in ['.tx', '.ty', '.tz',
				'.rx', '.ry', '.rz',
				'.sx', '.sy', '.sz',
				'.v']:
		pm.setAttr(pnt + attr, l=True, k=False)
		pm.setAttr(pnt + attr, cb=False)

	# create nodes
	aim_mtx = pm.createNode('fourByFourMatrix', n='_%sAim_MTX'%(name))
	aimVector = pm.createNode('plusMinusAverage', n='_%sUpVector_PMA'%(name))
	crsPrd = pm.createNode('vectorProduct', n='_%sCrossProduct_VP'%(name))
	decomp = pm.createNode('decomposeMatrix', n='_%sAimOut_DMtx'%(name))
	getWs = pm.createNode('decomposeMatrix', n='_%sGetWSPosition_DMtx'%(name))

	# create aim vector
	pm.setAttr(aimVector + '.operation', 2)
	pm.connectAttr(driver + '.worldMatrix[0]', getWs + '.inputMatrix')

	pos = [0, 1]
	if negaim: pos = [1, 0]

	pm.connectAttr(getWs + '.outputTranslate', aimVector + '.input3D[%d]'%pos[0])
	pm.connectAttr(pm.listRelatives(pnt, s=True)[0] + '.worldPosition[0]',
					 aimVector + '.input3D[%d]'%pos[1])

	pm.connectAttr(aimVector + ".output3D.output3Dx", aim_mtx + ".in00")
	pm.connectAttr(aimVector + ".output3D.output3Dy", aim_mtx + ".in01")
	pm.connectAttr(aimVector + ".output3D.output3Dz", aim_mtx + ".in02")

	if not upObject:

		pm.setAttr(aim_mtx + ".in10", upVector[0])
		pm.setAttr(aim_mtx + ".in11", upVector[1])
		pm.setAttr(aim_mtx + ".in12", upVector[2])

		pm.setAttr(crsPrd + '.operation', 2)
		pm.connectAttr(aimVector + '.output3D', crsPrd + '.input1')

		pm.setAttr(crsPrd + ".input2.input2X", upVector[0])
		pm.setAttr(crsPrd + ".input2.input2Y", upVector[1])
		pm.setAttr(crsPrd + ".input2.input2Z", upVector[2])

	pm.connectAttr(crsPrd + '.output.outputX', aim_mtx + ".in20")
	pm.connectAttr(crsPrd + '.output.outputY', aim_mtx + ".in21")
	pm.connectAttr(crsPrd + '.output.outputZ', aim_mtx + ".in22")

	pm.connectAttr(getWs + '.outputTranslateX', aim_mtx + ".in30")
	pm.connectAttr(getWs + '.outputTranslateY', aim_mtx + ".in31")
	pm.connectAttr(getWs + '.outputTranslateZ', aim_mtx + ".in32")


	if mo:
		mult = pm.createNode("multMatrix", n='_%sDriverMO_mtx'%(name))
		inv = pm.createNode('inverseMatrix', n='_%sDriverINV_TMP'%(name))
		pm.connectAttr( aim_mtx + '.output', inv + '.inputMatrix')

		drivenWsMtx = pm.getAttr(driven + '.worldMatrix')
		driverInvsWsMtx = pm.getAttr(inv + '.outputMatrix')

		pm.setAttr(mult + '.matrixIn[0]', drivenWsMtx * driverInvsWsMtx)
		pm.connectAttr(aim_mtx + '.output', mult + '.matrixIn[1]')

		pm.delete(inv)

		if invParMult:
			pm.connectAttr(mult + '.matrixSum', invParMult + '.matrixIn[0]')
			pm.connectAttr(invParMult + '.matrixSum', decomposeMat + '.inputMatrix')
		else:
			pm.connectAttr(mult + '.matrixSum', decomposeMat + '.inputMatrix')
	else:
		if invParMult:
			pm.connectAttr(aim_mtx + '.output', invParMult + '.matrixIn[0]')
			pm.connectAttr(invParMult + '.matrixSum', decomposeMat + '.inputMatrix')
		else:
			pm.connectAttr(aim_mtx + '.output', decomposeMat + '.inputMatrix')

	pm.connectAttr('%s.outputRotate'%decomposeMat, '%s.rotate'%driven)



def constraint(*args, **kwargs):
	""" Creates a matrix constraint, if more then one driver are passed
		this setup will create a weight matrix node.
		Args: drivers, driven
		kwargs:
			n - name : name of setup
			mo - maintanoffset : maintans offset
			nt - notranslate : no translate (rotate only)
			nr - norotate : no rotate (translate only)
			beigncycle - bc : if false, prevents beign cycle
	"""

	# grab keyword arguments
	name = kwargs.get('n', kwargs.get('name', 'constraint_mtx'))
	mo = kwargs.get('mo', kwargs.get('maintanoffset', True))
	nt = kwargs.get('nt', kwargs.get('notranslate', False))
	nr = kwargs.get('nr', kwargs.get('norotate', False))
	beigncycle = kwargs.get('beigncycle', kwargs.get('bc', False))

	driven = args[-1:][0]
	drivers = args[:-1]

	invParMult = pm.createNode("multMatrix", n='_%sInv_mtx'%name)
	decomposeMat = pm.createNode("decomposeMatrix", n='_%s_DcmpMtx'%name)

	# set the rotate order
	rotateOrder = pm.getAttr(driven + '.rotateOrder')
	pm.setAttr(decomposeMat + '.inputRotateOrder', rotateOrder)

	# prevent begin cycle or create it
	if beigncycle:
		pm.connectAttr("%s.parentInverseMatrix"%driven,
						 "%s.matrixIn[1]"%invParMult)
	else:
		parent = pm.listRelatives(driven, p=True)

		if parent:
			pm.connectAttr("%s.worldInverseMatrix"%parent[0],
							 "%s.matrixIn[1]"%invParMult)
		else: pm.delete(invParMult)

	# setup maintain offset
	if mo:
		mult_objs = []
		for driver in drivers:
			mult = pm.createNode("multMatrix", n='_%s_%sMO_mtx'%(name, driver.title()))
			mult_objs.append(mult)

			drivenWsMtx = pm.getAttr(driven + '.worldMatrix')
			driverInvsWsMtx = pm.getAttr(driver + '.worldInverseMatrix')

			pm.setAttr(mult + '.matrixIn[0]', drivenWsMtx * driverInvsWsMtx)
			pm.connectAttr(driver + '.worldMatrix', mult + '.matrixIn[1]')

	# if we have multiple drivers, create a wtAddMatrix and to weight them
	wtMat = None
	if len(drivers) > 1:
		wtMat = pm.createNode('wtAddMatrix', n='_%s_WtMtx'%name)

		weight = 1.0/(len(drivers))
		# connect drivers to weight matrix
		for i, driver in enumerate(drivers):
			if mo:
				mult = mult_objs[i]
				pm.connectAttr('%s.matrixSum'%mult,
							   '%s.wtMatrix[%d].matrixIn'%(wtMat, i))
			else:
				pm.connectAttr('%s.worldMatrix'%driver,
							   '%s.wtMatrix[%d].matrixIn'%(wtMat, i))

			pm.setAttr('%s.wtMatrix[%d].weightIn'%(wtMat, i), weight)

		if invParMult:
			pm.connectAttr('%s.matrixSum'%wtMat, '%s.matrixIn[0]'%invParMult)
			pm.connectAttr('%s.matrixSum'%invParMult, '%s.inputMatrix'%decomposeMat)
		else:
			pm.connectAttr('%s.matrixSum'%wtMat, '%s.inputMatrix'%decomposeMat)
	else:
		if invParMult:
			if mo:
				pm.connectAttr('%s.matrixSum'%mult_objs[0],
								  '%s.matrixIn[0]'%invParMult)
			else:
				pm.connectAttr('%s.worldMatrix[0]'%drivers[0], '%s.matrixIn[0]'%invParMult)

			pm.connectAttr('%s.matrixSum'%invParMult, '%s.inputMatrix'%decomposeMat)
		else:
			if mo:
				pm.connectAttr('%s.matrixSum'%mult_objs[0], '%s.inputMatrix'%decomposeMat)
			else:
				pm.connectAttr('%s.worldMatrix'%drivers[0], '%s.inputMatrix'%decomposeMat)

	# if not no translate
	if not nr:
		pm.connectAttr('%s.outputRotate'%decomposeMat, '%s.rotate'%driven)
	# not no rotate
	if not nt:
		pm.connectAttr('%s.outputTranslate'%decomposeMat, '%s.translate'%driven)


	return decomposeMat, wtMat


def jointConstraint(tf, jnt, name="jntconstriant"):
	""" constraint transform to joint preserve joint orients """

	t_mat = pm.createNode("multMatrix", n=name + "Trans_MAT")
	r_mat = pm.createNode("multMatrix", n=name + "Rot_MAT")
	t_dmat = pm.createNode("decomposeMatrix", n=name + "Trans_DMAT")
	r_dmat = pm.createNode("decomposeMatrix", n=name + "Rot_DMAT")
	inv_mat = pm.createNode("inverseMatrix", n=name + "InvMat_TMP")

	rotateOrder = pm.getAttr(tf + '.rotateOrder')
	pm.setAttr(t_dmat + '.inputRotateOrder', rotateOrder)
	pm.setAttr(r_dmat + '.inputRotateOrder', rotateOrder)

	tf = pm.PyNode(tf)
	jnt = pm.PyNode(jnt)

	tf.worldMatrix[0] >> t_mat.matrixIn[0]
	jnt.parentInverseMatrix[0] >> t_mat.matrixIn[1]

	t_mat.matrixSum >> t_dmat.inputMatrix
	t_dmat.outputTranslate >> jnt.translate
	t_dmat.outputScale >> jnt.scale
	t_dmat.outputShear >> jnt.shear

	t_mat.matrixSum >> r_mat.matrixIn[0]
	t_mat.matrixSum >> inv_mat.inputMatrix

	r_mat.matrixIn[1].set(inv_mat.outputMatrix.get())
	pm.delete(inv_mat)

	r_mat.matrixSum >> r_dmat.inputMatrix
	r_dmat.outputRotate >> jnt + ".rotate"
