"""
this GEE script extracts GPM and MODIS LST data for given sample locations
projection: geo lat/lon
"""
import ee
import datetime
from eehelper.common import *
from logger import Logger


def filter_coll(coll,
                year=None,
                startjulian=None,
                endjulian=None):
    """
    Method to filter an ee.ImageCollection object by date and AOI
    :param coll: ee.ImageCollection()
    :param year:
    :param startjulian:
    :param endjulian:
    :return: ee.ImageCollection
    """
    return ee.ImageCollection(coll).filterDate(ee.Date.fromYMD(year, 1, 1),
                                               ee.Date.fromYMD(year, 12, 31)) \
        .filter(ee.Filter.calendarRange(startjulian,
                                        endjulian))


def composite(coll,
              multiplier=1.0,
              reduce_type='average',
              aoi=None):
    """
    Function to reduce a given collection
    :param coll:ee.ImageCollection()
    :param multiplier: image multiplier
    :param reduce_type: options: average, total, rms, diag
    :param aoi: area of interest
    :return:
    """
    coll_ = ee.ImageCollection(coll).map(lambda x: x.multiply(ee.Image(multiplier)))

    if reduce_type == 'average':
        return ee.ImageCollection(coll_).reduce(ee.Reducer.mean()).clip(aoi)
    elif reduce_type == 'total':
        return ee.ImageCollection(coll_).reduce(ee.Reducer.sum()).clip(aoi)
    elif reduce_type == 'rms':
        coll__ = ee.ImageCollection(coll_).map(lambda x: ee.Image(x).multiply(ee.Image(x)))
        return ee.Image(coll__.reduce(ee.Reducer.mean())).sqrt().clip(aoi)
    elif reduce_type == 'diag':
        coll__ = ee.ImageCollection(coll_).map(lambda x: ee.Image(x).multiply(ee.Image(x)))
        return ee.Image(coll__.reduce(ee.Reducer.sum())).sqrt().clip(aoi)
    else:
        raise ValueError('Not Implemented')


def lst_band_properties_scale(lst_img,
                              band='LST_Day_1km'):
    """
    Scaling MODIS LST and adding system:time_start property
    :param lst_img: MODIS LST image
    :param band:
    :return:
    """
    out_img = lst_img.select([band]).copyProperties(lst_img)
    return out_img


if __name__ == '__main__':

    ee.Initialize()

    folder = "/home/temp/"
    Handler(dirname=folder).dir_create()

    logfile = folder + \
        'gee_precip_data_extract_v{}.log'.format(datetime.datetime.now().isoformat()
                                                 .split('.')[0].replace('-', '_').replace(':', '_'))

    log = Logger('GEE',
                 filename=logfile,
                 stream=True)

    log.lprint('Logfile: {}'.format(logfile))

    samp = ee.FeatureCollection("users/xxxx/shapefiles/ALL_coordinates").getInfo()

    gpm = ee.ImageCollection("NASA/GPM_L3/IMERG_V06")
    lst = ee.ImageCollection("MODIS/006/MOD11A1")

    log.lprint(EEFunc.expand_image_meta(lst.first().getInfo()))

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
    lst_daily = lst.map(lst_band_properties_scale)

    # spatial scale
    export_scale = 1000

    # print and check
    first_meta = gpm.first().getInfo()
    log.lprint(EEFunc.expand_image_meta(first_meta))

    # print and check
    first_meta = lst_daily.first()
    log.lprint(EEFunc.expand_image_meta(first_meta))

    # print and check
    log.lprint(EEFunc.expand_feature_coll_meta(samp))

    log.lprint('----------****----------------')

    # iterate thru all years and months
    for year in years:
        for month, days in julian_days:

            log.lprint('Date: {}-{}-XX'.format(str(year), str(month).upper()))

            str_id = 'y{}_{}_'.format(str(year), str(month))

            # create collections
            gpm_precip_coll = filter_coll(gpm_precip, year, days[0], days[1])
            gpm_error_coll = filter_coll(gpm_error, year, days[0], days[1])
            lst_coll = filter_coll(lst_daily, year, days[0], days[1])

            # obtain number of available images
            n_gpm = gpm_precip_coll.size().getInfo()
            n_lst = lst_coll.size().getInfo()

            log.lprint('GPM images: {} | LST images: {}'.format(str(n_gpm), str(n_lst)))

            # create image composite to export
            if n_gpm > 0 and n_lst > 0:

                data_img = ee.Image(composite(gpm_precip_coll, 0.5, 'total').select([0], [str_id + 'precipMM'])
                                    .addBands(composite(gpm_error_coll,  0.5, 'diag').select([0], [str_id + 'precipErrDiagMM']))
                                    .addBands(composite(gpm_error_coll,  0.5, 'rms').select([0], [str_id + 'precipErrRMSMM']))
                                    .addBands(composite(lst_coll,  0.02, 'average').select([0], [str_id + 'lstK'])))\
                                   .clip(aoi)

                # export image metadata
                log.lprint(EEFunc.expand_image_meta(data_img.getInfo()))

                # export task metadata
                task_config = {
                    'driveFileNamePrefix': str_id + '_data_img',
                    'crs': 'EPSG:4326',
                    'scale': export_scale,
                    'maxPixels': 1e13,
                    'fileFormat': 'GeoTIFF',
                    'region': aoi_coords,
                    'driveFolder': drive_folder
                }

                # define task
                task1 = ee.batch.Export.image(data_img,
                                              str_id + 'data_img',
                                              task_config)

                # begin task
                task1.start()
                log.lprint(task1)

            log.lprint('----------****----------------')






