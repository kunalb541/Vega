#!/bin/sh
cd ~/Desktop/Vega-master
rm nparray/*txt*
rm dat/dif/*
rm dat/psf/*
rm dat/ref/*
mpiexec -n 4 python3 download.py
mpiexec -n 4 python3 psf.py


