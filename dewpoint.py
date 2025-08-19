# Version 1.0 released by David Romps on April 15, 2021.
# 
# When using this code, please cite:
# 
# @article{20dewpoint,
#   Title   = {Accurate expressions for the dew point and frost point derived from the {Rankine-Kirchhoff} approximations},
#   Author  = {David M. Romps},
#   Journal = {Journal of the Atmospheric Sciences},
#   Year    = {2021},
#   Month   = jul,
#   Number  = {7},
#   Pages   = {2113--2116},
#   Volume  = {78}
# }
#
# This dew-point function returns the dewpoint (Td) in K.
# The inputs are:
# - p in Pascals
# - T in Kelvins
# - Exactly one of rh, rhl, and rhs (dimensionless, from 0 to 1):
#    * The value of rh is interpreted to be the relative humidity with
#      respect to liquid water if T >= 273.15 K and with respect to ice if
#      T < 273.15 K. 
#    * The value of rhl is interpreted to be the relative humidity with
#      respect to liquid water
#    * The value of rhs is interpreted to be the relative humidity with
#      respect to ice
# - return_fp is an optional logical flag.  If true, the frost point (Tf)
#   is returned instead of the dew point (Td). 
# - return_max_dp_fp is an optional logical flag.  If true, the maximum of the
#   dew point (Td) and frost point (Tf) is returned.

def dewpoint(T,rh=None,rhl=None,rhs=None,return_fp=False,return_max_dp_fp=False):

   import math
   import scipy.special

   # Parameters
   Ttrip = 273.16     # K
   ptrip = 611.65     # Pa
   E0v   = 2.3740e6   # J/kg
   E0s   = 0.3337e6   # J/kg
   ggr   = 9.81       # m/s^2
   rgasa = 287.04     # J/kg/K 
   rgasv = 461        # J/kg/K 
   cva   = 719        # J/kg/K
   cvv   = 1418       # J/kg/K 
   cvl   = 4119       # J/kg/K 
   cvs   = 1861       # J/kg/K 
   cpa   = cva + rgasa
   cpv   = cvv + rgasv

   # The saturation vapor pressure over liquid water
   def pvstarl(T):
      return ptrip * (T/Ttrip)**((cpv-cvl)/rgasv) * \
         math.exp( (E0v - (cvv-cvl)*Ttrip) / rgasv * (1/Ttrip - 1/T) )
   
   # The saturation vapor pressure over solid ice
   def pvstars(T):
      return ptrip * (T/Ttrip)**((cpv-cvs)/rgasv) * \
         math.exp( (E0v + E0s - (cvv-cvs)*Ttrip) / rgasv * (1/Ttrip - 1/T) )

   # Calculate pv from rh, rhl, or rhs
   rh_counter = 0
   if rh  is not None:
      rh_counter = rh_counter + 1
   if rhl is not None:
      rh_counter = rh_counter + 1
   if rhs is not None:
      rh_counter = rh_counter + 1
   if rh_counter != 1:
      print(rh_counter)
      exit('Error in dewpoint: Exactly one of rh, rhl, and rhs must be specified')
   if rh is not None:
      # The variable rh is assumed to be 
      # with respect to liquid if T > Ttrip and 
      # with respect to solid if T < Ttrip
      if T > Ttrip:
         pv = rh * pvstarl(T)
      else:
         pv = rh * pvstars(T)
      rhl = pv / pvstarl(T)
      rhs = pv / pvstars(T)
   elif rhl is not None:
      pv = rhl * pvstarl(T)
      rhs = pv / pvstars(T)
      if T > Ttrip:
         rh = rhl
      else:
         rh = rhs
   elif rhs is not None:
      pv = rhs * pvstars(T)
      rhl = pv / pvstarl(T)
      if T > Ttrip:
         rh = rhl
      else:
         rh = rhs

   # Calculate Td and Tf
   aL = -(cpv-cvl)/rgasv
   bL = -(E0v-(cvv-cvl)*Ttrip)/(rgasv*T)
   cL = bL/aL
   Td = T*cL/scipy.special.lambertw((pv/pvstarl(T))**(1/aL)*cL*math.exp(cL),-1).real
   aS = -(cpv-cvs)/rgasv
   bS = -(E0v+E0s-(cvv-cvs)*Ttrip)/(rgasv*T)
   cS = bS/aS
   l1 = math.log(pv/pvstars(T))/aS + math.log(cS) + cS
   if rh == 0:
      Tf = 0
   elif l1 < 709:
      Tf = T*cS/scipy.special.lambertw((pv/pvstars(T))**(1/aS)*cS*math.exp(cS),0).real
   else:
      l2 = math.log(l1)
      Tf = T*cS/(l1-l2+l2/l1+l2*(-2+l2)/(2*l1**2)+l2*(6-9*l2+2*l2**2)/(6*l1**3)+l2*(-12+36*l2-22*l2**2+3*l2**3)/(12*l1**4))

   # Return either Td or Tf
   if return_fp and return_max_dp_fp:
      exit('return_fp and return_max_dp_fp cannot both be true')
   elif return_fp:
      return Tf
   elif return_max_dp_fp:
      return max(Td,Tf)
   else:
      return Td