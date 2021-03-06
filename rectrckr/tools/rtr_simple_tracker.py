#!/usr/bin/python2.7
#coding: utf-8
import argparse
import code

import rectrckr
import rectrckr.lowlevel as lowlevel

import matplotlib as mpl
mpl.use( "agg" )
from pylab import *
import code

from rectrckr.kalman_filter import KalmanFilter

def main():

    parser = argparse.ArgumentParser(description='Initial rectangle localization.')
    parser.add_argument('input', type=argparse.FileType('r'))
    parser.add_argument('img_a', type=int)
    parser.add_argument('img_b', type=int)
    parser.add_argument('px', type=int)
    parser.add_argument('py', type=int)
    args = parser.parse_args()

    ## Initial position guess
    px, py = args.px, args.py

    ## Object that provides an interface to the images, and contains
    ## information such as the camera parameters
    ds = rectrckr.DataSource(args.input)

    img = ds.get_image(args.img_a)
    ## Extract edgels
    edges = img.extract_edgels(px,py)
    lx = (edges[1] - edges[0])/2
    ly = (edges[3] - edges[2])/2

    print px, py, lx, ly


    kalman = KalmanFilter()
    kalman.state = array([px,py,lx,ly,0,0,0,0])

    kalman.Mobser = array([
            [1,0,-1, 0,0,0,0,0],
            [1,0, 1, 0,0,0,0,0],
            [0,1, 0,-1,0,0,0,0],
            [0,1, 0, 1,0,0,0,0],
            ])

    new_data = array([
            50,150,100,200.0
            ])

    dt = 1.0

    ##
    import cProfile
    pr = cProfile.Profile()
    pr.enable()
    ##

    fig = figure(1)
    subplot(1,1,1)
    fig.tight_layout()

    log_zh = zeros((args.img_b-args.img_a,4))
    log_z = zeros((args.img_b-args.img_a,4))
    for k in range(args.img_b-args.img_a):

        print '--['+'%03d'%(k + args.img_a)+']' + 70 * '-'
        kalman.predict_state(dt)
        print 'pred st: ', kalman.state
        kalman.predict_observations()
        print 'pred obs:', kalman.z_hat

        img = ds.get_image(k + args.img_a)
        px,py = kalman.state[:2]
        zhat = copy(kalman.z_hat)
        new_data = img.extract_edgels(px,py)

        print 'measured:', new_data
        merr = norm(kalman.z_hat - new_data)
        print 'measurement error:', merr

        kalman.update_from_observations(new_data)
        print 'updt st:', kalman.state

        # ## Log predicted state and outputs
        log_zh[k] = zhat
        log_z[k] = new_data


    ##
    ## Plot image and the extracted edges
        cla()
        imshow(copy(img.img), cmap=cm.gray)
        plot(new_data[:2], [py,py], 'k--')
        plot([px,px], new_data[2:4], 'k--')

        plot(zhat[:2], [py,py], 'bo')
        plot([px,px], zhat[2:4], 'bo')
        plot(px,py, 'bs')

        plot(new_data[:2], [py,py], 'ro')
        plot([px,px], new_data[2:4], 'ro')
        plot(px,py, 'rs')

        axis([0,img.img.shape[1],img.img.shape[0],0])

        savefig(ds.get_output_path(k))

    ##
    pr.dump_stats('mycoutstats.profi')
    ##
    savetxt('zh.dat', log_zh)
    savetxt('z.dat', log_z)


    code.interact(local=locals())



if __name__ == '__main__':
    from rectrckr.tools import rtr_init
    rtr_init.main()
