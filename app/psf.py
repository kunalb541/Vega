from astropy.io import fits
import numpy as np
import os
import pickle
from astropy.stats import SigmaClip
from photutils.background import StdBackgroundRMS
import random
import statistics

#Getting the names of files
named = os.listdir('../app/dat/dif/')
namep = os.listdir('../app/dat/psf/')

#load file using astropy
def load(filename):
    
    # Load the FITS hdulist using astropy.io.fits
    hdulist = fits.open(filename,ignore_missing_simple=True)
    data = hdulist[1].data
    date = hdulist[1].header['OBSMJD ']
    ga = hdulist[1].header['GAIN']
    fid = hdulist[1].header['FILTERID']
    
    if fid == 1:
        fid = 'g'
    if fid == 2:
        fid = 'r'
    if fid == 3:
        fid = 'i'
        
    zp = hdulist[1].header['MAGZP']
    uzp = hdulist[1].header['MAGZPUNC']
    hdulist.close()
    return data, date, ga, fid, zp, uzp


def par(nr):

    data, date, ga, fid, zp, uzp = load('./app/dat/dif/' + named[nr])
    datad = data[5:20,5:20]
    hdu = fits.open('./app/dat/psf/' + namep[nr])
    datap = hdu[0].data
    hdu.close()
    datap = datap[5:20,5:20]
    sigma_clip = SigmaClip(sigma=3.0)
    bkgrms = StdBackgroundRMS(sigma_clip)
    bkg = bkgrms.calc_background_rms(datad)
    
    datad = [item for sublist in datad for item in sublist]
    datap = [item for sublist in datap for item in sublist]
    datad = np.asarray(datad, dtype=np.float64)
    datap = np.asarray(datap, dtype=np.float64)
    temp = datad
    temp = np.where(temp<0.0,0.0,temp)
    temp = np.sqrt((temp/ga) + bkg**2)
    u = (datap*datad)/(temp**2)
    d = (datap**2/temp**2)
    mag = np.sum(u)/np.sum(d)
    
    mag1 = mag + 5000
    mag2 = mag - 5000
    
    tmag = [random.uniform(mag1, mag2) for _ in range(1000)]
    like = []


    for i in range(len(tmag)):
        
        l = (np.log(1/(np.sqrt(2*np.pi*temp**2))) - ((datad - (tmag[i]*datap))/(2*temp**2))**2)
        l = np.sum(l)        
        like.append(l)
        
    sig = statistics.stdev(like)
    
    fo = 10**(0.4*zp)
    sigfo = fo*np.log(10)*uzp/2.5

    fr = mag/fo
    sigr = np.sqrt((sig/fo)**2 + (mag*sigfo/fo**2)**2)  

    if fr > 3 * sigr:
    
        mag = -2.5*np.log10(fr)
        sigp = -2.5*np.log10(1-(sigr/fr))
        sign = 2.5*np.log10(1+(sigr/fr)) 
        mlim =  float("NAN")

    else:
    
        mlim = -2.5 * np.log10(5*sigr)
        mag = float("NAN")
        sigp = float("NAN")
        sign = float("NAN")
    
    return mag,sigp,sign,date,fid,mlim,nr

def psf():

    temp = []  
    for i in range(len(named)): 
        try:
            temp.append(par(i))
        except:
            continue

    mag =[]
    sigp = []
    sign = []
    date= []
    fid = []
    no = []
    mlim = []

    for i in temp:

            mag.append(i[0])
            sigp.append(i[1])
            sign.append(i[2])
            date.append(i[3])
            fid.append(i[4])
            mlim.append(i[5])
            no.append(i[6])
            print(mag)

    with open("../app/nparray/mag.txt", "wb") as fp:  # Pickling
        pickle.dump(mag, fp)
    with open("../app/nparray/date.txt", "wb") as fp:  # Pickling
        pickle.dump(date, fp)
    with open("../app/nparray/sigp.txt", "wb") as fp:  # Pickling
        pickle.dump(sigp, fp)
    with open("../app/nparray/sign.txt", "wb") as fp:  # Pickling
        pickle.dump(sign, fp)
    with open("../app/nparray/no.txt", "wb") as fp:  # Pickling
        pickle.dump(no, fp)
    with open("../app/nparray/fid.txt", "wb") as fp:  # Pickling
        pickle.dump(fid, fp)
    with open("../app/nparray/mlim.txt", "wb") as fp:  # Pickling
        pickle.dump(mlim, fp)

psf()