import cv2
import mediapipe as mp
import time
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from mediapipe.python import solutions
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import numpy as np
import pandas as pd
import analyzer as AnalyzerPackage 


class Painter:
    def __init__(self):
        self.color = (0,0,255) #lines colors (will be able to set this value)
        self.thickness = 2 #lines thickness
        self.cleanThickness = 15 #eraser thickness

        self.prevFinger = np.array([0,0]) # previous Coordinates of finger
        
        self.blackScreen = np.zeros((480,640,3), np.uint8) #lines will be drawn on black screen first. (uint8 is for same type as camera frame)
        
        #specify color platte path
        self.palettePath = r'C:\Users\Furkan\Desktop\Projeler\Python\VirtualDrawer\color_palette.png'
        
        #define color palette from defined path
        self.colorPalette = cv2.imread(self.palettePath)
        
        #define color list from color palette image
        self.colorValueList = [(255,255,255),(255,255,0),(255,0,255),(0,255,255),(0,255,0),(255,0,0),(0,0,255)] #white, cyan, purple, yellow, green, blue, red
        self.colorCordinatesList=[]


        #every singe color element 
        #size in palette
        self.colorPixelWidth = 65
        self.colorPixelHeight = 50

        self.colorList = {} #connection between color values and color area on the palette

        for i in range(1,8):
            p1=(640-(65*(i-1))-10,0)
            p2=(640-(65*i),50)
            #cv2.rectangle(self.colorPalette,p1,p2,(0,0,0),self.thickness)
            self.colorCordinatesList.append((p1,p2)) #coordinates list appended

            self.colorList[(p1,p2)] = self.colorValueList[i-1] #connected
            #with this assignment, we will know which area the indexfinger in. And select that, for drawing color.
    
    def getBlackScreen(self):
        #to call black screen of this painter object  
        return self.blackScreen
    
    def draw(self,painterFrame,fingerPosition):
        
        cv2.circle(painterFrame,(int(fingerPosition[0]), int(fingerPosition[1])),4,(self.color),self.thickness, cv2.FILLED) #filled circle

        currentFingerX = int(fingerPosition[0])
        currentFingerY = int(fingerPosition[1])

        #previousFingerX = int(self.prevFinger[0])
        #previousFingerY = int(self.prevFinger[1])
        
        #print(currentFingerX , " " , currentFingerY)
        

        if((self.prevFinger[0]) == 0 and (self.prevFinger[1]) == 0): #if values are 0, this means frame come first time
            self.prevFinger[0], self.prevFinger[1] = currentFingerX, currentFingerY #set previous coordinate and return
            return painterFrame
 
        previousFingerX = int(self.prevFinger[0])
        previousFingerY = int(self.prevFinger[1])


        #print on black screen by using coordinates
        cv2.line(self.blackScreen,(currentFingerX,currentFingerY),(previousFingerX,previousFingerY),self.color,self.thickness)
        self.prevFinger[0], self.prevFinger[1]= currentFingerX, currentFingerY #change previous finger positions from new ones
        



        return painterFrame

    
    def clean(self, painterFrame, fingerPosition):
        cv2.circle(painterFrame,(int(fingerPosition[0]), int(fingerPosition[1])),self.cleanThickness,(0,0,0),self.thickness, cv2.FILLED) #filled black circle

        currentFingerX = int(fingerPosition[0])
        currentFingerY = int(fingerPosition[1])

       # print(currentFingerX , " " , currentFingerY)

        if(self.prevFinger[0] and (self.prevFinger[1]) == 0):
            self.prevFinger[0], self.prevFinger[1] = currentFingerX, currentFingerY
            return painterFrame

        previousFingerX = int(self.prevFinger[0])
        previousFingerY = int(self.prevFinger[1])

        #clean on black screen by using previous and current coordinate of finger (Clean color = black)
        cv2.line(self.blackScreen,(currentFingerX,currentFingerY),(previousFingerX,previousFingerY),(0,0,0),self.cleanThickness)
       
        self.prevFinger[0], self.prevFinger[1]= currentFingerX, currentFingerY 



        return painterFrame


    def chose(self,painterFrame,fingerPosition):
        #cv2.circle(painterFrame,(int(fingerPosition[0]), int(fingerPosition[1])),self.cleanThickness,(0,0,0),self.thickness, cv2.FILLED) #filled black circle
        cv2.line(painterFrame,(int(fingerPosition[0]), int(fingerPosition[1])),(int(fingerPosition[0]), int(fingerPosition[1]-20)),self.color,self.thickness)
      
        #add color palette to live frame 
        painterFrame[0:50, 0:640, :] = self.colorPalette
        
        
        #print(fingerPosition[0]) #axis x
        #print(fingerPosition[1]) #axis y
        
        currentIndexFingerX , currentIndexFingerY = int(fingerPosition[0]), int(fingerPosition[1])
        
        #previousFingerX = int(self.prevFinger[0])
        #previousFingerY = int(self.prevFinger[1])
        
        #print("x =>" , fingerPosition[0])
        #print("y => " , fingerPosition[1])
            
        #for i in range(1-8):
        #self.isInside(self.colorCordinatesList[1], currentIndexFingerX, currentIndexFingerY)
        
        if(currentIndexFingerY < 50): #if finger is close top to choosing palette
            for i in range(0,7):
                if(self.isInside(self.colorCordinatesList[i], currentIndexFingerX)):
                    #change the color to color area that finger in
                    self.color = self.colorValueList[i]
                    
                    #for removing rectangle from previous color
                    self.colorPalette = cv2.imread(self.palettePath)

                    p1, p2 = self.colorCordinatesList[i]
                    print(self.colorCordinatesList[i])
                    
                    #draw rectangle to choosen color
                    cv2.rectangle(self.colorPalette,p1,p2,(0,0,0),self.thickness)
                
        return painterFrame




    
    def isInside(self, area, fingerX):
        cordinate_0 = area[0]
        cordinate_1 = area[1]
        #y is always 0-50
       
        #x1 > x2
        #y1 < y2
        
        x1 = cordinate_0[0]
        x2 = cordinate_1[0]
      

        if(x1 > fingerX and  x2 < fingerX):
            return True


        return False


