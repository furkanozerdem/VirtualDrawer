import cv2
import mediapipe as mp
import time
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import numpy as np
import analyzer as AnalyzerPackage

def main():
    analyze = AnalyzerPackage.Analyzer()
    vid = cv2.VideoCapture(0)
    

    
    while(True):
     
        ret, frame = vid.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)      
       
        paintingFrame , frame , blackScreen= analyze.getFrame(frame)
        
        #------------------------------------------------------------#
        #to draw on the frame, we need to use binary threshold method
        #we will going to give a threshold value and then use bitwise operations.
        grayFrame = cv2.cvtColor(blackScreen,cv2.COLOR_BGR2GRAY)
        _ , frameInv = cv2.threshold(grayFrame,59,255,cv2.THRESH_BINARY_INV) #frame is binary image now
        frameInv = cv2.cvtColor(frameInv,cv2.COLOR_GRAY2BGR)

        paintingFrame = cv2.bitwise_and(paintingFrame,frameInv)
        paintingFrame = cv2.bitwise_or(paintingFrame, blackScreen)

        


        cv2.imshow('frame', frame)
        cv2.imshow('painter', paintingFrame)
        cv2.imshow('Black Screen', blackScreen)
       

        #paintingFrame = cv2.addWeighted(paintingFrame,0.2,blackScreen,0.8,0)



        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    
    # After the loop release the cap object
    vid.release()
    # Destroy all the windows
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
