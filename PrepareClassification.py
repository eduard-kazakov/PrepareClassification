import gdal
import ogr
import sys
import numpy as np
from datetime import datetime
import dbf
import os
import glob

def PrepareClassification(input_classification_tif, classification_datetime, output_dir, ice_water_threshold=4):

    # To WGS84 tif
    ice_class_wgs84_tif_name = 'niersc_ice_class_' + classification_datetime.strftime('%Y%m%dT%H%M%S') + '.tif'
    cmd = 'gdalwarp -t_srs EPSG:4326 %s %s' % (input_classification_tif, os.path.join(output_dir,ice_class_wgs84_tif_name))
    print cmd
    os.system(cmd)


    # To edge WGS84 tif
    ice_edge_wgs84_tif_name = 'niersc_ice_edge_' + classification_datetime.strftime('%Y%m%dT%H%M%S') + '.tif'
    cmd = 'gdal_calc.py -A %s --outfile=%s --calc="A>%s"' % (os.path.join(output_dir,ice_class_wgs84_tif_name), os.path.join(output_dir,ice_edge_wgs84_tif_name), str(ice_water_threshold))
    print cmd
    os.system(cmd)

    # To ice_class vector
    ice_class_shp_name = 'niersc_ice_class_' + classification_datetime.strftime('%Y%m%dT%H%M%S') + '.shp'
    cmd = 'gdal_polygonize.py %s -f "ESRI Shapefile" %s Class' % (os.path.join(output_dir,ice_class_wgs84_tif_name), os.path.join(output_dir,ice_class_shp_name))
    print cmd
    os.system(cmd)

    # To ice_edge vector
    ice_edge_shp_temp_name = 'niersc_ice_edge_' + classification_datetime.strftime('%Y%m%dT%H%M%S') + '_temp.shp'
    ice_edge_shp_name = 'niersc_ice_edge_' + classification_datetime.strftime('%Y%m%dT%H%M%S') + '.shp'
    cmd = 'gdal_polygonize.py %s -f "ESRI Shapefile" %s DN' % (os.path.join(output_dir,ice_edge_wgs84_tif_name), os.path.join(output_dir,ice_edge_shp_temp_name))
    print cmd
    os.system(cmd)

    cmd = 'ogr2ogr -f "ESRI Shapefile" -where "DN=1" %s %s' % (os.path.join(output_dir,ice_edge_shp_name), os.path.join(output_dir,ice_edge_shp_temp_name))
    print cmd
    os.system(cmd)



    # Add DateTime attr
    print 'Adding DateTime attribute'
    ice_class_dbf_name = os.path.join(output_dir,ice_class_shp_name.split('.')[0] + '.dbf')
    ice_edge_dbf_name = os.path.join(output_dir, ice_edge_shp_name.split('.')[0] + '.dbf')
    ice_class_db = dbf.Table(ice_class_dbf_name)
    with ice_class_db:
        ice_class_db.add_fields('datetime C(100)')
        for record in ice_class_db:
            dbf.write(record, datetime=classification_datetime.strftime('%Y%m%dT%H%M%S'))

    ice_edge_db = dbf.Table(ice_edge_dbf_name)
    with ice_edge_db:
        ice_edge_db.add_fields('datetime C(100)')
        for record in ice_edge_db:
            dbf.write(record, datetime=classification_datetime.strftime('%Y%m%dT%H%M%S'))

    print 'deleting temp'
    temp_files = glob.glob(os.path.join(output_dir,'*temp*'))
    for temp_file in temp_files:
        os.remove(temp_file)