#!/usr/bin/python3

import sys
import numpy as np
import re

class Pwscf:

    def __init__(self, filename=None):
        self.control    = {}
        self.system     = {}
        self.electrons  = {}
        self.atypes      = {}
        self.atoms       = []
        self.cell_parameters = []

        self.ktype = "automatic"
        self.kpoints = [1,1,1]
        self.shiftk = [0,0,0]
        self.klist = []

        self.set_pwscf_default()

        if filename:
            self.read(filename)


    def __del__(self):
        print("Destroy class PwscfIn")

    def set_pwscf_default(self):
        self.control['calculation']  = 'scf'
        self.control['restart_mode'] = None
        self.control['prefix']       = 'test'
        self.control['pseudo_dir']   = './'
        self.control['outdir']       = '\'./\''
        self.control['wf_collect']   = None
        self.control['tprnfor']      = None

        self.system['ibrav']        = None
        self.system['celldm(1)']    = None
        self.system['celldm(2)']    = None
        self.system['celldm(3)']    = None
        self.system['nat']          = 0
        self.system['ntyp']         = 0
        self.system['nbnd']         = None
        self.system['ecutwfc']      = float(30.0)
        self.system['force_symmorphic'] = None
        self.system['occupations']  = None

        self.electrons['mixing_mode']     = None
        self.electrons['mixing_beta']     = None
        self.electrons['conv_thr']        = float(1E-7)
        self._kpoints           = [0,0,0,0,0,0]

        self.cell_units      = 'bohr'
        self.atomic_pos_type = 'bohr'

    def write(self,filename):
        f = open(filename,'w')
        f.write(str(self))
        f.close()


    def stringify_group(self, keyword, group):
        string='&%s\n' % keyword
        for keyword in group:
            if group[keyword] != None:
                string += "%20s = %s\n" % (keyword, group[keyword])
        string += "/&end\n"
        return string


    def __str__(self):
        string=''
        string += self.stringify_group("control",self.control)
        string += self.stringify_group("system",self.system)
        string += self.stringify_group("electrons",self.electrons)

        if int(self.system['ibrav']) == 0:
            string += self.write_cell_parameters()

        string += self.write_atomicspecies()
        string += self.write_atoms()
        string += self.write_kpoints()
        return string

    def read_atomicspecies(self):
        lines = iter(self.file_lines)
        for line in lines:
            if "ATOMIC_SPECIES" in line:
                for i in range(int(self.system["ntyp"])):
                    atype, mass, psp = next(lines).split()
                    self.atypes[atype] = [mass,psp]

    def write_atomicspecies(self):
        string = "ATOMIC_SPECIES\n"
        for atype in self.atypes:
            string += " %3s %8s %20s\n" % (atype, self.atypes[atype][0], self.atypes[atype][1])
        return string

    def read_atoms(self):
        lines = iter(self.file_lines)
        atomicp_pattern=r'\s*ATOMIC_POSITIONS\s*\{?\s*(\w*)\s*\}?'
        for line in lines:
            if re.search(atomicp_pattern, line):
                match = re.search(atomicp_pattern, line)
                self.atomic_pos_type = match.group(1).lower()
                for i in range(int(self.system["nat"])):
                    atype, x,y,z = next(lines).split()
                    self.atoms.append([atype,[float(i) for i in x,y,z]])

    def write_atoms(self):
        string = "ATOMIC_POSITIONS { %s }\n"%self.atomic_pos_type
        for atom in self.atoms:
            string += "%3s %14.10lf %14.10lf %14.10lf\n" % (atom[0], atom[1][0], atom[1][1], atom[1][2])
        return string

    def read_cell_parameters(self):
        cellp_pattern  =r'\s*CELL_PARAMETERS\s*\{?\s*(\w*)\s*\}?'
        self.cell_parameters = [[1,0,0],[0,1,0],[0,0,1]]
        ibrav = int(self.system['ibrav'])
        if ibrav == 0:
            if 'celldm(1)' in self.system.keys():
                a = float(self.system['celldm(1)'])
            else:
                a = 1
            lines = iter(self.file_lines)
            for line in lines:
                if re.search(cellp_pattern, line):
                    match = re.search(cellp_pattern, line)
                    self.cell_units = match.group(1)
                    for i in range(3):
                        self.cell_parameters[i] = [ float(x)*a for x in lines.next().split() ]
        elif ibrav == 4:
            a = float(self.system['celldm(1)'])
            c = float(self.system['celldm(3)'])
            self.cell_parameters = [[   a,          0,  0],
                                    [-a/2,sqrt(3)/2*a,  0],
                                    [   0,          0,c*a]]
        elif ibrav == 2:
            a = float(self.system['celldm(1)'])
            self.cell_parameters = [[ -a/2,   0, a/2],
                                    [    0, a/2, a/2],
                                    [ -a/2, a/2,   0]]
        else:
            print 'ibrav = %d not implemented'%ibrav
            exit(1)

    def write_cell_parameters(self):
        string = "CELL_PARAMETERS { %s }\n"%self.cell_units
        for i in range(3):
            string += ("%14.10lf "*3+"\n")%tuple(self.cell_parameters[i])
        return string

    def read_namelist(self,group):
        for line in self.file_lines:
            if "="  not in line:
                continue
            key, value=line.split("=")
            for keyword in group:
                if key.strip().lower() == keyword:
                    group[keyword] = value.strip().strip(',')

    def read(self, filename):
        ifile = open(filename,'r')
        self.file_lines=ifile.readlines()

        self.read_namelist(self.control)
        self.read_namelist(self.system)
        self.read_namelist(self.electrons)

        self.read_cell_parameters()
        self.read_atomicspecies()
        self.read_atoms()
        self.read_kpoints()

        ifile.close()


    def read_kpoints(self):
        lines = iter(self.file_lines)
        #find K_POINTS keyword in file and read next line
        for line in lines:
            if "K_POINTS" in line:
                #chack if the type is automatic
                if "automatic" in line.lower():
                    self.ktype = "automatic"
                    vals = map(float, lines.next().split())
                    self.kpoints, self.shiftk = vals[0:3], vals[3:6]
                #otherwise read a list
                elif "gamma" in line.lower():
                    self.ktype = "gamma"
                else:
                    #read number of kpoints
                    nkpoints = int(lines.next().split()[0])
                    self.klist = []
                    self.ktype = ""
                    try:
                        lines_list = list(lines)
                        for n in range(nkpoints):
                            vals = lines_list[n].split()[:4]
                            self.klist.append( map(float,vals) )
                    except IndexError:
                        print "wrong k-points list format"
                        exit(1)

    def write_kpoints(self):
        string = "K_POINTS { %s }\n"%self.ktype
        if self.ktype == "automatic":
            string += ("%3d"*6+"\n")%tuple(self.kpoints + self.shiftk)
        elif self.ktype == "crystal" or self.ktype == "tpiba" :
            string += "%d\n" % len(self.klist)
            for i in self.klist:
              string += ('%12.8lf '*4+'\n') % tuple(i)
        return string


    def get_atoms(self, units):
        from utilities import ang2au,au2ang
        from lattice   import red2car,car2red
        atoms= np.array([atom[1] for atom in self.atoms])

        if units == self.atomic_pos_type:
            return atoms

        if self.atomic_pos_type == "angstrom":
            atoms = atoms*ang2au
        elif self.atomic_pos_type == "alat":
            atoms = atoms*float(self.system['celldm(1)'])
        elif self.atomic_pos_type == "crystal":
            atoms = red2car(atoms, np.array(self.cell_parameters))


        if units == "bohr":
            return atoms
        elif units == "alat":
            return atoms/float(self.system['celldm(1)'])
        elif units == "crystal":
            return car2red(units, np.array(self.cell_parameters))

    def set_atoms(self, new_atoms, units):
        new_atoms_list=new_atoms.to_list()
        for atom,new_atom in self.atoms, new_atoms_list:
            atom[1]=new_atom
        self.atomic_pos_type = units

