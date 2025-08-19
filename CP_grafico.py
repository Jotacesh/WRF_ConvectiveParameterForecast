import xarray as xr
import pandas as pd

# ----- Seccion para permitir ingreso de variable fuera del codigo -----
# example: python promedios_mensuales.py --var SRH_500m_LM
import argparse
parser = argparse.ArgumentParser(description='Define la fecha de inicializacion del pronostico gfs')
parser.add_argument('--var', type=str, default="20250729", help='Fecha en formato yyyymmdd')
args = parser.parse_args()

# Usar la variable
var = args.var
print(f'Fecha de inicializacion: {var}')

fecha=var
ds=xr.open_dataset(rf'/home/cr2/jcampos/WRF_simulation/wrf_GFS/wrf_forecast_{fecha}/CP_wrfout_{fecha}.nc')
lat=ds.lat.values; lon=ds.lon.values; CP=ds.ConvectiveParameters; time=pd.to_datetime(ds.time.values)
CP=ds.ConvectiveParameters

import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
import imageio.v2 as imageio

time_dim = CP.shape[0]


# Crear carpeta temporal para imagenes
output_folder = "temp_frames"
os.makedirs(output_folder, exist_ok=True)

# indices de los niveles a graficar
niveles = [0, 3, 9, 11]
# rangos de las colorbar para cada viarbale
rangos=[[50,500],[10,24],[-400,-100],[-0.5,-0.01]]
names=["MUCAPE", "BS_01km", "SRH500m_LM", "STP"]
units=["[J/kg]", "[m/s]", "[m2/s2]", ""]

step=1
filenames = []

for t in range(time_dim):
    fig, axes = plt.subplots(2, 2, figsize=(8, 8), dpi=200, subplot_kw={'projection': ccrs.PlateCarree()})
    fig.suptitle(f"Convective Parameters - GFS forecast \n init: {time[0].strftime('%Y-%m-%dT%H:%M:%S')} -- f{t*step:03} \n valid_time: {time[t].strftime('%Y-%m-%dT%H:%M:%S')}", fontsize=16)
    axes = axes.flatten()
    for i in range(4):
        ax = axes[i]
        ax.coastlines(resolution='10m')
        gl=ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        ax.set_extent([-85,-65,-46,-25])
        gl.top_labels=False
        gl.right_labels=False
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        ax.plot(lon[:, 0], lat[:, 0], color='red', transform=ccrs.PlateCarree(),label='Dominio WRF (9km)')
        # Parte derecha
        ax.plot(lon[:, -1], lat[:, -1], color='red', transform=ccrs.PlateCarree())
        # Parte inferior
        ax.plot(lon[0, :], lat[0, :], color='red', transform=ccrs.PlateCarree())
        # Parte superior
        ax.plot(lon[-1, :], lat[-1, :], color='red', transform=ccrs.PlateCarree())
        data = CP[t, :, :, niveles[i]]
        if i in [0, 1]:
            vmin, vmax = rangos[i][0], rangos[i][1]
            im = ax.contourf(lon, lat, data, cmap='jet', levels=np.linspace(vmin,vmax,11), extend='max')
        elif i in [2, 3]:
            vmin, vmax = rangos[i][0], rangos[i][1]
            im = ax.contourf(lon, lat, data, cmap='jet_r',levels=np.linspace(vmin,vmax,11), extend='min')
        #cnt=ax.contour(lon,lat,ds.mslp[t,:,:]/100, colors='k',alpha=0.4, linewidths=0.6 )
        #ax.clabel(cnt,fontsize=7)
        ax.legend()
        cbar = fig.colorbar(im, ax=ax, orientation='vertical')
        cbar.set_label(f"{names[i]} {units[i]}")
    filename = os.path.join(output_folder, f"frame_{t:03d}.png")
    plt.savefig(filename)
    filenames.append(filename)
    plt.close()
    print(t)

dest_folder=f"/home/cr2/jcampos/WRF_simulation/wrf_GFS/wrf_forecast_{fecha}"
with imageio.get_writer(f"{dest_folder}/CP_wrf-forecast_{fecha}.gif", mode='I', fps=1) as writer:
    for filename in filenames:
        image = imageio.imread(filename)
        writer.append_data(image)

# Eliminar imagenes temporales (opcional)
for filename in filenames:
    os.remove(filename)
os.rmdir(output_folder)
