#!/usr/bin/env python
__doc__ = """

Jingpeng Wu <jingpeng.wu@gmail.com>, 2015
"""
import numpy as np
import pyznn
import emirt
import time
import matplotlib.pylab as plt
# parameters
ftrn = "../dataset/ISBI2012/data/original/train-volume.tif"
flbl = "../dataset/ISBI2012/data/original/train-labels.tif"
fnet_spec = '../networks/srini2d.znn'
# learning rate
eta = 0.01
# momentum
momentum = 0

# output size
outsz = np.asarray([1,20,20])
# number of threads
num_threads = 7

# prepare input
vol = emirt.io.imread(ftrn).astype('float32')
lbl = emirt.io.imread(flbl).astype('float32')
# normalize the training volume
vol = vol / 255
lbl = (lbl>0.5).astype('float32')

print "output volume size: {}x{}x{}".format(outsz[0], outsz[1], outsz[2])
net = pyznn.CNet(fnet_spec, outsz[0],outsz[1],outsz[2],num_threads)
net.set_eta( eta / float(outsz[0] * outsz[1] * outsz[2]) )
net.set_momentum( momentum )

# compute inputsize and get input
fov = np.asarray(net.get_fov())
print "field of view: {}x{}x{}".format(fov[0],fov[1], fov[2])
insz = fov + outsz - 1

err = 0;
cls = 0;
# get gradient
from front_end import get_sample
from cost_fn import square_loss
plt.ion()
plt.show()

start = time.time()
for i in xrange(1,1000000):
    vol_in, lbl_out = get_sample( vol, insz, lbl, outsz )
    
    # forward pass
    prop = net.forward(np.ascontiguousarray(vol_in))
    
    # cost function and accumulate errors
    cerr, ccls, grdt = square_loss( prop, lbl_out )  
    err = err + cerr
    cls = cls + ccls   
    
    if i%1000==0:
        err = err / float(1000 * outsz[0] * outsz[1] * outsz[2]) 
        cls = cls / float(1000 * outsz[0] * outsz[1] * outsz[2])
        
        # time
        elapsed = time.time() - start
        print "iteration %d,    sqerr: %.3f,    clserr: %.3f,   elapsed: %.1f s"\
                %(i, err, cls, elapsed)
        # real time visualization
        norm_prop = emirt.volume_util.norm(prop)   
        norm_lbl_out = emirt.volume_util.norm( lbl_out )
        abs_grdt = np.abs(grdt)

        plt.subplot(221),   plt.imshow(vol_in[0,:,:],   cmap='gray')
        plt.xlabel('input')
        plt.subplot(222),   plt.imshow(norm_prop[0,:,:],    interpolation='nearest', cmap='gray')
        plt.xlabel('inference')
        plt.subplot(223),   plt.imshow(norm_lbl_out[0,:,:], interpolation='nearest', cmap='gray')
        plt.xlabel('lable')
        plt.subplot(224),   plt.imshow(abs_grdt[0,:,:],     interpolation='nearest', cmap='gray')
        plt.xlabel('gradient')
        plt.pause(1)
        
        # reset time
        start = time.time()
        # reset err and cls
        err = 0
        cls = 0
           
    # run backward pass    
    net.backward( np.ascontiguousarray(grdt) )

        
#%% visualization
#com = emirt.show.CompareVol((vol_in, lbl_out))
#com.vol_compare_slice()