#!/usr/bin/python3
#
# Copyright (c) 2017-2018, E. Cannuccia and C. Attaccalite
# All rights reserved.
#
# Calculate thermal lines on single phonon modes or 
# on linear combination of the different phonons
#

from QEplayground.pwscf  import *
from QEplayground.matdyn import *
from QEplayground.pwout  import *
from QEplayground.units  import autime2s,amu2au,thz2cm1
import math

def single_mode_thermal_line(qe_input, qe_dyn, modes):

    masses=qe_input.get_masses()
    ref_mass=max(masses)
    M       =1.0/(np.sum(np.reciprocal(masses)))
    M       =M*float(qe_input.system['nat'])

    string="\n\n* * * Frozen phonon calculations * * *\n\n"
    string+="Reference  mass : %12.8f \n" % ref_mass
    string+="Reduced    mass : %12.8f [ref_mass units]  %12.8f  [amu]\n" % (M/ref_mass,M )

    print(string)

    # convert Mass to a.u.
    M       =M*amu2au

    # output reader
    qe_output=Pwout(qe_input)

    scf_filename="scf.in"

    #Equilibrium calculation
#    folder="EQUIL"
#    qe_input.run(scf_filename,folder)
#    qe_output.read_output(scf_filename+".log", path=folder)
#    en_equil=qe_output.tot_energy

    # DFTP results
    eig = np.array(qe_dyn.eig)

    print("\n")

    for im in modes:

        w_atom_units=eig[0,im]*(2.0*math.pi)/thz2cm1*autime2s*1e12

        delta=1.0/np.sqrt(2.0*w_atom_units)

        print("\nDisplacement mode %d = %12.8f a.u." % (im+1,delta))

        qe_dyn.print_atoms_sigma(0,im, delta)

#        qe_right=qe_dyn.generate_displacement(0, im,  delta)
#        qe_left =qe_dyn.generate_displacement(0, im, -delta)
        #
        folder="LEFT_"+str(im)
#        qe_left.run(scf_filename,folder)
#        qe_output.read_output(scf_filename+".log", folder)
#        en_left=qe_output.tot_energy
        #
        folder="RIGHT_"+str(im)
#        qe_right.run(scf_filename,folder)
#        qe_output.read_output(scf_filename+".log", folder)
#        en_right=qe_output.tot_energy
