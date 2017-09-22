#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = ("Helder")
__version__ = ("0.1")
__url__ = ('http://williams.best.vwh.net/sunrise_sunset_algorithm.htm')
# original URL dead, code hosted at:
# https://gist.github.com/ankithaldar/c759ea7ae8e3b264ed3c

#imports
PY3=True
from math import floor, ceil, pi, atan, tan, sin, asin, cos, acos
from datetime import timedelta, datetime
import sys
#   script imports
#imports

def dayOfYear(d,m,y):
    return(floor(275.*m/9.) - (floor((m+9.)/12.) * (1.+floor((y-4.*floor(y/4.)+2.)/3.))) + d - 30.)

def timeDate(date):
    return(timedelta(seconds = date*3600))

def sunCalc(lat, lng, td_utc):
    d2r = pi/180.
    
    # make time
    T = datetime.timetuple(datetime.utcnow()+timedelta(hours=td_utc))
    yr,mn,dy,h,m,s,x,x,x = T
    print yr, mn, dy, h, m, s
    doy = dayOfYear(dy,mn,yr)
    
    #
    # SUNRISE
    #

    #convert the longitude to hour value and calculate an approximate time
    lngH = lng/15.
    t = doy + (6. - lngH)/24.

    #m => Sun's mean anomaly
    m = (0.9856 * t) - 3.289
    
    #l => Sun's true longitude
    l = m + (1.916 * sin(m*d2r)) + (0.020 * sin(2 * m*d2r)) + 282.634
    l +=  -360 if l > 360 else 360 if l < 360 else 0
    
    #ra = Sun's right ascension (right ascension value needs to be in the same quadrant as L)
    ra = atan(0.91764 * tan(l*d2r))/d2r
    ra +=  -360 if ra > 360 else 360 if ra < 360 else 0
    ra += (floor(l/90) - floor(ra/90)) * 90
    ra /= 15

    #sinDec, cosDec => Sine and Cosine of Sun's declination
    sinDec = 0.39782 * sin(l*d2r)
    cosDec = cos(asin(sinDec))

    #Sun's local hour angle
    cosH = (cos(90.8333333333333*d2r) - (sinDec * sin(lat*d2r))) / (cosDec * cos(lat*d2r))
    if cosH > 1: print('the sun never rises on this location (on the specified date)'); sys.exit()
    h = (360 - (acos(cosH)/d2r))/15
    
    #Local mean time of rising/setting
    meanT = h + ra - (0.06571 * t) - 6.622

    #adjust back to local standard time
    sunriseLocal = meanT - lngH + td_utc
    sunriseLocal += 24 if sunriseLocal < 0 else -24 if sunriseLocal > 24 else 0
    
    #
    # SUNSET
    #

    #convert the longitude to hour value and calculate an approximate time
    lngH = lng/15.
    t = doy + (18. - lngH)/24.

    #m => Sun's mean anomaly
    m = (0.9856 * t) - 3.289
    
    #l => Sun's true longitude
    l = m + (1.916 * sin(m*d2r)) + (0.020 * sin(2 * m*d2r)) + 282.634
    l +=  -360 if l > 360 else 360 if l < 360 else 0
    
    #ra = Sun's right ascension (right ascension value needs to be in the same quadrant as L)
    ra = atan(0.91764 * tan(l*d2r))/d2r
    ra +=  -360 if ra > 360 else 360 if ra < 360 else 0
    ra += (floor(l/90) - floor(ra/90)) * 90
    ra /= 15

    #sinDec, cosDec => Sine and Cosine of Sun's declination
    sinDec = 0.39782 * sin(l*d2r)
    cosDec = cos(asin(sinDec))

    #Sun's local hour angle
    cosH = (cos(90.8333333333333*d2r) - (sinDec * sin(lat*d2r))) / (cosDec * cos(lat*d2r))
    if cosH < -1: print('the sun never sets on this location (on the specified date)'); sys.exit()
    h = (acos(cosH)/d2r)/15
    
    #Local mean time of rising/setting
    meanT = h + ra - (0.06571 * t) - 6.622

    #adjust back to local standard time
    sunsetLocal = meanT - lngH + td_utc
    sunsetLocal += 24 if sunsetLocal < 0 else -24 if sunsetLocal > 24 else 0
    return sunriseLocal, sunsetLocal
    
if __name__ == '__main__':

    lat = 38.54040
    lng = -121.73917
    tz = -7

    sunrise, sunset = sunCalc(lat, lng, tz)
    lod = sunset - sunrise

    print("")
    print('Sunrise: {}'.format(timeDate(sunrise)))
    print('Sunset: {}'.format(timeDate(sunset)))
    print('Length of day: {}'.format(timeDate(lod)))
    print("")
    print('Sunrise: '+str(sunrise))
    print('Sunset: '+str(sunset))
    print('Length of day: '+str(lod))
