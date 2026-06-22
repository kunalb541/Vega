from astropy.io import ascii
import requests
from multiprocessing import Pool


data_url = "https://irsa.ipac.caltech.edu/ibe/data/ztf/products/sci"
ref_url = "https://irsa.ipac.caltech.edu/ibe/data/ztf/products/ref"
search_data_url = "https://irsa.ipac.caltech.edu/ibe/search/ztf/products/sci"
search_ref_url = "https://irsa.ipac.caltech.edu/ibe/search/ztf/products/ref"
search_region = str(60/3600)
cutout_size = '25'


def search(pos):

    payload = {"POS":pos, "SIZE":search_region, "INTERSECT":"CENTER", "CT":"ipac_table"}
    r = requests.get(search_data_url, params = payload)
    with open('./app/dat/delme.dat', 'wb') as f:
        f.write(r.content)


def download_ref(pos):
    
    payload = {"POS":pos, "SIZE":search_region, "INTERSECT":"CENTER", "CT":"ipac_table"}
    r = requests.get(search_ref_url, params = payload)
    open('./app/dat/delme.dat', 'wb').write(r.content)
    data = ascii.read('./app/dat/delme.dat', format='ipac', delimiter='|')
    fieldprefix = '000'
    paddedfield = '000'+ str(data['field'][0])
    filtercode = data['filtercode'][0]
    paddedccdid = str(data['ccdid'][0]).zfill(2)
    qid = str(data['qid'][0])
    refimg_fname = ref_url + '/' + fieldprefix +'/field'+paddedfield+'/'+filtercode+'/ccd'+paddedccdid+'/q'+qid+'/ztf_'+paddedfield+'_'+filtercode+'_c'+paddedccdid+'_q'+qid+'_refimg.fits'+ '?center={0}&size={1}asec'.format(pos,cutout_size)
    R = requests.get(refimg_fname)
    open('./app/dat/ref/{0}.fits'.format(refimg_fname.split('.fits')[0].split('/')[-1]),'wb').write(R.content)


def download_dif(dif):
    try:
        R = requests.get(dif)
        open('./app/dat/dif/{0}.fits'.format(dif.split('.fits')[0].split('/')[-1]), 'wb').write(R.content)
    except:
        pass
    


def download_psf(psf):
    try:  
        R = requests.get(psf)
        open('./app/dat/psf/{0}.fits'.format(psf.split('.fits')[0].split('/')[-1]), 'wb').write(R.content)
    except:
        pass


def download(ra,dec):

    pos = str(ra)+','+str(dec)
    download_ref(pos)
    search(pos)
    data = ascii.read('./app/dat/delme.dat', format='ipac', delimiter='|')
    d_names = []
    p_names = []

    for i in range(len(data)):

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
        d_names.append(difimg_fname)     

        psfimg_name = data_url + '/' + year + '/'+ month + day + '/' + fracday + '/ztf_' + filefracday + '_' + paddedfield + '_' + filtercode + '_c' + paddedccid + '_' + imgtypecode + '_q' + qid + '_' + suffix_2
        p_names.append(psfimg_name)
    
    with Pool(20) as mp_pool:
        mp_pool.map(download_dif, d_names)
    
    with Pool(20) as mp_pool:
        mp_pool.map(download_psf, p_names)
    
    