
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 21 13:25:39 2020

@author: blahblahmac
"""

from astropy import wcs
from astropy.io import fits
import numpy as np
import os
import pickle
from astropy.stats import SigmaClip
from photutils import StdBackgroundRMS
import random
import statistics
from mpi4py import MPI

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

inp = np.load('nparray/input.npy')
#loading ra and dec from input saved by the dash app
ra = inp[0]
dec = inp[1]

#Getting the names of files
named = os.listdir('dat/dif/')
namep = os.listdir('dat/psf/')
#no  of images / processor
npo  = len(named)//size


#load file using astropy
def load(filename):
    
    # Load the FITS hdulist using astropy.io.fits
    hdulist = fits.open(filename)
    w = wcs.WCS(hdulist[1].header)
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
    return data, date, w, ga, fid, zp, uzp

# Function to perform photometry
def par(nr):
  
    data, date, w, ga, fid, zp, uzp = load('dat/dif/' + named[nr])
    datad = data[5:20,5:20]
    hdu = fits.open('dat/psf/' + namep[nr],mode='readonly', ignore_missing_end=True)
    hdu.verify('fix')
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
    
    mag1 = mag + 50000
    mag2 = mag - 50000
    
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
    
    return mag,sigp,sign,date,fid,mlim
            
    
    
comm.Barrier()

mag =[]
date= []
fid = []
no = []
sigp = []
sign = []
mlim = []

for i in range(rank*npo,(rank+1)*npo):
    
    try:            
        m, sp, sn, d, f, lim = par(i)
        mag.append(m)
        date.append(d)
        fid.append(f)
        no.append(i)
        sigp.append(sp)
        sign.append(sn)
        mlim.append(lim)
    except:
        continue
   
   
comm.Barrier()
data = comm.gather([mag,sigp,sign,date,fid,no,mlim], root=0)

if rank == 0:
    
    mag =[]
    sigp = []
    sign = []
    date= []
    fid = []
    no = []
    mlim = []

    for i in range(len(data)):
        
        temp = data[i]
        mag.append(temp[0])
        sigp.append(temp[1])
        sign.append(temp[2])
        date.append(temp[3])
        fid.append(temp[4])
        no.append(temp[5])
        mlim.append(temp[6])

    mag = [val for sublist in mag for val in sublist]
    sigp = [val for sublist in sigp for val in sublist]
    sign = [val for sublist in sign for val in sublist]
    date = [val for sublist in date for val in sublist]
    fid = [val for sublist in fid for val in sublist]
    no = [val for sublist in no for val in sublist]
    mlim = [val for sublist in mlim for val in sublist]

    with open("nparray/mag.txt", "wb") as fp:  # Pickling
        pickle.dump(mag, fp)
    with open("nparray/date.txt", "wb") as fp:  # Pickling
        pickle.dump(date, fp)
    with open("nparray/sigp.txt", "wb") as fp:  # Pickling
        pickle.dump(sigp, fp)
    with open("nparray/sign.txt", "wb") as fp:  # Pickling
        pickle.dump(sign, fp)
    with open("nparray/no.txt", "wb") as fp:  # Pickling
        pickle.dump(no, fp)
    with open("nparray/fid.txt", "wb") as fp:  # Pickling
        pickle.dump(fid, fp)
    with open("nparray/mlim.txt", "wb") as fp:  # Pickling
        pickle.dump(mlim, fp)
