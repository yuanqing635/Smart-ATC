import struct
import time

rd = renderdoc
class MeshData(rd.MeshFormat):
    indexOffset = 0
    name = ''

#plane1为depth内部的mesh
plane320 = [6, 30, 48, 60, 66, 78, 96, 123, 156, 237, 264, 270, 306, 462, 468, 564, 576, 576, 594, 648, 714, 744, 768, 786, 798, 828, 834, 849, 864, 882, 996, 1032, 1074, 1116, 1194, 1260, 1368, 1428, 1548, 1848, 1962, 2223, 2652, 2661, 2706, 4200, 4659, 5424, 5973, 6774, 7116, 7911, 8184, 9699, 15396, 15828, 20637, 53721]
plane747 = [6, 9, 12, 18, 24, 30, 36, 54, 60, 63, 69, 72, 78, 117, 123, 126, 153, 192, 198, 201, 204, 207, 210, 255, 264, 270, 294, 303, 309, 318, 321, 324, 327, 360, 375, 423, 447, 516, 576, 612, 618, 663, 762, 774, 876, 972, 1014, 1116, 1188, 1209, 1227, 1236, 1248, 1254, 1272, 1383, 1404, 1476, 1548, 1668, 1680, 1746, 3027, 3033, 3156, 3714, 4671, 5109, 5130, 5994, 6690, 7380, 7995, 8826, 9687, 9897, 10026, 10626, 19377, 35202]
#plane2为depth1外部的mesh
#plane2 = [408, 480, 516, 588, 864, 876, 1242, 1578, 2472, 3246, 3900, 4530, 4548, 8940, 10650, 11886, 37800, 41256, 74943]
_plane320 = [516, 864, 876, 1242, 2472, 2520, 2895, 3246, 3306, 3474, 3900, 4020, 4530, 4896, 8940, 10650, 11886, 37800, 41256, 74943, 238368]
_plane747 = [150, 210, 228, 288, 330, 342, 429, 450, 456, 492, 672, 684, 690, 756, 888, 972, 1404,1470, 1626, 1632, 1674, 1704, 1710, 1743, 1896, 1968, 2088, 2124, 2274, 2289, 2430, 2652, 2994, 3048, 3057, 3066, 3282, 3822, 3909, 3948, 4170, 4221, 7989, 8166, 8376, 9027, 9258, 10044, 10338, 10401, 13818, 13866, 15390, 17769, 18891, 20646, 21609, 21912, 22125, 22062, 28929, 32778, 32814, 34563, 37515]
#plane2 = [238368]
#maxsize = 1e5
#238368->size = 19558077
#vis = [864,2472,3246,480,37800,11886,10650,264,4530,4548,1242,876,408, 516,8940,588,1578,41256,3900]
#startIndex, endIndex  = 34655,34817
##################################

def getMeshOutputs(controller, postvs):
    meshOutputs = []
    posidx = 0

    vs = controller.GetPipelineState().GetShaderReflection(rd.ShaderStage.Vertex)

    # Repeat the process, but this time sourcing the data from postvs.
    # Since these are outputs, we iterate over the list of outputs from the
    # vertex shader's reflection data
    for attr in vs.outputSignature:
        # Copy most properties from the postvs struct
        meshOutput = MeshData()
        meshOutput.indexResourceId = postvs.indexResourceId
        meshOutput.indexByteOffset = postvs.indexByteOffset
        meshOutput.indexByteStride = postvs.indexByteStride
        meshOutput.baseVertex = postvs.baseVertex
        meshOutput.indexOffset = 0
        meshOutput.numIndices = postvs.numIndices

        # The total offset is the attribute offset from the base of the vertex,
        # as calculated by the stride per index
        meshOutput.vertexByteOffset = postvs.vertexByteOffset
        meshOutput.vertexResourceId = postvs.vertexResourceId
        meshOutput.vertexByteStride = postvs.vertexByteStride

        # Construct a resource format for this element
        meshOutput.format = rd.ResourceFormat()
        meshOutput.format.compByteWidth = rd.VarTypeByteSize(attr.varType)
        meshOutput.format.compCount = attr.compCount
        meshOutput.format.compType = rd.VarTypeCompType(attr.varType)
        meshOutput.format.type = rd.ResourceFormatType.Regular

        meshOutput.name = attr.semanticIdxName if attr.varName == '' else attr.varName

        if attr.systemValue == rd.ShaderBuiltin.Position:
            posidx = len(meshOutputs)

        meshOutputs.append(meshOutput)

    # Shuffle the position element to the front
    if posidx > 0:
        pos = meshOutputs[posidx]
        del meshOutputs[posidx]
        meshOutputs.insert(0, pos)

    accumOffset = 0

    for i in range(0, len(meshOutputs)):
        meshOutputs[i].vertexByteOffset = accumOffset

        # Note that some APIs such as Vulkan will pad the size of the attribute here
        # while others will tightly pack
        fmt = meshOutputs[i].format

        accumOffset += (8 if fmt.compByteWidth > 4 else 4) * fmt.compCount
    return meshOutputs

def unpackData(fmt, data):
    # We don't handle 'special' formats - typically bit-packed such as 10:10:10:2
    if fmt.Special():
        raise RuntimeError("Packed formats are not supported!")

    formatChars = {}
    #                                 012345678
    formatChars[rd.CompType.UInt] = "xBHxIxxxL"
    formatChars[rd.CompType.SInt] = "xbhxixxxl"
    formatChars[rd.CompType.Float] = "xxexfxxxd"  # only 2, 4 and 8 are valid

    # These types have identical decodes, but we might post-process them
    formatChars[rd.CompType.UNorm] = formatChars[rd.CompType.UInt]
    formatChars[rd.CompType.UScaled] = formatChars[rd.CompType.UInt]
    formatChars[rd.CompType.SNorm] = formatChars[rd.CompType.SInt]
    formatChars[rd.CompType.SScaled] = formatChars[rd.CompType.SInt]

    # We need to fetch compCount components
    vertexFormat = str(fmt.compCount) + formatChars[fmt.compType][fmt.compByteWidth]

    # Unpack the data
    value = struct.unpack_from(vertexFormat, data, 0)

    # If the format needs post-processing such as normalisation, do that now
    if fmt.compType == rd.CompType.UNorm:
        divisor = float((2 ** (fmt.compByteWidth * 8)) - 1)
        value = tuple(float(i) / divisor for i in value)
    elif fmt.compType == rd.CompType.SNorm:
        maxNeg = -float(2 ** (fmt.compByteWidth * 8)) / 2
        divisor = float(-(maxNeg - 1))
        value = tuple((float(i) if (i == maxNeg) else (float(i) / divisor)) for i in value)

    # If the format is BGRA, swap the two components
    if fmt.BGRAOrder():
        value = tuple(value[i] for i in [2, 1, 0, 3])

    return value

def getIndices(controller, mesh):
    # Get the character for the width of index
    indexFormat = 'B'
    if mesh.indexByteStride == 2:
        indexFormat = 'H'
    elif mesh.indexByteStride == 4:
        indexFormat = 'I'

    # Duplicate the format by the number of indices
    indexFormat = str(mesh.numIndices) + indexFormat

    # If we have an index buffer
    if mesh.indexResourceId != rd.ResourceId.Null():
        #
        #print('mesh.indexResourceId = ',mesh.indexResourceId)
        #
        # Fetch the data
        ibdata = controller.GetBufferData(mesh.indexResourceId, mesh.indexByteOffset, 0)

        # Unpack all the indices, starting from the first index to fetch
        offset = mesh.indexOffset * mesh.indexByteStride
        indices = struct.unpack_from(indexFormat, ibdata, offset)

        # Apply the baseVertex offset
        return [i + mesh.baseVertex for i in indices]
    else:
        # With no index buffer, just generate a range
        print('mesh.numIndices = ',mesh.numIndices)
        return tuple(range(mesh.numIndices))
def printVar(v, indent=''):
    print(indent + v.name + ":")
    if len(v.members) == 0:
        valstr = ""
        for r in range(0, v.rows):

            valstr += indent

            for c in range(0, v.columns):
                valstr += '%.5f ' % v.value.f32v[r * v.columns + c]

            if r < v.rows - 1:
                valstr += "\n"
        print(valstr)
        with open(path + txt, 'a') as f:
            f.write(valstr)
    for v in v.members:
        printVar(v, indent + '    ')
def printMeshData(controller, meshData):
    # meshData is MeshOutputs that is a list[MeshData]
    # indices is the mesh's idx[]
    indices = getIndices(controller, meshData[0])
    #print('indices = ',indices)

    #print("GetEventName(eventId) = ",qrenderdoc.EventBrowser().GetEventName(34655))
    #print("Mesh configuration:")
    #for attr in meshData:
    #    print("\t%s:" % attr.name)
    #    print("\t\t- vertex: %s / %d stride" % (attr.vertexResourceId, attr.vertexByteStride))
    #    print("\t\t- format: %s x %s @ %d" % (attr.format.compType, attr.format.compCount, attr.vertexByteOffset))

    # We'll decode the first three indices making up a triangle
    #
    # choose the numbers of vertex in this range
    #
    #outtxt = ''
    #print('This mesh size is ',len(indices))
    #size is 238368
    with open(path + 'pos_' + txt, 'a') as f:
        for idx in indices:
            #t0 = time.time()
            #print("Vertex %d is index %d:" % (i, idx))
            attr = meshData[0]
            #for attr in meshData:
            # This is the data we're reading from. This would be good to cache instead of
            # re-fetching for every attribute for every index
            offset = attr.vertexByteOffset + attr.vertexByteStride * idx
            data = controller.GetBufferData(attr.vertexResourceId, offset, 0)

            # Get the value from the data
            value = unpackData(attr.format, data)
            value = str(value) + '\n'

            #outtxt += str(value) + '\n'
            #if len(outtxt) % 1000 == 0:
            #    print('len = ',len(outtxt))

            #if len(outtxt) > maxsize:
            f.write(value)
            #    outtxt = ''
            #print('this time use ',time.time() - t0)

            # We don't go into the details of semantic matching here, just print both
            #print("\tAttribute '%s': %s" % (attr.name, value))
        #print('outtxt = ', outtxt)
    #print('size = ', len(outtxt))
    #return outtxt

def out(controller):

    # Fetch the postvs data
    postvs = controller.GetPostVSData(0, 0, rd.MeshDataStage.VSOut)

    # Calcualte the mesh configuration from that
    meshOutputs = getMeshOutputs(controller, postvs)

    # Print it
    printMeshData(controller, meshOutputs)



def sampleCode(controller):
    t0 = time.time()
    draw = controller.GetRootActions()[-1]
    print(draw.eventId)
    controller.SetFrameEvent(draw.eventId, True)
    texsave = rd.TextureSave()
    # Select the first color output
    print(draw.copyDestination)
    texsave.resourceId = draw.copyDestination

    if texsave.resourceId == rd.ResourceId.Null():
        return

    ##导出RT矩阵

    state = controller.GetPipelineState()
    pipe = state.GetGraphicsPipelineObject()
    entry = state.GetShaderEntryPoint(rd.ShaderStage.Vertex)
    ps = state.GetShaderReflection(rd.ShaderStage.Vertex)
    cb = state.GetConstantBuffer(rd.ShaderStage.Vertex, 0, 0)
    cbufferVars = controller.GetCBufferVariableContents(pipe, ps.resourceId, entry, 0, cb.resourceId, 0, 0)
    for v in cbufferVars:
        printVar(v)

    ##导出RT

    filename = str(int(texsave.resourceId))
    print("Saving images of %s at %d: %s" % (filename, draw.eventId, draw.GetName(controller.GetStructuredFile())))

    # Save different types of texture

    # Blend alpha to a checkerboard pattern for formats without alpha support
    texsave.alpha = rd.AlphaMapping.BlendToCheckerboard

    # Most formats can only display a single image per file, so we select the
    # first mip and first slice
    texsave.mip = 0
    texsave.slice.sliceIndex = 0

    texsave.destType = rd.FileType.JPG
    controller.SaveTexture(texsave, path + figure + ".jpg")
    # Find the biggest drawcall=event in the whole capture
    event = pyrenderdoc.GetEventBrowser()
    print(event.GetCurrentFilterText())
    event.SetEmptyRegionsVisible(True)
    eid = pyrenderdoc.GetLastAction().eventId
    # print(eid)
    startIndex = 0
    endIndex = 0
    for i in range(1, eid):
        if event.IsAPIEventVisible(i) == 1:
            # print(i)
            startIndex = i
            break
    for k in range(startIndex, eid):
        if event.IsAPIEventVisible(k) == 0:
            # print(k)
            endIndex = k
            break

    for draw in controller.GetRootActions():
        #outtxt = ''
        print('draw = ',draw.eventId)

        for d in draw.children:
            print('d = ',d.eventId)
            #The reason of 'endIndex -1' is the last draw is just a end symbol
            if d.eventId < startIndex:
                if d.numIndices in _plane:
                    controller.SetFrameEvent(d.eventId, True)
                    #outtxt += out(controller)
                    out(controller)
            elif d.eventId < endIndex:
                if d.numIndices in plane:
                    controller.SetFrameEvent(d.eventId, True)
                    #outtxt += out(controller)
                    out(controller)
            else:
                break
        #if outtxt != '':
        #    with open('pos_' + txt, 'a') as f:
        #        f.write(outtxt)
    t1 = time.time()
    print('Outputing has been over,using time:', t1 - t0)
#cap, controller = loadCapture(file)


#for i in range(0,len(meshOutputs)):
#	print('meshOutPuts ',i,' ',meshOutputs[i].indexResourceId)
for i in range(1,253):
    if 'pyrenderdoc' in globals():
        #选择对应planeSize
        plane = {}
        _plane = {}
        if 1 <= i <= 36:
            plane = plane320
            _plane = _plane320
        elif 37 <= i <= 216:
            plane = plane320
            _plane = _plane320
        elif 217<= i <= 252:
            plane = plane747
            _plane = _plane747
        path = "F:\\dataset\\"#C:\\Users\\00\\Desktop\\
        file = str(i)+'.rdc'
        figure = str(i)
        txt = str(i)+'.txt'
        pyrenderdoc.LoadCapture(file, renderdoc.ReplayOptions(), file, False, True)
        pyrenderdoc.Replay().BlockInvoke(sampleCode)


