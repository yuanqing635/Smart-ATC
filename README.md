# Smart-ATC
## Project Description
### Backgrounds
This Smart-ATC project is aimed at building a smarter air traffic control system using deep learning.  

Current ATC systems only serve as video monitoring systems that are mainly  used for monitoring the aircrafts on the ground and storing the videoed content. 
However, the control of air traffic still requires tons of human interventions. 
With the construction of more and more airports, the demands for air traffic controller are also increasing, but it's hard to train such a professional controller in a short period. This means that the number of existing air traffic controllers could not meet the demands of evey ATC tower. 
Then, to help address the above problems and make ATC systems smarter, we came up with an idea of a smart air traffic system.  
###  Why Simulated Data
This smart ATC system will have the ability to recognize and track the aircrafts and some other targets both in the sky and on the ground. In this samrt system, we plan to use deep learning to realize the automation of ATC tower. This helps to alleviate the burden on manpower and improve the efficiency of the ATC system at the same time. Our goal is to build a transfer learning framework that is aimed at the detection, segementation and tracking of targets. So, the first step is to construct a proper training data set. The weather and geographical conditions could vary among different airports and the lighting condition could vary across a single day. Thus, to make our deep learning models converge in different scenes, we have to use a data set that contains different images under different environmental conditions. Getting images by photograph is nearly impossible since we would waste plenty of time and manpower on taking photos in different airports around the world. Due to this reason, we decide to generate images using a 3D simulator called Microsoft Flight Simulator 2020. This simulator contains many airports and aircrafts across the globe that are modeled with the proportion of 1:1. However, the output of the trained deep learning model using this simulated data set would not be accurate when it is applied to a practical scene since the feature distribution of the real-scene images is not the same as that of the simulated images. To solve this problem, we will use transfer learning to generate a new model that could function well in practical scenes from the model trained on the simulated data set.   
### What is this repository about
In this project, we will record our progress on constructing the synthetic dataset.
