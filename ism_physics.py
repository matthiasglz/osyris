#=======================================================================================
#This file is part of OSIRIS.

#OSIRIS is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#OSIRIS is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with OSIRIS.  If not, see <http://www.gnu.org/licenses/>.
#=======================================================================================

from load_ramses_data import get_binary_data
import config_osiris as conf
import numpy as np
import struct
from scipy.interpolate import RegularGridInterpolator

#===================================================================================
# An empty container class which will be filled up as the EOS, opacity, resistivity
# tables are read.
#===================================================================================
class IsmTable():
    
    def __init__(self):
                
        return


#===================================================================================
# Generic function to interpolate simulation data onto opacity table
#===================================================================================
def ism_interpolate(table_container=None,values=[0],points=[0],in_log=False):
    
    func = RegularGridInterpolator(table_container.grid,values)
    
    if in_log:
        return func(points)
    else:
        return np.power(10.0,func(points))
    


#===================================================================================
# Function to read in binary file containing EOS table
#===================================================================================
def read_eos_table(fname="tab_eos.dat"):
    
    print("Loading EOS table: "+fname)
    
    # Read binary EOS file
    with open(fname, mode='rb') as eos_file:
        eosContent = eos_file.read()
    eos_file.close()
    
    # Define data fields. Note that the order is important!
    data_fields = ["rho_eos","ener_eos","temp_eos","pres_eos","s_eos","cs_eos","xH_eos","xH2_eos","xHe_eos","xHep_eos"]

    # Create table container
    theTable = IsmTable()
    
    # Initialise offset counters and start reading data
    ninteg = nfloat = nlines = nstrin = nquadr = 0
    
    # Get table dimensions
    [theTable.nRho,theTable.nEner] = get_binary_data(fmt="2i",content=eosContent,ninteg=ninteg,nlines=nlines,nfloat=nfloat)
    
    # Get table limits
    ninteg += 2
    nlines += 1
    [theTable.rhomin,theTable.rhomax,theTable.emin,theTable.emax,theTable.yHe] = \
        get_binary_data(fmt="5d",content=eosContent,ninteg=ninteg,nlines=nlines,nfloat=nfloat)
        
    array_size = theTable.nRho*theTable.nEner
    array_fmt  = "%id" % array_size
    nfloat += 5
    nlines += 1
    
    # Now loop through all the data fields
    for i in range(len(data_fields)):
        setattr(theTable,data_fields[i],np.reshape(get_binary_data(fmt=array_fmt,content=eosContent, \
                ninteg=ninteg,nlines=nlines,nfloat=nfloat),[theTable.nRho,theTable.nEner],order="F"))
        nfloat += array_size
        nlines += 1
    
    del eosContent
    
    theTable.grid = (np.log10(theTable.rho_eos[:,0]), np.log10(theTable.ener_eos[0,:]/theTable.rho_eos[0,:]))
        
    print("EOS table read successfully")

    return theTable


#===================================================================================
# Function to interpolate simulation data onto EOS table
#===================================================================================
def get_eos(holder,eos_fname="tab_eos.dat",variables=["temp_eos","pres_eos","s_eos","cs_eos","xH_eos","xH2_eos","xHe_eos","xHep_eos"]):
    
    if holder.info["eos"] == 0:
        print("Simulation data did not use a tabulated EOS. Exiting")
        return
    else:
        try:
            n = holder.eos_table.nRho
        except AttributeError:
            holder.eos_table = read_eos_table(fname=eos_fname)

        for var in variables:
            print("Interpolating "+var)
            #grid = (np.log10(holder.eos_table.rho_eos[:,0]), np.log10(holder.eos_table.ener_eos[0,:]/holder.eos_table.rho_eos[0,:]))
            #func = RegularGridInterpolator(holder.eos_table.grid, np.log10(getattr(holder.eos_table,var)))
            pts  = np.array([np.log10(holder.density.values), np.log10(holder.internal_energy.values)]).T
            
            #pts  = np.array([np.log10(holder.density.values),np.log10(holder.temperature.values),np.log10(holder.radiative_temperature.values)]).T
            vals = ism_interpolate(holder.eos_table,np.log10(getattr(holder.eos_table,var)),pts)
            
            holder.new_field(name=var,label=var,values=vals,verbose=False,norm=1.0)

    return







#===================================================================================
#===================================================================================
#===================================================================================

#===================================================================================
# Function to read in binary file containing opacity table
#===================================================================================
def read_opacity_table(fname="vaytet_grey_opacities3D.bin"):
    
    print("Loading opacity table: "+fname)
    
    # Read binary resistivity file
    with open(fname, mode='rb') as kappa_file:
        kappaContent = kappa_file.read()
    kappa_file.close()
    
    # Create table container
    theTable = IsmTable()
    
    # Initialise offset counters and start reading data
    ninteg = nfloat = nlines = nstrin = nquadr = 0
    
    # Get table dimensions
    [theTable.nx,theTable.ny,theTable.nz] = get_binary_data(fmt="3i",content=kappaContent)
    
    # Get table limits
    [theTable.dx,theTable.dy,theTable.dz,theTable.xmin,theTable.xmax,theTable.ymin,theTable.ymax,theTable.zmin,theTable.zmax] = \
        get_binary_data(fmt="9d",content=kappaContent,correction=12)
    
    # Read table coordinates:
    
    # x: density
    ninteg += 3
    nfloat += 9
    nlines += 1
    theTable.dens = get_binary_data(fmt="%id"%theTable.nx,content=kappaContent,ninteg=ninteg,nlines=nlines,nfloat=nfloat)
    
    # y: gas temperature
    nfloat += theTable.nx
    nlines += 1
    theTable.tgas = get_binary_data(fmt="%id"%theTable.ny,content=kappaContent,ninteg=ninteg,nlines=nlines,nfloat=nfloat)
    
    # z: radiation temperature
    nfloat += theTable.ny
    nlines += 1
    theTable.trad = get_binary_data(fmt="%id"%theTable.nz,content=kappaContent,ninteg=ninteg,nlines=nlines,nfloat=nfloat)
    
    # Now read opacities
    array_size = theTable.nx*theTable.ny*theTable.nz
    array_fmt  = "%id" % array_size
    
    #print theTable.nx,theTable.ny,theTable.nz
    
    # Planck mean
    nfloat += theTable.nz
    nlines += 1
    theTable.kappa_p = np.reshape(get_binary_data(fmt=array_fmt,content=kappaContent, \
                ninteg=ninteg,nlines=nlines,nfloat=nfloat),[theTable.nx,theTable.ny,theTable.nz],order="F")
    
    # Rosseland mean
    nfloat += array_size
    nlines += 1
    theTable.kappa_r = np.reshape(get_binary_data(fmt=array_fmt,content=kappaContent, \
                ninteg=ninteg,nlines=nlines,nfloat=nfloat),[theTable.nx,theTable.ny,theTable.nz],order="F")
    
    del kappaContent
    
    theTable.grid = (theTable.dens,theTable.tgas,theTable.trad)
    
    #print theTable.dens
    #print theTable.tgas
    #print theTable.trad
    
    
    print("Opacity table read successfully")
    
    return theTable


#===================================================================================
# Function to interpolate simulation data onto opacity table
#===================================================================================
def get_opacities(holder,opacity_fname="vaytet_grey_opacities3D.bin",variables=["kappa_p","kappa_r"]):
    
    
    try:
        n = holder.opacity_table.nx
    except AttributeError:
        holder.opacity_table = read_opacity_table(fname=opacity_fname)
    
    if not hasattr(holder,"radiative_temperature"):
        print("Radiative temperature is not defined. Computing it now.")
        holder.new_field(name="radiative_temperature",operation="(radiative_energy_1/"+str(conf.constants["a_r"])+")**0.25",label="Trad")

    for var in variables:
        print("Interpolating "+var)
        pts  = np.array([np.log10(holder.density.values),np.log10(holder.temperature.values),np.log10(holder.radiative_temperature.values)]).T
        vals = ism_interpolate(holder.opacity_table,getattr(holder.opacity_table,var),pts)
        holder.new_field(name=var,label=var,values=vals,verbose=False,norm=1.0)

    return



#===================================================================================
#===================================================================================
#===================================================================================

#===================================================================================
# Function to read in binary file containing resistivity table
#===================================================================================
def read_resistivity_table(fname="resnh.bin"):
    
    print("Loading resistivity table: "+fname)
    
    # Read binary resistivity file
    with open(fname, mode='rb') as res_file:
        resContent = res_file.read()
    res_file.close()
    
    # Create table container
    theTable = IsmTable()
    
    # Initialise offset counters and start reading data
    ninteg = nfloat = nlines = nstrin = nquadr = 0
    
    # Get length of record on first line to determine number of dimensions in table
    rec_size = get_binary_data(fmt="i",content=resContent,correction=-4)
    ndims = rec_size[0]/4
    
    print "ndims",ndims
    
    # Get table dimensions
    theTable.nx = np.roll(np.array(get_binary_data(fmt="%ii"%ndims,content=resContent)),1)
    print theTable.nx
    
    nx_read = np.copy(theTable.nx)
    
    if ndims == 3:
        nx_read[0] += 2
    elif ndims == 4:
        nx_read[0] += 7
    
    # Now read the bulk of the table containing abundances in one go
    ninteg += ndims
    nlines += 1
    resistivite_chimie_x = np.reshape(get_binary_data(fmt="%id"%(np.prod(nx_read)),content=resContent,ninteg=ninteg,nlines=nlines,nfloat=nfloat),nx_read,order="F")
    
    print "kk",theTable.nx,nx_read
    print resistivite_chimie_x[:,0,0]
    print np.shape(resistivite_chimie_x)
    
    # Now we compute conductivities ==========================
    
    # Define some constants ==================================
    
    #pi=3.1415927410125732422d0
    rg      = 0.1e-4       # grain radius 
    mp      = 1.6726e-24   # proton mass
    me      = 9.1094e-28   # electron mass
    mg      = 1.2566e-14   # grain mass
    e       = 4.803204e-10 # electron charge
    mol_ion = 29.0*mp      # molecular ion mass
    Met_ion = 23.5*mp      # atomic ion mass
    kb      = 1.3807e-16   # Boltzmann
    clight  = 2.9979250e+10
    #real(kind=8), parameter ::mH      = 1.6600000d-24
    #real(kind=8), parameter ::mu_gas = 2.31d0
    #real(kind=8) :: scale_d = mu_gas*mH
    rho_s      = 2.3
    rho_n_tot  = 1.17e-21
    a_0        = 0.0375e-4
    a_min      = 0.0181e-4
    a_max      = 0.9049e-4
    zeta       = a_min/a_max
    lambda_pow = -3.5
    
    # Compute grain distribution =============================
    
    if ndims == 3:
        nbins_grains = (theTable.nx[0]-7)/3
        nion = 7
    elif ndims == 4:
        nbins_grains = (theTable.nx[0]-9)/3
        nion = 9
    print 'nbins_grains',nbins_grains
    
    r_grains = np.zeros([nbins_grains])
       
    Lp1 = lambda_pow + 1.0
    Lp3 = lambda_pow + 3.0
    Lp4 = lambda_pow + 4.0
    fnb = float(nbins_grains)

    if nbins_grains == 1:
         r_grains[0] = a_0
    else:
        for i in range(nbins_grains):
            r_grains[i] = a_min*zeta**(-float(i+1)/fnb) * np.sqrt( Lp1/Lp3* (1.0-zeta**(Lp3/fnb))/(1.0-zeta**(Lp1/fnb)))


    q_res  = np.zeros([theTable.nx[0]])
    m_res  = np.zeros([theTable.nx[0]])
    mg_res = np.zeros([theTable.nx[0]])
    
    q_res[:] = e
    q_res[0] = -e
    if ndims == 3:
        qchrg = [e,-e,0.0]
        for i in range(nion,theTable.nx[0]):
            q_res[i] = qchrg[(i-7) % 3]               
    elif ndims == 4:
        qchrg = [0.0,e,-e]
        for i in range(nion,theTable.nx[0]):
            q_res[i] = qchrg[(i-8) % 3]               

    m_res[0] = me        # e-
    m_res[1] = 23.5*mp   # metallic ions
    m_res[2] = 29.0*mp   # molecular ions
    m_res[3] = 3.0*mp    # H3+
    m_res[4] = mp        # H+
    m_res[5] = 12.0*mp   # C+
    m_res[6] = 4.0*mp    # He+
    if ndims == 4:
        m_res[7] = 39.098*mp # K+
        m_res[8] = 22.990*mp # Na+
    for i in range(nbins_grains):
        mg_res[i] = 4.0/3.0*np.pi*r_grains[i]**3*rho_s
        m_res[nion+1+3*i:nion+1+3*(i+1)] = mg_res[i]
    
    
    print q_res
    print '======================='
    print m_res
    
    
    # Compute conductivities =============================
    
    # Define magnetic field range and resolution
    bminchimie = 1.0e-10
    bmaxchimie = 1.0e+10
    bchimie = 150
    #dbchimie=(np.log10(bmaxchimie)-np.log10(bminchimie))/float(bchimie-1)
    Barray = np.linspace(np.log10(bminchimie),np.log10(bmaxchimie),bchimie)
    
    nchimie = theTable.nx[1]
    tchimie = theTable.nx[2]
    if ndims == 3:
        xichimie = 1
        resistivite_chimie = np.zeros([4,nchimie,tchimie,bchimie])
    elif ndims == 4:
        xichimie = theTable.nx[3]
        resistivite_chimie = np.zeros([4,nchimie,tchimie,xichimie,bchimie])
    

    tau_sn      = np.zeros([theTable.nx[0]])
    omega       = np.zeros([theTable.nx[0]])
    sigma       = np.zeros([theTable.nx[0]])
    phi         = np.zeros([theTable.nx[0]])
    zetas       = np.zeros([theTable.nx[0]])
    gamma_zeta  = np.zeros([theTable.nx[0]])
    gamma_omega = np.zeros([theTable.nx[0]])
    omega_bar   = np.zeros([theTable.nx[0]])
   
    for iX in range(xichimie):
        for iB in range(bchimie):
            for iT in range(tchimie):
                for iH in range(nchimie):

                    B = Barray[iB]
                    if ndims == 3:
                        nh = resistivite_chimie_x[0,iH,iT]  # density (.cc) of current point
                        T  = resistivite_chimie_x[1,iH,iT]
                    elif ndims == 4:
                        nh = resistivite_chimie_x[0,iH,iT,iX]  # density (.cc) of current point
                        T  = resistivite_chimie_x[1,iH,iT,iX]
                        xi = resistivite_chimie_x[2,iH,iT,iX]
      
                    for i in range(nion):
                        if  i==0 : # electron
                            if ndims == 3:
                                sigv = 1.3e-9
                            elif ndims == 4:
                                sigv = 3.16e-11 * (np.sqrt(8.0*kb*1.0e-7*T/(np.pi*me*1.0e-3))*1.0e-3)**1.3
                            tau_sn[i] = 1.0/1.16*(m_res[i]+2.0*mp)/(2.0*mp)*1.0/(nH/2.0*sigv)
                        
                        else: # ions   
                        #elif (i>=1) and (i<nion): # ions
                            if ndims == 3:
                                sigv = 1.69e-9
                            elif ndims == 4:
                                muuu=m_res[i]*2.0*mp/(m_res[i]+2.0*mp)
                                if (i==1) or (i==2):
                                    sigv=2.4e-9 *(np.sqrt(8.0*kb*1.0e-7*T/(np.pi*muuu*1.0e-3))*1.0e-3)**0.6
                                elif i==3:
                                    sigv=2.0e-9 * (np.sqrt(8.0*kb*1.0e-7*T/(np.pi*muuu*1.0e-3))*1.0e-3)**0.15
                                elif i==4:
                                    sigv=3.89e-9 * (np.sqrt(8.0*kb*1.0e-7*T/(np.pi*muuu*1.0e-3))*1.0e-3)**(-0.02)
                                else:
                                    sigv=1.69e-9
                            tau_sn[i] = 1.0/1.14*(m_res[i]+2.0*mp)/(2.0*mp)*1.0/(nH/2.0*sigv)
                        
                        omega[i] = q_res[i]*B/(m_res[i]*clight)
                        if ndims == 3:
                            sigma[i] = resistivite_chimie_x[i+2,iH,iT]*nH*(q_res[i])**2*tau_sn[i]/m_res[i]
                        else:
                            sigma[i] = resistivite_chimie_x[i+3,iH,iT,iX]*nH*(q_res[i])**2*tau_sn[i]/m_res[i]
                        #phi[i] = 0.0
                        #zetas[i] = 0.0
                        gamma_zeta[i] = 1.0
                        gamma_omega[i] = 1.0
                        #omega_bar[i] = 0.0
                        
                    ## STOPPED HERE ===================
                        
                    #for  i in range(nbins_grains):
                        
      
        #tau_sn(nion+1+3*(i-1))= 1.d0/1.28d0*(m_g(i)+2.d0*mp)/(2.d0*mp)*1.d0/(nH/2.d0*(pi*r_g(i)**2*(8.d0*Kb*T/(pi*2.d0*mp))**0.5))
        #omega(nion+1+3*(i-1)) = q(nion+1+3*(i-1))*B/(m_g(i)*c_l)
        #sigma(nion+1+3*(i-1)) = resistivite_chimie_x(nion+1+3*(i-1),iH,iT,iX)*nH*(q(nion+1+3*(i-1)))**2*tau_sn(nion+1+3*(i-1))/m_g(i)
      
        #tau_sn(nion+2+3*(i-1))= tau_sn(nion+1+3*(i-1))
        #omega(nion+2+3*(i-1)) = q(nion+2+3*(i-1))*B/(m_g(i)*c_l)
        #sigma(nion+2+3*(i-1)) = resistivite_chimie_x(nion+2+3*(i-1),iH,iT,iX)*nH*(q(nion+2+3*(i-1)))**2*tau_sn(nion+2+3*(i-1))/m_g(i)
      
      #end do
            

      ###do i=1,nion
        ###if  (i==1) then  ! electron
          ###sigv=3.16d-11 * (dsqrt(8d0*kB*1d-7*T/(pi*me*1d-3))*1d-3)**1.3d0
          ###tau_sn(i) = 1.d0/1.16d0*(m(i)+2.d0*mp)/(2.d0*mp)*1.d0/(nH/2.d0*sigv)
        ###else if (i>=2 .and. i<=nion) then ! ions
          ###muuu=m(i)*2d0*mp/(m(i)+2d0*mp)
          ###if (i==2 .or. i==3) then
            ###sigv=2.4d-9 *(dsqrt(8d0*kB*1d-7*T/(pi*muuu*1d-3))*1d-3)**0.6d0
          ###else if (i==4) then
            ###sigv=2d-9 * (dsqrt(8d0*kB*1d-7*T/(pi*muuu*1d-3))*1d-3)**0.15d0
          ###else if (i==5) then
            ###sigv=3.89d-9 * (dsqrt(8d0*kB*1d-7*T/(pi*muuu*1d-3))*1d-3)**(-0.02d0)
          ###else
            ###sigv=1.69d-9
          ###end if
          ###tau_sn(i) = 1.d0/1.14d0*(m(i)+2.d0*mp)/(2.d0*mp)*1.d0/(nH/2.d0*sigv)
        ###end if
        ###omega(i) = q(i)*B/(m(i)*c_l)
        ###sigma(i) = resistivite_chimie_x(i,iH,iT,iX)*nH*(q(i))**2*tau_sn(i)/m(i)
        ###phi(i) = 0.d0
        ###zetas(i) = 0.d0
        ###gamma_zeta(i) = 1.d0
        ###gamma_omega(i) = 1.d0
        ###omega_bar(i) = 0.d0
      ###end do
      
      ##do  i=1,nbins_grains   ! grains
      
        ##tau_sn(nion+1+3*(i-1))= 1.d0/1.28d0*(m_g(i)+2.d0*mp)/(2.d0*mp)*1.d0/(nH/2.d0*(pi*r_g(i)**2*(8.d0*Kb*T/(pi*2.d0*mp))**0.5))
        ##omega(nion+1+3*(i-1)) = q(nion+1+3*(i-1))*B/(m_g(i)*c_l)
        ##sigma(nion+1+3*(i-1)) = resistivite_chimie_x(nion+1+3*(i-1),iH,iT,iX)*nH*(q(nion+1+3*(i-1)))**2*tau_sn(nion+1+3*(i-1))/m_g(i)
      
        ##tau_sn(nion+2+3*(i-1))= tau_sn(nion+1+3*(i-1))
        ##omega(nion+2+3*(i-1)) = q(nion+2+3*(i-1))*B/(m_g(i)*c_l)
        ##sigma(nion+2+3*(i-1)) = resistivite_chimie_x(nion+2+3*(i-1),iH,iT,iX)*nH*(q(nion+2+3*(i-1)))**2*tau_sn(nion+2+3*(i-1))/m_g(i)
      
      ##end do

      ##sigP=0.d0
      ##sigO=0.d0
      ##sigH=0.d0

      ##do i=1,nvarchimie
         ##sigP=sigP+sigma(i)
         ##sigO=sigO+sigma(i)/(1.d0+(omega(i)*tau_sn(i))**2)
         ##sigH=sigH-sigma(i)*omega(i)*tau_sn(i)/(1.d0+(omega(i)*tau_sn(i))**2)
      ##end do

      ##if(sigH==0d0) sigH=1d-30

      ##resistivite_chimie(1,iH,iT,iX,iB)=log10(sigP)
      ##resistivite_chimie(2,iH,iT,iX,iB)=log10(sigO)
      ##resistivite_chimie(3,iH,iT,iX,iB)=log10(abs(sigH))
      ##resistivite_chimie(0,iH,iT,iX,iB)=sign(1.0d0,sigH)
##end do
##end do
##end do
##end do

    
    
    ##print("Resistivity table read successfully")

    ##return theTable















#open(42,file='resnh.dat', status='old')
        #read(42,*) nchimie, tchimie, nvarchimie
        #read(42,*)
        #read(42,*)
        #allocate(resistivite_chimie_x(-1:nvarchimie,nchimie,tchimie,1))
        #do i=1,tchimie
           #do j=1,nchimie
              #read(42,*)resistivite_chimie_x(0:nvarchimie,j,i,1),dummy,dummy,dummy,dummy,resistivite_chimie_x(-1,j,i,1)
#!              print *, resistivite_chimie_x(:,j,i)
           #end do
           #read(42,*)
        #end do
        #close(42)
        #rho_threshold=max(rho_threshold,resistivite_chimie_x(0,1,1,1)*(mu_gas*mH)/scale_d) ! input in part/cc, output in code units
        #nminchimie=(resistivite_chimie_x(0,1,1,1))
        #dnchimie=(log10(resistivite_chimie_x(0,nchimie,1,1))-log10(resistivite_chimie_x(0,1,1,1)))/&
                 #&(nchimie-1)
#!                 print*, dnchimie,15.d0/50.d0
        #tminchimie=(resistivite_chimie_x(-1,1,1,1))
        #dtchimie=(log10(resistivite_chimie_x(-1,1,tchimie,1))-log10(resistivite_chimie_x(-1,1,1,1)))/&
                 #&(tchimie-1)
#!                 print*, dtchimie,3.d0/50.d0
#!         close(333)
        #call rq
        #call nimhd_3dtable
     #else if(use_x3d==1)then

        #open(42,file='marchand2016_table.dat',form='unformatted')
        #read(42) nchimie, tchimie, xichimie, nvarchimie
        #allocate(resistivite_chimie_x(-2:nvarchimie+4,nchimie,tchimie,xichimie))
        #read(42) resistivite_chimie_x
        #close(42)

        #rho_threshold=max(rho_threshold,resistivite_chimie_x(-2,1,1,1)*(mu_gas*mH)/scale_d) ! input in part/cc, output in code units
        #nminchimie=(resistivite_chimie_x(-2,1,1,1))
        #dnchimie=(log10(resistivite_chimie_x(-2,nchimie,1,1))-log10(resistivite_chimie_x(-2,1,1,1)))/&
                 #&(nchimie-1)
#!                 print*, dnchimie,15.d0/50.d0
        #tminchimie=(resistivite_chimie_x(-1,1,1,1))
        #dtchimie=(log10(resistivite_chimie_x(-1,1,tchimie,1))-log10(resistivite_chimie_x(-1,1,1,1)))/&
                 #&(tchimie-1)
#!                 print*, dtchimie,3.d0/50.d0
        #ximinchimie=(resistivite_chimie_x(0,1,1,1))
        #dxichimie=(log10(resistivite_chimie_x(0,1,1,xichimie))-log10(resistivite_chimie_x(0,1,1,1)))/&
                 #&(xichimie-1)
        #call rq_3d
        #call nimhd_4dtable
     #else
        #print*, 'must choose an input for abundances or resistivities'
        #stop
     #endif
