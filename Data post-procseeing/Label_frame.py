import cv2
import numpy as np
from scipy.spatial import ConvexHull
from queue import Queue
q = Queue(300000)
import copy
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

def getmat(img):
    label = [[0] * 1920 for i in range(1080)]
    for i in range(0,1080):
        for j in range(0,1920):
            if all(img[i,j] == (0,0,255)):
                label[i][j] = 1
    return label

#dfs会导致栈溢出，所以需要用BFS
def find(label,vis):
    while(q.empty() == 0):
        (x, y) = q.get()
        if x - 1 >= 0 and label[x - 1][y] == 1 and vis[x - 1][y] == 0:
            vis[x - 1][y] = 1
            size[0] += 1
            q.put((x - 1,y))
        if x + 1 < 1080 and label[x + 1][y] == 1 and vis[x + 1][y] == 0:
            vis[x + 1][y] = 1
            size[0] += 1
            q.put((x + 1, y))
        if y + 1 < 1920 and label[x][y + 1] == 1 and vis[x][y + 1] == 0:
            vis[x][y + 1] = 1
            size[0] += 1
            q.put((x, y + 1))
        if y - 1 >= 0 and label[x][y - 1] == 1 and vis[x][y - 1] == 0:
            vis[x][y - 1] = 1
            size[0] += 1
            q.put((x, y - 1))

def Maxcon(label):
    maxsize = 0
    maxi = 0
    maxj = 0
    vis = [[0] * 1920 for i in range(1080)]
    for i in range(0, 1080):
        for j in range(0, 1920):
            size[0] = 0
            if label[i][j] == 1 and vis[i][j] == 0:
                q.put((i,j))
                vis[i][j] = 1
                size[0] += 1
                find(label,vis)
            if maxsize < size[0]:
                maxi = i
                maxj = j
                maxsize = size[0]
    return maxi,maxj

def con(label,i,j):
    vis = [[0] * 1920 for i in range(1080)]
    q.put((i,j))
    vis[i][j] = 1
    while (q.empty() == 0):
        (x, y) = q.get()
        if x - 1 >= 0 and label[x - 1][y] == 1 and vis[x - 1][y] == 0:
            vis[x - 1][y] = 1
            maxmat[0].append(x - 1)
            maxmat[1].append(y)
            q.put((x - 1, y))
        if x + 1 < 1080 and label[x + 1][y] == 1 and vis[x + 1][y] == 0:
            vis[x + 1][y] = 1
            maxmat[0].append(x + 1)
            maxmat[1].append(y)
            q.put((x + 1, y))
        if y + 1 < 1920 and label[x][y + 1] == 1 and vis[x][y + 1] == 0:
            vis[x][y + 1] = 1
            maxmat[0].append(x)
            maxmat[1].append(y + 1)
            q.put((x, y + 1))
        if y - 1 >= 0 and label[x][y - 1] == 1 and vis[x][y - 1] == 0:
            vis[x][y - 1] = 1
            maxmat[0].append(x)
            maxmat[1].append(y - 1)
            q.put((x, y - 1))

size = [0]
i = 217
#for i in range(1,253):
    ################################################
path = "C:\\Users\\00\\Desktop\\"
impath = path + str(i) + ".jpg"
print(impath)
img = cv2.imread(impath)
print(img.shape)
# 修改部分列名（感觉是多余操作）
# df = df.rename(columns={" SV_Position.x":"SV_PositionX", " SV_Position.y":"SV_PositionY"," SV_Position.w":"SV_PositionW",})
file = path + "pos_" + str(i) + ".txt"
with open(file, encoding='utf=8') as f:
    lines = f.readlines()
df = [[], []]
#depth = []#深度
for line in lines:
    d = line.strip().strip('()').split(',')
    d = list(map(float, d))
    #print(np.array(d).shape)
    # 投影（不太理解公式为啥是这样）
    df[0].append((d[0] / d[3] + 1) / 2 * 1920)
    df[1].append((1 - (d[1] / d[3])) / 2 * 1080)
    #depth.append(d[2]/d[3])
df_nd = np.array(df)
#######################################################
m = 0
k = df_nd.shape[1]
# print(df_nd)
# points = []
_img = copy.deepcopy(img)
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
    cv2.fillPoly(img, [mesh], (0, 0, 255))

#得到最大连通域
maxmat = [[],[]]
label = getmat(img)
mi,mj = Maxcon(label)
max = con(label,mi,mj)
_img = mark(_img, np.array(maxmat))
print("the max connect has finished")
# 写入图像并存飞机坐标
with open('GT_' + str(i) + '.txt', 'a') as f:
    for i in range(len(maxmat[0])):
        x = maxmat[0][i]
        y = maxmat[1][i]
        st = '(' + str(x) + ',' + str(y) + ')\n'
        f.write(st)
savepath = ""
figname = savepath + 'labeled_'+str(i)+'.jpg'
cv2.imwrite(figname,_img)
cv2.imshow("1",_img)
cv2.waitKey(0)

# points = np.array(points)
# print(t)
# cv2.fillPoly(img, [points], (0, 0, 128))
# img = mark(img,df_nd)


# 此处为有噪声图
# savepath = ""
# figname = savepath + 'labeled_'+str(i)+'.jpg'
# cv2.imwrite(figname,img)
# cv2.imshow("1",img)
# cv2.waitKey(0)
#