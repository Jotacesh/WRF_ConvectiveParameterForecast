#!/bin/bash

source ~/.bashrc
conda activate data-science
fecha=`date +%Y%m%d`

cd /home/cr2/jcampos/WRF_simulation/wrf_GFS/

python get_GFS_forecast.py --var ${fecha} #esto genera las condiciones iniciales cada 6 horas

#crea carpeta de simulacion con archivos basicos y donde se generará el wrfout
folder_name=wrf_forecast_${fecha}
mkdir ${folder_name}
cd ${folder_name}
# la carpeta tendrá de nombre la fecha de simulacion
mkdir ${fecha}
cp /home/cr2/jcampos/WRF_simulation/Basico/* /home/cr2/jcampos/WRF_simulation/wrf_GFS/${folder_name}/${fecha}/
cd ${fecha}

# modificar namelist.wps
# ----- MODIFICA RUTAS DE OUTPUTS ----------
namelist_file="/home/cr2/jcampos/WRF_simulation/wrf_GFS/${folder_name}/${fecha}/namelist.wps"

output1="opt_output_from_geogrid_path = '/home/cr2/jcampos/WRF_simulation/wrf_GFS/${folder_name}/${fecha}/',"
output2="opt_output_from_metgrid_path =  '/home/cr2/jcampos/WRF_simulation/wrf_GFS/${folder_name}/${fecha}/',"
sed -i "s|opt_output_from_geogrid_path = '/home/cr2/jcampos/WRF_simulation/SOOACH/',|${output1}|" "${namelist_file}"
sed -i "s|opt_output_from_metgrid_path = '/home/cr2/jcampos/WRF_simulation/SOOACH/',|${output2}|" "${namelist_file}"
sed -i "s|dx.*|dx = 9000,|" "${namelist_file}"
sed -i "s|dy.*|dy = 9000,|" "${namelist_file}"

# ------ MODIFICA FECHA DE INICIO Y FIN --------
start_date=$(date -d "`date +%Y%m%d`" +%Y-%m-%d_%H:%M:%S)
end_date=$(date -d "`date +%Y%m%d` +3 days" +%Y-%m-%d_%H:%M:%S)

sed -i "s|start_date.*|start_date='${start_date}',|" "${namelist_file}"
sed -i "s|end_date.*|end_date='${end_date}',|" "${namelist_file}"

# ----- MODIFICA INICIO Y FIN EN NAMELIST.INPUT
namelist_file="/home/cr2/jcampos/WRF_simulation/wrf_GFS/${folder_name}/${fecha}/namelist.input"

start_year=$(date -d "`date +%Y%m%d`" +%Y)
start_month=$(date -d "`date +%Y%m%d`" +%m)
start_day=$(date -d "`date +%Y%m%d`" +%d)

end_year=$(date -d "`date +%Y%m%d` +3 days" +%Y)
end_month=$(date -d "`date +%Y%m%d` +3 days" +%m)
end_day=$(date -d "`date +%Y%m%d` +3 days" +%d)

sed -i "s|start_year.*|start_year               = ${start_year},|" "${namelist_file}"
sed -i "s|start_day.*|start_day                = ${start_day},|" "${namelist_file}"
sed -i "s|start_month.*|start_month              = ${start_month},|" "${namelist_file}"
sed -i "s|end_year.*|end_year               = ${end_year},|" "${namelist_file}"
sed -i "s|end_day.*|end_day                = ${end_day},|" "${namelist_file}"
sed -i "s|end_month.*|end_month              = ${end_month},|" "${namelist_file}"
# editar parametros de tamaño de celda y niveles verticales
sed -i "s|dx.*|dx = 9000,|" "${namelist_file}"
sed -i "s|dy  .*|dy = 9000,|" "${namelist_file}"
sed -i "s|e_vert.*|e_vert = 55,|" "${namelist_file}"
sed -i "s|num_metgrid_levels .*|num_metgrid_levels       = 34,|" "${namelist_file}"
# editar fisicas
sed -i "s|mp_physics.*|mp_physics = 8,|" "${namelist_file}"
sed -i "s|ra_lw_physics.*|ra_lw_physics = 4,|" "${namelist_file}"
sed -i "s|ra_sw_physics.*|ra_sw_physics = 4,|" "${namelist_file}"
sed -i "s|bl_pbl_physics.*|bl_pbl_physics = 5,|" "${namelist_file}"
sed -i "s|cu_physics.*|cu_physics = 2,|" "${namelist_file}"
sed -i "s|num_soil_layers.*|num_soil_layers = 4,|" "${namelist_file}"

# ------ Ejecuta WRF ejecutables
ml icc/2019.2.187-GCC-8.2.0-2.31.1  impi/2019.2.185
ml WPS/4.2-dmpar
ml WRF/4.1.3-dmpar

./geogrid.exe
cp /home/cr2/jcampos/TEST_WRF/WPS-4.2/ungrib/Variable_Tables/Vtable.GFS Vtable
./link_grib.csh /home/cr2/jcampos/WRF_simulation/wrf_GFS/init_GFS_files/${fecha}_t00/*
./ungrib.exe
./metgrid.exe

./real.exe

# ejecuta wrf en sbatch
sbatch /home/cr2/jcampos/WRF_simulation/wrf_GFS/wrf_forecast_${fecha}/${fecha}/lanza-wrf.sh

echo "Se comenzó a ejecutar la simulación de WRF"
sleep 3600s # pausa el script por 1 hora

# Bucle de comprobación de que terminó la simulación
while true; do
    if [ -f rsl.error.0000 ]; then #comprueba la existencia del archivo, si no existe, le asigna a count el valor 0.
        count=$(grep -c 'SUCCESS COMPLETE WRF' rsl.error.0000)
    else
        count=0
    fi

    if [ "$count" -eq 1 ]; then
        echo "El archivo contiene 'SUCCESS COMPLETE WRF'. La simulación terminó de ejecutarse. Continuando..."
        break
    else
        sleep 15m # si aun no está el archivo, o si aún no termina la simulación, que se vuelva a comprobar en otros 15 minutos
    fi
done


mv wrfout* wrfout_${fecha}.nc



echo "Cálculo de parámetros convectivos a partir de salida de WRF"
python /home/cr2/jcampos/WRF_simulation/wrf_GFS/wrf_ConvectiveParameters.py --var ${fecha} # calcula parametros convectivos
python /home/cr2/jcampos/WRF_simulation/wrf_GFS/CP_grafico.py --var ${fecha} # genera gif

rm wrfout_${fecha}.nc
