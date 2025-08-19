#%%
import os
import requests

# Autor: Javier Campos Núñez 
# Fecha: 17-06-2025
# Descripción: Descarga pronósticos de GFS con las variables necesarias para calcular
# parámetros convectivos.

# Definir región
#lat_n = -30
#lat_s = -55
#lon_o = -85
#lon_e = -67
lat_n=-20
lat_s=-60
lon_o=-100
lon_e=-60
# ----- Seccion para permitir ingreso de variable fuera del codigo -----
# example: python promedios_mensuales.py --var SRH_500m_LM
import argparse
parser = argparse.ArgumentParser(description='Define la fecha de inicializacion del pronostico gfs')
parser.add_argument('--var', type=str, default="20250729", help='Fecha en formato yyyymmdd')
args = parser.parse_args()

# Usar la variable
var = args.var
print(f'Fecha de inicializacion: {var}')


# Definir fecha y parámetros
date = var  # formato yyyymmdd
init = "00"
res = "0p25"
fhour=f"{0:03d}"
# URL base
base_url = f"https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_{res}.pl?dir=%2Fgfs.{date}%2F{init}%2Fatmos&file=gfs.t{init}z.pgrb2.{res}.f{fhour}"
params_fixed = f"&var_DPT=on&var_MSLET=on&var_HGT=on&var_ICEC=on&var_ICETMP=on&var_PRMSL=on&var_ICMR=on&var_LAND=on&var_PRES=on&var_RH=on&var_SNMR=on&var_SNOD=on&var_SOILL=on&var_SOILW=on&var_SOTYP=on&var_SPFH=on&var_TMP=on&var_TSOIL=on&var_UGRD=on&var_VGRD=on&var_WEASD=on&lev_0-0.1_m_below_ground=on&lev_0.1-0.4_m_below_ground=on&lev_0.4-1_m_below_ground=on&lev_1-2_m_below_ground=on&lev_2_m_above_ground=on&lev_10_m_above_ground=on&lev_1000_mb=on&lev_975_mb=on&lev_950_mb=on&lev_925_mb=on&lev_900_mb=on&lev_850_mb=on&lev_800_mb=on&lev_750_mb=on&lev_700_mb=on&lev_650_mb=on&lev_600_mb=on&lev_550_mb=on&lev_500_mb=on&lev_450_mb=on&lev_400_mb=on&lev_350_mb=on&lev_300_mb=on&lev_250_mb=on&lev_200_mb=on&lev_150_mb=on&lev_100_mb=on&lev_70_mb=on&lev_50_mb=on&lev_40_mb=on&lev_30_mb=on&lev_20_mb=on&lev_15_mb=on&lev_10_mb=on&lev_7_mb=on&lev_5_mb=on&lev_3_mb=on&lev_2_mb=on&lev_1_mb=on&lev_0.7_mb=on&lev_0.4_mb=on&lev_0.2_mb=on&lev_0.1_mb=on&lev_0.07_mb=on&lev_0.04_mb=on&lev_0.02_mb=on&lev_0.01_mb=on&lev_surface=on&lev_max_wind=on&lev_mean_sea_level=on"

subregion = f"&subregion=&toplat={lat_n}&leftlon={lon_o}&rightlon={lon_e}&bottomlat={lat_s}"

# Crear carpeta destino
destino= f"init_GFS_files/{date}_t{init}"
os.makedirs(destino, exist_ok=True)
#%% Iterar sobre las horas de pronóstico con barra de progreso
import requests
from tqdm import tqdm
import os
# Definir paso y horas máximas
step = 6  # horas de pronóstico
max_hour = 96
# Iterar sobre las horas de pronóstico
for i in range(0, max_hour + 1, step):
    fhour = f"{i:03d}"
    file_param = f"&file=gfs.t{init}z.pgrb2.{res}.f{fhour}"
    url = base_url + file_param + params_fixed + subregion
    nombre_archivo = f"{destino}/gfs{res}_t{init}z_{date}_f{fhour}.grb2"

    # Saltar si ya existe
    if os.path.exists(nombre_archivo):
        print(f"{nombre_archivo} ya existe, saltando...")
        continue

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))

        with open(nombre_archivo, "wb") as f, tqdm(
            desc=f"Descargando f{fhour}",
            total=total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            ncols=80
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                bar.update(len(chunk))

    except Exception as e:
        print(f"Error al descargar f{fhour}: {e}")
#%% Fin del script
# Une GFS
