"""
this GEE script extracts GPM and MODIS LST data for given sample locations
projection: geo lat/lon
"""
import ee
import os
import datetime
from eehelper.eehelper import EEHelper


if __name__ == '__main__':

    ee.Initialize()

    helper = EEHelper()

    folder = "/home/temp/"
    os.makedirs(folder)

    # spatial scale
    export_scale = 1000

    gpm = ee.ImageCollection("NASA/GPM_L3/IMERG_V06")
    lst = ee.ImageCollection("MODIS/006/MOD11A1")

    print(EEHelper.expand_image_meta(lst.first().getInfo()))

    drive_folder = 'precip_temp_output'

    # coordinates for area of interest
    aoi_coords = [[[-150.85512251110526, 67.15679295750088],
                   [-150.85512251110526, 63.089354508791175],
                   [-141.71449751110526, 63.089354508791175],
                   [-141.71449751110526, 67.15679295750088]]]

    aoi_geom = {'type': 'Polygon', 'coordinates': aoi_coords}

    aoi = ee.Geometry.Polygon(aoi_coords, None, False)

    # julian days for all months
    julian_days = [['jan', (1, 31)],
                   ['feb', (32, 59)],
                   ['mar', (60, 90)],
                   ['apr', (91, 120)],
                   ['may', (121, 151)],
                   ['jun', (152, 181)],
                   ['jul', (182, 212)],
                   ['aug', (213, 243)],
                   ['sep', (244, 273)],
                   ['oct', (274, 304)],
                   ['nov', (305, 334)],
                   ['dec', (335, 365)]]

    years = list(range(2000, 2020))

    # important bands in GPM dataset
    gpm_precip = gpm.select(['precipitationCal'])
    gpm_error = gpm.select(['randomError'])

    # modify LST data set, select band and radiometric scale
    lst_daily = lst.map(EEHelper.band_with_properties)

    # print and check
    first_meta = gpm.first().getInfo()
    print(EEHelper.expand_image_meta(first_meta))

    # print and check
    first_meta = lst_daily.first()
    print(EEHelper.expand_image_meta(first_meta))

    print('----------****----------------')

    # iterate thru all years and months
    for year in years:
        for month, days in julian_days:

            print('Date: {}-{}-XX'.format(str(year), str(month).upper()))

            str_id = 'y{}_{}_'.format(str(year), str(month))

            # create collections
            gpm_precip_coll = helper.get_images(gpm_precip, year=year, start_julian=days[0], end_julian=days[1])
            gpm_error_coll = helper.get_images(gpm_error, year=year, start_julian=days[0], end_julian=days[1])
            lst_coll = helper.get_images(lst_daily, year=year, start_julian=days[0], end_julian=days[1])

            # obtain number of available images
            n_gpm = gpm_precip_coll.size().getInfo()
            n_lst = lst_coll.size().getInfo()

            print('GPM images: {} | LST images: {}'.format(str(n_gpm), str(n_lst)))

            # create image composite to export
            if n_gpm > 0 and n_lst > 0:

                helper.scale_factor = 0.5
                helper.composite_function = 'sum'
                gpm_precip_composite = helper.composite_image(gpm_precip_coll,
                                                              band_selector=[0],
                                                              band_names=['precipMM'])

                helper.composite_function = 'rms'
                gpm_precip_error_composite = helper.composite_image(gpm_precip_coll,
                                                                    band_selector=[0],
                                                                    band_names=['precipErrRMSMM'])

                helper.composite_function = 'mean'
                helper.scale_factor = 0.02
                lst_composite = helper.composite_image(lst_coll,
                                                       band_selector=[0],
                                                       band_names=['lstK'])

                data_img = ee.Image(gpm_precip_composite)\
                    .addBands(gpm_precip_error_composite)\
                    .addBands(lst_composite)\
                    .clip(aoi)

                # export image metadata
                print(EEHelper.expand_image_meta(data_img.getInfo()))

                helper.export_image_to_drive(data_img,
                                             folder=drive_folder,
                                             scale=export_scale,
                                             region=aoi_coords,
                                             crs='EPSG:4326',
                                             verbose=True)

            print('----------****----------------')
