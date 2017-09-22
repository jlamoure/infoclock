#!/usr/bin/env python
# coding: UTF-8
# license: GPL
#
## @package _08c_clock
#
#  A very simple analog clock.
#
#  The program transforms worldcoordinates into screencoordinates 
#  and vice versa according to an algorithm found in: 
#  "Programming principles in computer graphics" by Leendert Ammeraal.
#
#  Based on the code of Anton Vredegoor (anton.vredegoor@gmail.com) 
#
#  @author Paulo Roma
#  @since 01/05/2014
#  @see https://code.activestate.com/recipes/578875-analog-clock
#  @see http://orion.lcg.ufrj.br/python/figuras/fluminense.png

# TODO label inside of perimeter circles at the hours
# TODO make semicircle function
# TODO add light/dark semicircles around clock

import sys, types, os, subprocess
import time
from time import localtime
from datetime import timedelta,datetime
from math import floor, ceil, pi, atan, tan, sin, asin, cos, acos
from threading import Thread
import numpy as np
import json # for forecast
from pprint import pprint

try:
    from tkinter import *       # python 3
except ImportError:
    try:
       from mtTkinter import *  # for thread safe
    except ImportError:
       from Tkinter import *    # python 2
import sun
import tkFont


hasPIL = True
# we need PIL for resizing the background image
# in Fedora do: yum install python-pillow-tk
# or yum install python3-pillow-tk
try:
    from PIL import Image, ImageTk
except ImportError:
    hasPIL = False

## Class for handling the mapping from window coordinates
#  to viewport coordinates.
#
class mapper:
    ## Constructor.
    #
    #  @param world window rectangle.
    #  @param viewport screen rectangle.
    #
    def __init__(self, world, viewport):
        self.world = world 
        self.viewport = viewport
        x_min, y_min, x_max, y_max = self.world
        X_min, Y_min, X_max, Y_max = self.viewport
        f_x = float(X_max-X_min) / float(x_max-x_min) 
        f_y = float(Y_max-Y_min) / float(y_max-y_min) 
        self.f = min(f_x,f_y)
        x_c = 0.5 * (x_min + x_max)
        y_c = 0.5 * (y_min + y_max)
        X_c = 0.5 * (X_min + X_max)
        Y_c = 0.5 * (Y_min + Y_max)
        self.c_1 = X_c - self.f * x_c
        self.c_2 = Y_c - self.f * y_c

    ## Maps a single point from world coordinates to viewport (screen) coordinates.
    #
    #  @param x, y given point.
    #  @return a new point in screen coordinates.
    #
    def __windowToViewport(self, x, y):
        X = self.f *  x + self.c_1
        Y = self.f * -y + self.c_2      # Y axis is upside down 
        return X , Y

    ## Maps two points from world coordinates to viewport (screen) coordinates.
    #
    #  @param x1, y1 first point.
    #  @param x2, y2 second point.
    #  @return two new points in screen coordinates.
    #
    def windowToViewport(self,x1,y1,x2,y2):
        return self.__windowToViewport(x1,y1),self.__windowToViewport(x2,y2)

## Class for creating a new thread.
#
class makeThread (Thread):
      """Creates a thread."""

      ## Constructor.
      #  @param func function to run on this thread.
      #
      def __init__ (self,func):
          Thread.__init__(self)
          self.__action = func
          self.debug = False

      ## Destructor.
      #
      def __del__ (self):
          if ( self.debug ): print ("Thread end")

      ## Starts this thread.
      #
      def run (self):
          if ( self.debug ): print ("Thread begin")
          self.__action()

## Class for drawing a simple analog clock.
#  The backgroung image may be changed by pressing key 'i'.
#  The image path is hardcoded. It should be available in directory 'images'.
#
class clock:
    ## Constructor.
    #
    #  @param deltahours time zone.
    #  @param sImage whether to use a background image.
    #  @param w canvas width.
    #  @param h canvas height.
    #  @param useThread whether to use a separate thread for running the clock.
    #
    def __init__(self,root,deltahours = 0,sImage = True,w = 500,h = 500,useThread = False):
        self.world       = [-1,-1,1,1]
        #FIXME background don't work
        self.imgPath     = "/home/jacob/images/wallpapers/scapes/sacramento_6777f194dfd545c98482ffec2b088609.jpeg"  # image path
        if hasPIL and os.path.exists (self.imgPath):
           self.showImage = sImage
        else:
           self.showImage = False

        self.setColors()
        self._ALL        = 'handles'
        self.root        = root
        width, height    = w, h
        self.pad         = width/16

        self.daytime = True

        if self.showImage:
           self.fluImg = Image.open(self.imgPath)

        self.root.bind("<Escape>", lambda _ : root.destroy())
        self.delta = timedelta(hours = deltahours)  
        self.canvas = Canvas(root, width = width, height = height, background = self.bgcolor)


        viewport = (self.pad,self.pad,width-self.pad,height-self.pad)
        self.T = mapper(self.world,viewport)
        self.root.title('Clock')
        self.canvas.bind("<Configure>",self.resize)
        self.root.bind("<KeyPress-i>", self.toggleImage)
        self.canvas.pack(fill=BOTH, expand=YES)

        if useThread:
           st=makeThread(self.poll)
           #st2=makeThread(self.weather)
           #st3=makeThread(self.display)
           print("Starting threads")
           st.debug = True
           st.start()
           #st2.debug = True
           #st2.start()
           #st3.debug = True
           #st3.start()
        else:
           self.poll()

    ## Called when the window changes, by means of a user input.
    #
    def resize(self,event):
        sc = self.canvas
        sc.delete(ALL)            # erase the whole canvas
        width  = sc.winfo_width()
        height = sc.winfo_height()

        imgSize = min(width, height)
        self.pad = imgSize/16
        viewport = (self.pad,self.pad,width-self.pad,height-self.pad)
        self.T = mapper(self.world,viewport)

        '''
        if self.showImage:
           flu = self.fluImg.resize((int(0.8*0.8*imgSize), int(0.8*imgSize)), Image.ANTIALIAS) 
           self.flu = ImageTk.PhotoImage(flu)
           sc.create_image(width/2,height/2,image=self.flu)
        else:
           self.canvas.create_rectangle([[0,0],[width,height]], fill = self.bgcolor)
        '''

        self.redraw()             # redraw the clock	

    ## Sets the clock colors.
    #
    def setColors(self):
        if self.showImage:
           self.bgcolor     = 'antique white'
           self.timecolor   = 'dark orange'
           self.circlecolor = 'dark green'
        else:
           self.bgcolor     = '#000000'
           self.timecolor   = 'black'
           self.circlecolor = '#ffffff'
           self.nightcolor = 'navy'
           self.daycolor = 'sky blue'
           self.hourcolor = 'black'

    ## Toggles the displaying of a background image.
    #
    def toggleImage(self,event):
        if hasPIL and os.path.exists (self.imgPath):
           self.showImage = not self.showImage
           self.setColors()
           self.resize(event)

    ## Draws a circle at a given point.
    # 
    #  @param x,y given point.
    # 
    def paintcircle(self,x,y,size,color):
        ss = size
        sco = self.canvas.create_oval
        sco(self.T.windowToViewport(-ss+x,-ss+y,ss+x,ss+y), fill = color)

    ## Draws the handles.
    # 
    def painthms(self):
        # size the clock
        hrSz = 0.45
        mnSz = 0.67
        scSz = 0.67
        handWidth = self.pad/5
        secondWidth = self.pad/10
        #
        T = datetime.timetuple(datetime.utcnow()-self.delta)
        x,x,x,h,m,s,x,x,x = T
        self.root.title('%02i:%02i:%02i' %(h,m,s))
        scl = self.canvas.create_line
        # draw the hour handle
        angle = pi/2. - pi/12. * (h + m/60.0) # pi/12 is one hour
        scl(self.T.windowToViewport(0,0,(cos(angle)*hrSz),(sin(angle)*hrSz)), fill = self.timecolor, tag=self._ALL, width = handWidth)
        # draw the minute handle
        angle = pi/2 - pi/30 * (m + s/60.0) # pi/30 is one minute
        x, y = cos(angle)*mnSz,sin(angle)*mnSz
        scl(self.T.windowToViewport(0,0,x,y), fill = self.timecolor, tag=self._ALL, width = handWidth)
        # draw the second handle
        angle = pi/2 - pi/30 * s # pi/30 is one minute
        x, y = cos(angle)*scSz,sin(angle)*scSz
        scl(self.T.windowToViewport(0,0,cos(angle)*scSz,sin(angle)*scSz), fill = self.timecolor, tag=self._ALL, arrow = 'last', width = secondWidth)
    
    ## Draws the daylight/night
    # 
    def paintlight(self):
        # size the clock
        size = 0.9
        #
        lat = 38.54040
        lng = -121.73917
        tz = -7

        sunrise, sunset = sun.sunCalc(lat, lng, tz)

        riseAngle = pi/2. - (pi/12.)*sunrise
        setAngle = pi/2. - (pi/12.)*sunset
        while riseAngle < 0:
            riseAngle+=2*pi
        while setAngle < 0:
            setAngle+=2*pi
        nightSize = (setAngle+(2.*pi-np.absolute(riseAngle-setAngle)))
        daySize = (riseAngle-setAngle)

        ############################################################
        # determine if it is daytime or nightttime                 #
        T = datetime.timetuple(datetime.utcnow()-self.delta)       #
        x,x,x,h,m,s,x,x,x = T                                      #
        self.root.title('%02i:%02i:%02i' %(h,m,s))                 #
        angle = pi/2. - pi/12. * (h + m/60.0) # pi/12 is one hour  #
        if (angle>riseAngle) and (angle<setAngle):                 #
            self.daytime=True                                      #
        else:                                                      #
            self.daytime=False                                     #
        ############################################################

        arc = self.canvas.create_arc
        # night
        arc(self.T.windowToViewport(-size,-size,size,size), start=(riseAngle*180./pi), extent=(nightSize*180./pi), fill = "navy", tag=self._ALL)
        # day
        arc(self.T.windowToViewport(-size,-size,size,size), start=(setAngle*180./pi), extent=(daySize*180./pi), fill = "sky blue", tag=self._ALL)
        #scl = self.canvas.create_line
        #hrs24 = np.linspace(0,2*pi,200)
        #for i in hrs24:
        #    # daytime
        #    if ( (i < riseAngle) and (i > setAngle) ):
        #        scl(self.T.windowToViewport(0,0,(cos(i)*hrSz),(sin(i)*hrSz)), fill = "sky blue", tag=self._ALL, width = self.pad/5)
        #    # nighttime
        #    else:
        #        scl(self.T.windowToViewport(0,0,(cos(i)*hrSz),(sin(i)*hrSz)), fill = "navy", tag=self._ALL, width = self.pad/5)
    def painthours(self):
        fontsize = str(int(self.pad/1.4))
        hourfont = tkFont.Font(family="Century Schoolbook L", weight="bold",slant="italic",size=fontsize)
        placement = 0.79
        start = pi/2              # 24h is at pi/2
        step = pi/12              # 2*pi = step*24
        hours = ["12","1","2","3","4","5","6","7","8","9","10","11","12","1","2","3","4","5","6","7","8","9","10","11"]
        for i in range(24):       # draw the hour ticks as circles
            angle =  start-i*step
            x, y = cos(angle)*placement,sin(angle)*placement
            coords,junkcoords = self.T.windowToViewport(x,y,0,0)
            self.canvas.create_text(coords[0],coords[1],text=hours[i],fill=self.hourcolor,font=hourfont)

    ## Redraws the whole clock.
    # 
    def redraw(self):
        self.canvas.delete(ALL)   # erase the whole canvas
        self.paintlight()         # draw daytime/nighttime color background
        self.painthours()         # draw hour text
        #FIXME#self.canvas.delete(self._ALL)  # delete selected elements
        self.painthms()           # draw the handles
        if not self.showImage:
           self.paintcircle(0,0,0.01,self.timecolor)  # draw a circle at the centre of the clock

    ## Animates the clock, by redrawing everything after a certain time interval. 
    #
    def poll(self):
        self.redraw()
        self.root.after(200,self.poll) # run thread 5x per second
   
    def weather(self):
        print("checking weather...")
        with open('forecast.json') as json_data:
            f = json.load(json_data)
            #pprint(f)
        # look at forecast file
        # if age of forecast file is > 1hr:
        #   fetch weather
        #   put info in self object for clock thread to display
        # check weather every hour = 60*60*1000 ms
        self.root.after(60*60*1000,self.weather) # run thread every hour
    
    def display(self):
        lastActivityMs = int( ( str(subprocess.check_output(["xprintidle"])) ).strip() )
        activityTimeout = 5*60*1000 
        #if self.daytime:
        #    os.system("xset dpms force on")
        #else:
        #    if (lastActivityMs < activityTimeout):
        #        os.system("xset dpms force off")
        #self.root.after(2*60*1000,self.poll) # run thread every 2 minutes

## Main program for testing.
#
#  @param argv time zone, image background flag,
#         clock width, clock height, create thread flag.
#
def main(argv=None):
    if argv is None:
       argv = sys.argv
    if len(argv) > 2:
       try:
           deltahours = int(argv[1])
           sImage = (argv[2] == 'True')
           w = int(argv[3])
           h = int(argv[4])
           threading = (argv[5] == 'True')
       except ValueError:
           print ("A timezone is expected.")
           return 1
    else:
       deltahours = 7
       sImage = True  
       w = h = 650
       threading = True

    root = Tk()
    root.geometry ('+0+0')
    # deltahours: how far are you from utc?
    # Sometimes the clock may be run from another timezone ...
    clock(root,deltahours,sImage,w,h,threading)
    '''
    tz = -7
    lng = 38.54040
    lat = -121.73917
    solarnoon,sunrise,sunset = sun.calcSun(tz,lng,lat)
    print("Sunrise: "+str(sunrise))
    print("Solar noon: "+str(solarnoon))
    print("Sunset: "+str(sunset))
    '''

    root.mainloop()

if __name__=='__main__':
    sys.exit(main())
