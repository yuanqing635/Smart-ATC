import cv2
import numpy as np
from scipy.spatial import ConvexHull

#file = "G:/MSFS Captures/pos_demo"+st

def mark(img,df_nd):
    df_nd = df_nd.astype(int)
    len = df_nd.shape[1]
    df_nd = np.unique(df_nd, axis=0)
    for k in range(len):
        i, j = df_nd[0][k], df_nd[1][k]
        if i > 1080 or i <= 0 or j <= 0 or j > 1920:
            continue
        i -= 1
        j -= 1
        img[i,j] = (0,0,255)
    return img

#ConvexHull函数作用为找凸包，但不适合用于间断的线
def Hull(df_nd,points):
    hull = ConvexHull(df_nd)
    #print(type(hull.vertices),hull.vertices)

    for item in (hull.vertices):
        points.append([int(df_nd[item][0]),int(df_nd[item][1])])
    #points = np.array(points)
    return points






for i in range(14,15):
    ################################################
    impath = "G:/MSFS Captures/demo"+str(i)+".jpg"
    img = cv2.imread(impath)
    print(len(img))
    # 修改部分列名（感觉是多余操作）
    # df = df.rename(columns={" SV_Position.x":"SV_PositionX", " SV_Position.y":"SV_PositionY"," SV_Position.w":"SV_PositionW",})
    file = "G:/MSFS Captures/pos_demo"+str(i)+".txt"
    with open(file, encoding='utf=8') as f:
        lines = f.readlines()
    df = [[], []]
    for line in lines:
        d = line.strip().strip('()').split(',')
        d = list(map(float, d))

        # 投影（不太理解公式为啥是这样）
        df[0].append((d[0] / d[3] + 1) / 2 * 1920)
        df[1].append(1080 - (d[1] / d[3] + 1) / 2 * 1080)
    df_nd = np.array(df)
    #######################################################
    m = 0
    k = df_nd.shape[1]
    # print(df_nd)
    # points = []

    while m <= k - 3:
        mesh = []
        for n in range(m, m + 3):
            mesh.append([df_nd[0][n], df_nd[1][n]])

        # points = Hull(mesh, points,i//3)
        #print(m // 3, ' ')
        m += 3
        # print(i)
        mesh = np.array(mesh)
        mesh = mesh.astype(int)
        cv2.fillPoly(img, [mesh], (0, 0, 128))
    #points = np.array(points)
    #print(t)
    #cv2.fillPoly(img, [points], (0, 0, 128))
    #img = mark(img,df_nd)
    figname = 'labeled_demo'+str(i)+'.jpg'
    cv2.imwrite(figname,img)
    cv2.imshow("1",img)
    cv2.waitKey(0)