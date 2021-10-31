import struct
rd = renderdoc
class MeshData(rd.MeshFormat):
    indexOffset = 0
    name = ''
plane1 = [6, 12, 30, 48, 60, 66, 78, 96, 123, 156, 216, 237, 264, 270, 273, 306, 393, 360, 369, 384, 438, 462, 468, 528, 564, 576, 576, 594, 648, 714, 744, 768, 771, 774, 786, 798, 828, 834, 849, 864, 882, 996, 1032, 1074, 1116, 1194, 1260, 1368, 1428, 1548, 1848, 1962, 2223, 2652, 2661, 2706, 3078, 3456, 4200, 4302, 4659, 5424, 5973, 6528, 6774, 7116, 7911, 8184, 9198, 9699, 11955, 11979, 15396, 15828, 20637, 28623, 53721, 72174, 94269]
#plane2 = [408, 480, 516, 588, 864, 876, 1242, 1578, 2472, 3246, 3900, 4530, 4548, 8940, 10650, 11886, 37800, 41256, 74943]
plane2 = [516, 864, 876, 1242, 2472, 2520, 2895, 3246, 3306, 3474, 3900, 4020, 4530, 4896, 8940, 10650, 11886, 37800, 41256, 74943, 238368]
#plane2 = [516, 864, 876, 1242, 1578, 2472, 2520, 2895, 3246, 3306, 3474, 3900, 4020, 4530, 4896, 8940, 10650, 11886, 37800, 41256, 74943, 238368]
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
    for idx in indices:

        #print("Vertex %d is index %d:" % (i, idx))
        attr = meshData[0]
        #for attr in meshData:
            # This is the data we're reading from. This would be good to cache instead of
            # re-fetching for every attribute for every index
        offset = attr.vertexByteOffset + attr.vertexByteStride * idx
        data = controller.GetBufferData(attr.vertexResourceId, offset, 0)

        # Get the value from the data
        value = unpackData(attr.format, data)
        with open('pos_' + txt,'a') as f:
            f.write(str(value) + '\n')
        # We don't go into the details of semantic matching here, just print both
        #print("\tAttribute '%s': %s" % (attr.name, value))


def out(controller):

    # Fetch the postvs data
    postvs = controller.GetPostVSData(0, 0, rd.MeshDataStage.VSOut)

    # Calcualte the mesh configuration from that
    meshOutputs = getMeshOutputs(controller, postvs)

    # Print it
    printMeshData(controller, meshOutputs)



def sampleCode(controller):
    draw = controller.GetRootActions()[-1]
    print(draw.eventId)
    controller.SetFrameEvent(draw.eventId, True)

    texsave = rd.TextureSave()
    # Select the first color output
    print(draw.copyDestination)
    texsave.resourceId = draw.copyDestination

    if texsave.resourceId == rd.ResourceId.Null():
        return

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
    controller.SaveTexture(texsave, figure + ".jpg")
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

        print('draw = ',draw.eventId)


        for d in draw.children:
            print('d = ',d.eventId)
            #The reason of 'endIndex -1' is the last draw is just a end symbol
            if d.eventId < startIndex and d.numIndices in plane2:
                controller.SetFrameEvent(d.eventId, True)
                out(controller)
            if d.eventId >= startIndex and d.eventId < endIndex and d.numIndices in plane1:
                controller.SetFrameEvent(d.eventId, True)
                out(controller)
    print('Outputing has been over')
#cap, controller = loadCapture(file)


#for i in range(0,len(meshOutputs)):
#	print('meshOutPuts ',i,' ',meshOutputs[i].indexResourceId)
for i in range(14,15):
    if 'pyrenderdoc' in globals():
        file ='demo'+str(i)+'.rdc'
        figure = 'demo'+str(i)
        filename = file
        pyrenderdoc.LoadCapture(filename, renderdoc.ReplayOptions(), filename, False, True)
        txt = 'demo'+str(i)+'.txt'
        pyrenderdoc.Replay().BlockInvoke(sampleCode)