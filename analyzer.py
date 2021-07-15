import cv2
import mediapipe as mp
import time
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import numpy as np
import pandas as pd
import painter as PainterPackage 

class Analyzer:
    def __init__(self):
        self.prevFrameTime = 0
        self.currentFrameTime = 0
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands()
        self.mpDraw = mp.solutions.drawing_utils
        self.hands = self.mpHands.Hands()
        self.fingerYPositions = pd.DataFrame({ 
            "indexFinger" : 0 , #column
            "middleFinger" : 0 , #column
            "ringFinger" : 0 ,  #column
            "littleFinger" : 0 }, #column
            index = [0,1] #rows
            ) 
              #index 0 is end of the finger
              #index 1 is first joint area from bottom of that finger
        
        self.fingerStateCode = -1 #not assigned yet (this value represents what hand will do according to its fingers positions)
        self.indexFingerPosition = np.array([0,0]) # index finger coordinates (x,y)

        self.painterObject = PainterPackage.Painter()
        self.paintingFrame = np.zeros((480,640,3),np.uint8) 

    def fpsMeter(self):
        #fps calculation
        self.currentFrameTime = time.time() #get time for that frame
        fps = 1/(self.currentFrameTime - self.prevFrameTime) #calculate fps according to previous one
        self.prevFrameTime = self.currentFrameTime #get ready for new calculation (waiting for currentFrameTime)

        return int(fps)
        

    def getFrame(self,frame):
        #frame that will be painting
        self.paintingFrame = frame.copy()

        #calculate fps for measuring performance
        fps = self.fpsMeter() 
        
        #text align and put it on frame
        #0,0 is bottom left corner
        fpsTextPosition = (int(frame.shape[0] * 1/10),int(frame.shape[1] * 7/10) )
        cv2.putText(frame,"Fps :" + str(fps), fpsTextPosition,cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),2)
        

        #if there is a hand on the screen
        if(self.handAnalyze(frame)):
            if(self.fingerStateCode == 0 ): #Clean Mode
               
                #when hand removes from camera and then come back, the last coordinates should be remove
                self.painterObject.prevFinger = np.array([0,0])

                self.paintingFrame = self.painterObject.clean(self.paintingFrame, self.indexFingerPosition)
              
            elif(self.fingerStateCode == 1): #Draw Mode
               self.paintingFrame  = self.painterObject.draw(self.paintingFrame, self.indexFingerPosition)
               

            elif(self.fingerStateCode == 2): #Cancel Mode
               
               #when hand removes from camera and then come back, the last coordinates should be remove
               self.painterObject.prevFinger = np.array([0,0])
                 
            elif(self.fingerStateCode == 3 ): #Choose Mode
               #self.paintingFrame = self.painterObject.test(self.paintingFrame, self.indexFingerPosition)
                #when hand removes from camera and then come back, the last coordinates should be remove
                self.painterObject.prevFinger = np.array([0,0])
                self.paintingFrame = self.painterObject.chose(self.paintingFrame, self.indexFingerPosition)
                
               
        else: #only the case that hands can't find
            #when hand removes from camera and then come back, the last coordinates should be remove
            self.painterObject.prevFinger = np.array([0,0]) 

        #get drawn black screen from painter class
        blackScreen = self.painterObject.getBlackScreen()    
        
     
        #if not, return frame

        return self.paintingFrame , frame ,blackScreen
    

    def handAnalyze(self, frame):
        
        results = self.hands.process(frame) #trying to find any hand on frame
        if(results.multi_hand_landmarks): #if frame includes any hand

            #for drawing hand, need to use double for loop
            for handLandmarks in results.multi_hand_landmarks: 
                for id, lm in enumerate(handLandmarks.landmark):
                    self.mpDraw.draw_landmarks(frame,handLandmarks,self.mpHands.HAND_CONNECTIONS)

                    #to avoid multiple loops for better performance, need to get finger positions in the same loop as hand drawer loops

                    #to get finger Y positions => y * height of frame
                    #height of frame = frame.shape[0]
                    
                    #index finger positions
                    if (id == 6):
                        self.fingerYPositions.iloc[1]["indexFinger"] = lm.y * frame.shape[0] 
                    elif(id == 8):
                        self.fingerYPositions.iloc[0]["indexFinger"] = lm.y * frame.shape[0] 
                        
                        #to paint or any other options, need to track end of finger in object
                        self.indexFingerPosition = np.array([lm.x*frame.shape[1] , lm.y * frame.shape[0]])

                    #middle finger positions
                    elif(id == 10):
                        self.fingerYPositions.iloc[1]["middleFinger"] = lm.y * frame.shape[0] 
                    elif(id == 12):
                        self.fingerYPositions.iloc[0]["middleFinger"] = lm.y * frame.shape[0] 
                   
                    #ring finger positions
                    elif(id == 14):
                        self.fingerYPositions.iloc[1]["ringFinger"] = lm.y * frame.shape[0] 
                    elif(id == 16):
                        self.fingerYPositions.iloc[0]["ringFinger"] = lm.y * frame.shape[0] 
                   
                    #little finger positions
                    elif(id == 18):
                        self.fingerYPositions.iloc[1]["littleFinger"] = lm.y * frame.shape[0] 
                    elif(id == 20):
                        self.fingerYPositions.iloc[0]["littleFinger"] = lm.y * frame.shape[0] 

            #print(self.fingerYPositions)
          
            stateText, stateCode = self.fingerAnalyze() #to get which mode are we in and its code. To make decision what hand will do.

            #put mode text on the frame
            stateTextPosition = (int(frame.shape[0] * 3/10),int(frame.shape[1] * 2/10) )
            cv2.putText(frame,str(stateText),stateTextPosition,cv2.FONT_HERSHEY_COMPLEX,1,(0,255,255))
            
            
            self.fingerStateCode = stateCode
            self.fingerStateText = stateText

            return True #hand detected and finger position has been calculated

        return False #there is no hand in frame


    def fingerAnalyze(self): 
        #this function is for calculating finger position to choose one specific mode from below
        #cancel : to do nothing. Any draw or erase etc.
        #clean mode : to remove lines from screen
        #draw mode : to draw lines to screen
        #chose mode : select color or set thickness from palette

        fingerState = np.array([0,0,0,0]) #index, middle, ring, little
        
        # 1 is represents finger not to bend
        # 0 is represents finger bends
        fingerState[0] = 1 if (self.fingerYPositions.iloc[1]["indexFinger"] > self.fingerYPositions.iloc[0]["indexFinger"]) else 0
        fingerState[1] = 1 if (self.fingerYPositions.iloc[1]["middleFinger"] > self.fingerYPositions.iloc[0]["middleFinger"]) else 0
        fingerState[2] = 1 if (self.fingerYPositions.iloc[1]["ringFinger"] > self.fingerYPositions.iloc[0]["ringFinger"]) else 0
        fingerState[3] = 1 if (self.fingerYPositions.iloc[1]["littleFinger"] > self.fingerYPositions.iloc[0]["littleFinger"]) else 0

        stateText = ""
        stateCode = 0

        if(np.array_equal(fingerState , np.array([0,0,0,0]))): 
            stateText, stateCode = "Clean Mode" , 0
        elif(np.array_equal(fingerState , np.array([1,0,0,0]))):
            stateText, stateCode = "Draw Mode" , 1
        elif(np.array_equal(fingerState , np.array([1,1,0,0]))):
            stateText, stateCode = "Cancel Mode" , 2
        elif(np.array_equal(fingerState , np.array([1,1,1,0]))):
             stateText, stateCode = "Chose Mode" , 3



        return stateText, stateCode
