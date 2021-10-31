# Mesh导出
## 步骤
1、任意打开一张.rdc截图，在左上角Filter文本框里输入函数：$parent(Depth-only Pass #1)

![image](https://user-images.githubusercontent.com/93473296/139592303-ee5bd246-186f-488a-9d30-f1ba8f1a5b92.png)

2、打开Renderdoc图形界面中的Interactive Python Shell(Run Scripts)  
3、点击Open,打开Export_mesh.py  
4、点击Run  
![image](https://user-images.githubusercontent.com/93473296/139592361-e9058a0e-8459-40dd-b2e6-309b03a144c8.png)

## 生成结果
带有所有部件SV_Position的.txt文件
