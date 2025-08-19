# -*- coding: utf-8 -*-

#%% Este script es para calcular parametros convectivos a partir de las salidas de WRF
# Creado el 22-04-2025 - Javier Campos

import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from netCDF4 import Dataset
import xarray as xr
# importa librerias de wrf-python que se utilizaran: interplevel, getvar, latlon_coords, get_cartopy
from wrf import (getvar, to_np, interplevel, latlon_coords, get_cartopy)

# ----- Seccion para permitir ingreso de variable fuera del codigo -----
# example wrf_ConvectiveParameters.py --var 20250811    (fecha en formato yyyymmdd)
import argparse
parser = argparse.ArgumentParser(description='Define la fecha de inicializacion del pronostico gfs')
parser.add_argument('--var', type=str, default="20250729", help='Fecha en formato yyyymmdd')
args = parser.parse_args()

# Usar la variable
var = args.var
print(f'Fecha de inicializacion: {var}')

fecha=var # formato yyyymmdd

#%% leer archivos wrfout
w_ctrl=Dataset(rf"/home/cr2/jcampos/WRF_simulation/wrf_GFS/wrf_forecast_{fecha}/{fecha}/wrfout_{fecha}.nc")

#%% se cargan las variables utilizdas por R-ThundeR para cálculo de parámetros convectivos
t=getvar(w_ctrl, "temp", timeidx=None, units="degC").values #temperatura
speed,wdir=getvar(w_ctrl, "uvmet_wspd_wdir", timeidx=None, units="kt").values #velocidad y direccion
p=getvar(w_ctrl, "pressure", timeidx=None).values #presion    
td=getvar(w_ctrl, "td", timeidx=None, units="degC").values #temperatura de rocío
hgt_agl=getvar(w_ctrl, "height_agl", timeidx=None, units="m").values #altura sobre el nivel del terreno
lat,lon=latlon_coords(getvar(w_ctrl,'T2')) #latitud y longitud
times=getvar(w_ctrl,'times',timeidx=None)

# [1] MUCAPE [41] MLCAPE
# BS_500,1,2,3,6 [91,92,93,94,95] BSEFF_MU [101] BSEFF_ML [102]
# [130] SRH_500m_LM [131] SRH_1km_LM
# STP_new_LM [175] SHERBE [196]
# [8] MULCL_HGT [15] MULCL_TEMP [48] MLLCL_HGT [55] MLLCL_TEMP
# LR_500,1,2,3 [58,59,60,61] # LR_500700hPa [69]
# se busca máximo cape, bs y Lapse rate, mínimo SRH, STP, y LCL
# vector de indices formato python
# [0, 40, 90, 91, 92, 93, 94, 100, 101, 129, 130, 174, 195, 7, 14, 47, 54, 57, 58, 59, 60, 68]
#[0,2,9,11,17,21]
print('Empieza a calcular parametros convectivos')

# carga variables en superficie 
t_s=getvar(w_ctrl, "T2", timeidx=None).values-273.15 #temperatura
ws_s,wd_s=getvar(w_ctrl, "uvmet10_wspd_wdir", timeidx=None, units="kt").values #velocidad y direccion
p_s=getvar(w_ctrl, "PSFC", timeidx=None).values/100 #presion superficial en hPa    
td_s=getvar(w_ctrl, "td2", timeidx=None, units="degC").values #temperatura de rocío
from dewpoint import dewpoint
#----------------------------------------------------------------------
from joblib import Parallel, delayed
def compute_cp(k):
    from rpy2.robjects.packages import importr
    from rpy2.robjects import r,pandas2ri
    import rpy2.robjects as robjects
    pandas2ri.activate()
    importr('thunder')
    cp_slice=np.full((t.shape[2], t.shape[3], 22), np.nan)
    for i in range(t.shape[2]):
        for j in range(t.shape[3]):
            # agrega valores de superficie a los perfiles verticales.
            plev_f=np.concatenate([[p_s[k,i,j]],p[k,:,i,j]])
            H_f=np.concatenate([[0],hgt_agl[k, :, i, j]])
            T_f=np.concatenate([[t_s[k,i,j]],t[k, :, i, j]])
            Td_f=np.concatenate([[td_s[k,i,j]],td[k,:,i,j]])
            w_speed_f=np.concatenate([[ws_s[k,i,j]],speed[k, :, i, j]])
            w_dir_f=np.concatenate([[wd_s[k,i,j]],wdir[k, :, i, j]])
            cp_slice[i, j, :] = robjects.r['sounding_compute'](plev_f,
                H_f,T_f,Td_f, w_dir_f,w_speed_f,accuracy=2)[[0, 40, 90, 91, 92, 93, 94, 100, 101, 129, 130, 174, 7, 14, 47, 54, 57, 58, 59, 60, 68, 23]]
    return cp_slice
#%%

import time
init= time.time()
CP = Parallel(n_jobs=-1)(delayed(compute_cp)(t) for t in range(len(times))) # calcular los parametros convectivos para cada tiempo
CP=np.array(CP)
end=time.time()
print(f"Tiempo de ejecucion: {end-init} segundos")

print('Guardando CPs en un netcdf')
#%% guardar el resultado en un archivo
south_north = lat.shape[0]
west_east = lat.shape[1]
CP_da = xr.DataArray(
    CP,
    dims=['time', 'south_north', 'west_east', 'ParametroConvectivo'],
    coords={
        'time': times.values,
        'south_north': np.arange(south_north),
        'west_east': np.arange(west_east),
        'ParametroConvectivo': np.arange(22),
        'lat': (['south_north', 'west_east'], lat.values),
        'lon': (['south_north', 'west_east'], lon.values)
    }
)

ds = CP_da.to_dataset(name='ConvectiveParameters')
ds.to_netcdf(rf'/home/cr2/jcampos/WRF_simulation/wrf_GFS/wrf_forecast_{fecha}/CP_wrfout_{fecha}.nc')
print('Termino proceso correctamente')