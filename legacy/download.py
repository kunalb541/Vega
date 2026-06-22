from astropy.io import ascii
import requests
import numpy as np
from mpi4py import MPI

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

inp = np.load('nparray/input.npy')
#loading ra and dec from input saved by the dash app
ra = inp[0]
dec = inp[1]

base_url = "https://irsa.ipac.caltech.edu/ibe/search/ztf/products/sci"
data_url = "https://irsa.ipac.caltech.edu/ibe/data/ztf/products/sci"
pos = str(ra)+','+str(dec)  # example ra and dec in degrees, separated by comma and no whitespace
search_region = str(60/3600) #60 arcsec in degrees
cutout_size = '25' #in arcsec
payload = {"POS":pos, "SIZE":search_region, "INTERSECT":"CENTER", "CT":"ipac_table"}
r = requests.get(base_url, params = payload)
comm.Barrier() 
open('dat/delme.dat', 'wb').write(r.content)
data = ascii.read('dat/delme.dat', format='ipac', delimiter='|')

#no  of images / processor
 
npo  = len(data)//size
comm.Barrier()
for i in range(rank*npo,(rank+1)*npo):
    
    filefracday = str(data['filefracday'][i])
    year = filefracday[0:4]
    month = filefracday[4:6]
    day = filefracday[6:8]
    fracday = filefracday[8:]
    paddedfield = str(data["field"][i]).zfill(6)
    filtercode = data['filtercode'][i]
    paddedccid = str(data['ccdid'][i]).zfill(2)
    imgtypecode = data['imgtypecode'][i]
    qid = str(data['qid'][i])
    suffix_1 = "scimrefdiffimg.fits.fz"
    suffix_2 = "diffimgpsf.fits"
   
    difimg_fname = data_url + '/' + year + '/'+ month + day + '/' + fracday + '/ztf_' + filefracday + '_' + paddedfield + '_' + filtercode + '_c' + paddedccid + '_' + imgtypecode + '_q' + qid + '_' + suffix_1 + '?center={0}&size={1}asec'.format(pos,cutout_size)      
    R = requests.get(difimg_fname)
    open('dat/dif/{0}.fits'.format(difimg_fname.split('.fits')[0].split('/')[-1]), 'wb').write(R.content)
   
    psfimg_name = data_url + '/' + year + '/'+ month + day + '/' + fracday + '/ztf_' + filefracday + '_' + paddedfield + '_' + filtercode + '_c' + paddedccid + '_' + imgtypecode + '_q' + qid + '_' + suffix_2
    R = requests.get(psfimg_name)
    open('dat/psf/{0}.fits'.format(psfimg_name.split('.fits')[0].split('/')[-1]), 'wb').write(R.content)
comm.Barrier()     

'''
if rank == 0:
    
    base_url = "https://irsa.ipac.caltech.edu/ibe/search/ztf/products/ref"
    data_url = "https://irsa.ipac.caltech.edu/ibe/data/ztf/products/ref"
    r = requests.get(base_url, params = payload)
    open('dat/delme.dat', 'wb').write(r.content)
    data = ascii.read('dat/delme.dat', format='ipac', delimiter='|')
    fieldprefix = '000'
    if len(str(data['field'][0]))>3:
        paddedfield = '000'+ str(data['field'][0])[1:]
    else:
        paddedfield = '000'+ str(data['field'][0])
    filtercode = data['filtercode'][0]
    paddedccdid = str(data['ccdid'][0]).zfill(2)
    qid = str(data['qid'][0])
    refimg_fname = data_url + '/' + fieldprefix +'/field'+paddedfield+'/'+filtercode+'/ccd'+paddedccdid+'/q'+qid+'/ztf_'+paddedfield+'_'+filtercode+'_c'+paddedccdid+'_q'+qid+'_refimg.fits'+ '?center={0}&size={1}asec'.format(pos,cutout_size) 
   
    R = requests.get(refimg_fname)
    open('dat/ref/{0}.fits'.format(refimg_fname.split('.fits')[0].split('/')[-1]),'wb').write(R.content)
'''
