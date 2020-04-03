'''
Code to export Landsat image composites from GEE to google drive
'''


import ee
import math
from eehelper.eehelper import EEHelper

# function to make image collection
def make_ls(args):
    collection, elevation_image, elev_scale_factor, bounds, bands, \
        start_date, end_date, start_julian, end_julian, \
        pctl, index, unmask_val = args

    all_images1 = ee.ImageCollection(get_landsat_images(collection, bounds, start_date, end_date,
                                                        start_julian[0], end_julian[0]))

    all_images2 = ee.ImageCollection(get_landsat_images(collection, bounds, start_date, end_date,
                                                        start_julian[1], end_julian[1]))

    all_images3 = ee.ImageCollection(get_landsat_images(collection, bounds, start_date, end_date,
                                                        start_julian[2], end_julian[2]))

    img_season1 = ee.Image(add_suffix(maxval_comp_ndvi(all_images1, pctl, index).select(bands), '1'))\
        .unmask(unmask_val)

    img_season2 = ee.Image(add_suffix(maxval_comp_ndvi(all_images2, pctl, index).select(bands), '2'))\
        .unmask(unmask_val)

    img_season3 = ee.Image(add_suffix(maxval_comp_ndvi(all_images3, pctl, index).select(bands), '3'))\
        .unmask(unmask_val)

    slope = ee.Terrain.slope(elevation_image).multiply(elev_scale_factor)
    aspect = ee.Terrain.aspect(elevation_image)

    topo_image = elevation_image.addBands(slope).addBands(aspect).select([0, 1, 2],
                                                                         ['elevation', 'slope', 'aspect']).int16()

    return img_season1.addBands(img_season2).addBands(img_season3).addBands(topo_image).clip(bounds)


if __name__ == '__main__':

    ee.Initialize()

    # geometries begin -----------------------------------------------------------------------------------------------
    zone1 = ee.Geometry.Polygon(
        [[[-141.328125, 61.73152565113397],
          [-136.98804910875856, 61.55754198059565],
          [-130.25390625, 61.64816245852395],
          [-118.388671875, 61.64816245852392],
          [-109.775390625, 61.68987220045999],
          [-109.248046875, 79.88973717174639],
          [-124.8386769987568, 75.69839539226707],
          [-127.29971233251035, 73.05352679871419],
          [-127.76447139555012, 71.18241823975474],
          [-136.57574846816965, 69.76160143677127],
          [-141.416015625, 70.19999407534661]]])

    # geometries end -------------------------------------------------------------------------------------------------

    ls5 = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR")
    ls7 = ee.ImageCollection("LANDSAT/LE07/C01/T1_SR")
    ls8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR")

    elevation = ee.Image('USGS/GMTED2010')

    # collections end ----------------------------------------------------------------------------------------

    elev_scale_factor = 10000
    pctl = 50
    index = 'NDVI'
    unmask_val = -9999

    # season 1: spring
    startJulian1 = 90
    endJulian1 = 165

    # season 2: summer
    startJulian2 = 180
    endJulian2 = 240

    # season 3: fall
    startJulian3 = 255
    endJulian3 = 330

    # start year , end year , year
    years = {
        '1992': (1987, 1997),
        '2000': (1998, 2002),
        '2005': (2003, 2007),
        '2010': (2008, 2012),
        '2015': (2013, 2018)
    }

    # zone name, bounds
    zones = {
        'zone1': zone1,
        'zone2': zone2,
        'zone3': zone3,
        'zone4': zone4,
        'zone5': zone5,
    }

    internal_bands = ee.List(['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2', 'PIXEL_QA',
                              'RADSAT_QA', 'NDVI', 'NDWI', 'NBR', 'VARI', 'SAVI'])

    bands = ee.List(['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2',
                     'NDVI', 'NDWI', 'NBR', 'VARI', 'SAVI'])

    startJulian = [startJulian1, startJulian2, startJulian3]
    endJulian = [endJulian1, endJulian2, endJulian3]

    # static definitions end ----------------------------------------------------------------------------------------

    all_images = ls5.merge(ls7).merge(ls8)

    print(EEFunc.expand_image_meta(all_images.first()))

    for year, dates in years.items():

        startDate = ee.Date.fromYMD(dates[0], 1, 1)
        endDate = ee.Date.fromYMD(dates[1], 12, 31)

        for zone, bounds in zones.items():

            args = (all_images, elevation, elev_scale_factor, bounds, bands,
                    startDate, endDate, startJulian, endJulian,
                    pctl, index, unmask_val)

            output_img = ee.Image(make_ls(args))

            out_name = 'Median_SR_NDVI_' + zone + '_' + year

            task_config = {
                'driveFileNamePrefix': out_name,
                'crs': 'EPSG:4326',
                'scale': 30,
                'maxPixels': 1e13,
                'fileFormat': 'GeoTIFF',
                'region': bounds,
                'driveFolder': 'Median_SR_NDVI'
            }

            task1 = ee.batch.Export.image(output_img,
                                          out_name,
                                          task_config)

            task1.start()

