import ee
import sys
import math
import warnings


class EEHelper(object):
    """
    Helper class for Google Earth Engine python API scripts
    """
    def __init__(self,
                 const=0.5,
                 scale_factor=1,
                 index_list=None,
                 composite_index='NDVI',
                 composite_function='median'):
        """
        :param const: Constant value used in the SAVI formula
        :param scale_factor: Scale factor to multiply input ee.Image object with
        :param index_list: list of names of indices to add
                 valid names: ['EVI', 'NDVI', 'SAVI', 'NDWI', 'NBR', 'VARI']
                 default: None
        :param composite_index: Index to base the composite on (default: 'NDVI',
                                                                valid: 'NBR','EVI','SAVI','NDWI','NDVI')
        :param composite_function: Function to use for compositing (default: 'median',
                                                                    valid: 'mean','median','min','max',
                                                                    'sum','rms','diag',
                                                                    'interval_mean_xx_yy', 'percentile_xx')
                                                                    xx and yy are integers 0-100
        """
        self.scale_factor = scale_factor
        self.const = const
        self.index_list = index_list
        self.composite_index = composite_index
        self.composite_function = composite_function

    def __repr__(self):
        return '<EEFunc helper class for Google Earth Engine python scripts>'

    @staticmethod
    def expand_image_meta(img_meta):
        """
        Function to expand the metadata associated with an ee.Image object
        :param img_meta: Retrieved ee.Image metadata dictionary using getInfo() method
        :return: String
        """
        if type(img_meta) != dict:
            if type(img_meta).__name__ == 'Image':
                img_meta = img_meta.getInfo()
            else:
                raise RuntimeError('Unsupported EE object')

        out_str = ''
        for k, y in img_meta.items():
            if k == 'bands':
                for _y in y:
                    out_str += 'Band: {} : {}\n'.format(_y['id'], str(_y))
            elif k == 'properties':
                for _k, _y in y.items():
                    out_str += 'Property: {} : {}\n'.format(_k, str(_y))
            else:
                out_str += '{} : {}\n'.format(str(k), str(y))
        return out_str

    @staticmethod
    def expand_feature_meta(feat_meta):
        """
        Function to expand the metadata associated with an ee.Feature object
        :param feat_meta: Retrieved ee.Feature metadata dictionary using getInfo() method
        :return: String
        """
        if type(feat_meta) != dict:
            if type(feat_meta).__name__ == 'Feature':
                feat_meta = feat_meta.getInfo()
            else:
                raise RuntimeError('Unsupported EE object')

        out_str = ''
        for k, y in feat_meta.items():
            if k == 'geometry':
                for _k, _y in y.items():
                    out_str += '{}: {}\n'.format(str(_k), str(_y))

            elif k == 'properties':
                for _k, _y in y.items():
                    out_str += 'Property: {} : {}\n'.format(_k, str(_y))
            else:
                out_str += '{} : {}\n'.format(str(k), str(y))
        return out_str

    @staticmethod
    def expand_feature_coll_meta(feat_coll_meta):
        """
        Function to expand the metadata associated with an ee.FeatureCollection object
        :param feat_coll_meta: Retrieved ee.FeatureCollection metadata dictionary using getInfo() method
        :return: String
        """
        if type(feat_coll_meta) != dict:
            if type(feat_coll_meta).__name__ == 'FeatureCollection':
                feat_coll_meta = feat_coll_meta.getInfo()
            else:
                raise RuntimeError('Unsupported EE object')

        out_str = '---------------------\n'
        for k, y in feat_coll_meta.items():
            if k == 'features':
                for feat in y:
                    out_str += EEHelper.expand_feature_meta(feat) + '---------------------\n'

            elif k == 'properties':
                for _k, _y in y.items():
                    out_str += 'Property: {} : {}\n'.format(_k, str(_y))
            else:
                out_str += '{} : {}\n'.format(str(k), str(y))
        return out_str

    def ndvi(self,
             img):
        """
        Normalized difference vegetation index
        :param img: ee.Image object
        :returns: ee.Image object
        """
        return img.normalizedDifference(['NIR', 'RED']).select([0], ['NDVI']).multiply(self.scale_factor)

    def vari(self,
             img):
        """
        Visible Atmospherically Resistant Index
        :param img: ee.Image object
        :returns: ee.Image object
        """
        return (img.select(['RED']).subtract(img.select(['GREEN'])))\
            .divide(img.select(['RED']).add(img.select(['GREEN'])).subtract(img.select(['BLUE'])))\
            .select([0], ['VARI']).multiply(self.scale_factor)

    def evi(self,
            img):
        """
        Enhanced Vegetation Index
        :param img: ee.Image object
        :returns: ee.Image object
        """
        img = ee.Image(img)
        evi = ee.Image(img.select(['NIR']).subtract(img.select(['RED']))) \
            .divide(img.select(['NIR']).add((img.select(['RED'])).multiply(6.0)).subtract((img.select(['BLUE']))
                                                                                          .multiply(7.5)).add(1.0)) \
            .select([0], ['EVI'])
        return ee.Image(evi).multiply(2.5).multiply(self.scale_factor)

    def ndwi(self,
             img):
        """
        Normalized difference wetness index
        :param img: ee.Image object
        :returns: ee.Image object
        """
        return img.normalizedDifference(['NIR', 'SWIR2']).select([0], ['NDWI']).multiply(self.scale_factor)

    def nbr(self,
            img):
        """
        Normalized burn ratio
        :param img: ee.Image object
        :returns: ee.Image object
        """
        return img.normalizedDifference(['NIR', 'SWIR1']).select([0], ['NBR']).multiply(self.scale_factor)

    def savi(self,
             img):
        """
        Soil adjusted vegetation index
        :param img: ee.Image object
        :returns: ee.Image object
        """
        return (img.select(['NIR']).subtract(img.select(['RED'])).multiply(1 + self.const))\
            .divide(img.select(['NIR']).add(img.select(['RED'])).add(self.const))\
            .select([0], ['SAVI']).multiply(self.scale_factor).toInt16()

    def add_indices(self,
                    in_image):
        """
        Function to add indices to an image:  NDVI, NDWI, VARI, NBR, SAVI
        :param in_image: Input ee.Image object
        :returns: ee.Image object
        """

        temp_image = in_image.float().divide(self.scale_factor)

        for index in self.index_list:
            func = getattr(self, index.lower(), None)
            if func is not None:
                in_image = ee.Image(in_image).addBands(func(temp_image))

        return in_image

    @staticmethod
    def add_suffix(in_image,
                   suffix_str):
        """
        Add suffix to all band names
        :param in_image: input ee.Image object
        :param suffix_str: suffix to be added to all band names
        :returns: ee.Image object
        """
        bandnames = in_image.bandNames().map(lambda elem: ee.String(elem).toLowerCase().cat('_').cat(suffix_str))
        nb = bandnames.length()
        return in_image.select(ee.List.sequence(0, ee.Number(nb).subtract(1)), bandnames)

    @staticmethod
    def ls8_sr_corr(img):
        """
        Method to correct Landsat 8 based on Landsat 7 reflectance.
        This method scales the SR reflectance values to match LS7 reflectance
        The returned values are generally lower than input image
        based on roy et al 2016
        DOI: 10.1016/j.rse.2015.12.024

        :param img: ee.Image object
        :returns ee.Image object
        """
        return img.select(['B2'], ['BLUE']).float().multiply(0.8850).add(183).int16()\
            .addBands(img.select(['B3'], ['GREEN']).float().multiply(0.9317).add(123).int16())\
            .addBands(img.select(['B4'], ['RED']).float().multiply(0.9372).add(123).int16())\
            .addBands(img.select(['B5'], ['NIR']).float().multiply(0.8339).add(448).int16())\
            .addBands(img.select(['B6'], ['SWIR1']).float().multiply(0.8639).add(306).int16())\
            .addBands(img.select(['B7'], ['SWIR2']).float().multiply(0.9165).add(116).int16())\
            .addBands(img.select(['pixel_qa'], ['PIXEL_QA']).int16())\
            .addBands(img.select(['radsat_qa'], ['RADSAT_QA']).int16())\
            .copyProperties(img)\
            .copyProperties(img, ['system:time_start', 'system:time_end', 'system:index', 'system:footprint'])

    @staticmethod
    def ls5_sr_corr(img):
        """
        Method to correct Landsat 5 based on Landsat 7 reflectance.
        This method scales the SR reflectance values to match LS7 reflectance
        The returned values are generally lower than input image
        based on sulla-menashe et al 2016
        DOI: 10.1016/j.rse.2016.02.041

        :param img: ee.Image object
        :returns ee.Image object
        """
        return img.select(['B1'], ['BLUE']).float().multiply(0.91996).add(37).int16()\
            .addBands(img.select(['B2'], ['GREEN']).float().multiply(0.92764).add(84).int16())\
            .addBands(img.select(['B3'], ['RED']).float().multiply(0.8881).add(98).int16())\
            .addBands(img.select(['B4'], ['NIR']).float().multiply(0.95057).add(38).int16())\
            .addBands(img.select(['B5'], ['SWIR1']).float().multiply(0.96525).add(29).int16())\
            .addBands(img.select(['B7'], ['SWIR2']).float().multiply(0.99601).add(20).int16())\
            .addBands(img.select(['pixel_qa'], ['PIXEL_QA']).int16())\
            .addBands(img.select(['radsat_qa'], ['RADSAT_QA']).int16())\
            .copyProperties(img)\
            .copyProperties(img, ['system:time_start', 'system:time_end', 'system:index', 'system:footprint'])

    @staticmethod
    def ls_sr_band_correction(img):
        """
        This method renames LS5, LS7, and LS8 bands and corrects LS5 and LS8 bands
        this method should be used with SR only

        :param img: ee.Image object
        :returns ee.Image object
        """
        return \
            ee.Algorithms.If(
                ee.String(img.get('SATELLITE')).compareTo('LANDSAT_8'),
                ee.Algorithms.If(
                    ee.String(img.get('SATELLITE')).compareTo('LANDSAT_5'),
                    ee.Image(img.select(['B1', 'B2', 'B3', 'B4', 'B5', 'B7', 'pixel_qa', 'radsat_qa'],
                                        ['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2', 'PIXEL_QA', 'RADSAT_QA'])
                             .int16()
                             .copyProperties(img)
                             .copyProperties(img,
                                             ['system:time_start',
                                              'system:time_end',
                                              'system:index',
                                              'system:footprint'])),
                    ee.Image(EEHelper.ls5_sr_corr(img))
                ),
                ee.Image(EEHelper.ls8_sr_corr(img))
            )

    @staticmethod
    def ls_sr_only_clear(img):
        """
        Method to calcluate clear mask based on pixel_qa and radsat_qa bands

        :param img: ee.Image object
        :returns ee.Image object
        """
        clearbit = 1
        clearmask = math.pow(2, clearbit)
        qa = img.select('PIXEL_QA')
        qa_mask = qa.bitwiseAnd(clearmask)

        ra = img.select('RADSAT_QA')
        ra_mask = ra.eq(0)

        return ee.Image(img.updateMask(qa_mask).updateMask(ra_mask))

    @staticmethod
    def add_elevation_bands(img,
                            dem_img):
        """
        Method to add elevation, slope and aspect to ee.Image object
        :param img: Input ee.Image object
        :param dem_img: DEM image as ee.Image object
        """
        elevation = ee.Image(dem_img)
        slope = ee.Terrain.slope(elevation)
        aspect = ee.Terrain.aspect(elevation)
        topo = elevation.addBands(slope).addBands(aspect)\
            .select([0, 1, 2], ['elevation', 'slope', 'aspect'])
        return ee.Image(img).addBands(topo)

    @staticmethod
    def buffer_collection(feat_collection,
                          buffer_width=15,
                          bounds=True):
        """
        Method to buffer a feature collection
        :param feat_collection: feature collection to buffer
        :param buffer_width: Width of the buffer collection in meters (default: 15)
        :param bounds: if bounding rectangle for the buffer should be computed
        """
        if bounds:
            return feat_collection.map(lambda feat: feat.buffer(buffer_width).bounds())
        else:
            return feat_collection.map(lambda feat: feat.buffer(buffer_width))

    @staticmethod
    def band_with_properties(img,
                             band=None):
        """
        Method to select band(s) from an image and
        copy properties from the ee.Image object to the output
        :param img: ee.Image object
        :param band: List of band indices or names
        """
        if band is None:
            band = [0]
        out_img = img.select(band).copyProperties(img)
        return out_img

    def get_images(self,
                   collection,
                   bounds=None,
                   year=None,
                   start_date=None,
                   end_date=None,
                   start_julian=1,
                   end_julian=365,
                   index_list=None,
                   scale_factor=None,
                   **kwargs):
        """
        Make ee.ImageCollection object based on given common parameters
        :param collection: ee.ImageCollection object
        :param bounds: ee.Geometry object area of interest
        :param year: If processing for the entire year specify this instead of start_date and end_date
        :param start_date: starting date for filtering collection in format 'YYYY-MM-DD'
        :param end_date: ending date for filtering collection in format 'YYYY-MM-DD'
        :param start_julian: Start of julian date to filter collection on annual basis (Default:1)
        :param end_julian: End of julian date to filter collection on annual basis (Default:365)
        :param index_list: List of indices to be added to each image
                            (Default: ['NDVI', 'NDWI', 'SAVI', 'VARI', 'NBR'])
        :param scale_factor: Scale factor for added indices bands (Default: 10000)
        :param kwargs: Keyword arguments for mapping functions on the collection
                       Can be used only for valid collection-mappable functions in EEFunc
                           map='ls_sr_band_correction'
                           map='ls_sr_only_clear'
                           map='add_indices'
        :returns ee.ImageCollection object
        """
        coll = ee.ImageCollection(collection)

        if year is not None:
            start_date = '{}-01-01'.format(str(year))
            end_date = '{}-12-31'.format(str(year))

        if bounds is not None:
            coll = coll.filterBounds(bounds)
        if (start_date is not None) and (end_date is not None):
            coll = coll.filterDate(start_date, end_date)

        coll = coll.filter(ee.Filter.calendarRange(start_julian, end_julian))

        if len(kwargs) > 0:
            for key, value in kwargs.items():
                if key == 'map':
                    if value == 'add_indices':

                        if index_list is not None:
                            self.index_list = index_list

                        if scale_factor is not None:
                            self.scale_factor = scale_factor

                    func = getattr(self, value, None)

                    if func is not None:
                        coll = coll.map(func)
                else:
                    warnings.warn('The function {} is not implemented'.format(str(key)))
        return coll

    def composite_image(self,
                        collection,
                        region=None,
                        band_selector=None,
                        band_names=None):
        """
        function to generate a maximum value composite image
        Default reducer: Median
        Default compositing index: NDVI

        :param collection: ee.ImageCollection
        :param region: Region (ee.Geometry or ee.Feature) to clip the composite image
        :param band_selector: List of band selectors to select from each image
        :param band_names: list of names to rename the selected bands with
        :returns ee.Image object
        """
        collection = ee.ImageCollection(collection).map(lambda x: x.multiply(ee.Image(self.scale_factor)))
        if self.composite_function == 'mean' or self.composite_function == 'rms':
            reducer = ee.Reducer.mean()
        elif self.composite_function == 'median':
            reducer = ee.Reducer.median()
        elif self.composite_function == 'min':
            reducer = ee.Reducer.min()
        elif self.composite_function == 'max':
            reducer = ee.Reducer.max()
        elif self.composite_function == 'sum' or self.composite_function == 'diag':
            reducer = ee.Reducer.sum()
        elif 'percentile' in self.composite_function:
            pctl = int(self.composite_function.replace('percentile_', '').strip())
            reducer = ee.Reducer.percentile([pctl])
        elif 'interval_mean' in self.composite_function:
            temp_str = self.composite_function.replace('interval_mean_', '').strip()
            min_pctl, max_pctl = [int(elem) for elem in temp_str.split('_')]
            if min_pctl > max_pctl:
                min_pctl, max_pctl = max_pctl, min_pctl
            reducer = ee.Reducer.intervalMean(min_pctl,
                                              max_pctl)
        else:
            warnings.warn('Supplied reducer {} is not implemented.\n'.format(self.composite_function) +
                          'Using default: median')
            reducer = ee.Reducer.median()

        if band_names is not None:
            collection = collection.select(band_names)

        if self.composite_index is None:
            if self.composite_function in ('rms', 'diag'):
                out_img = ee.ImageCollection(collection.map(lambda x: ee.Image(x).multiply(ee.Image(x))))\
                    .reduce(reducer)
            else:
                out_img = collection.reduce(reducer)

        else:
            index_band = collection.select(self.composite_index).reduce(reducer)
            with_dist = collection.map(lambda image: image.addBands(image.select(self.composite_index)
                                                                    .subtract(index_band).abs().multiply(-1)
                                                                    .rename('quality')))
            out_img = with_dist.qualityMosaic('quality')
            out_img = out_img.select(out_img.bandNames().removeAll(['quality']))

        if region is not None:
            return out_img.clip(region)
        else:
            return out_img

    @staticmethod
    def export_image_to_drive(img,
                              folder=None,
                              scale=None,
                              crs=None,
                              region=None,
                              verbose=False,
                              save_metadata=True,
                              metadata_folder='.'):

        """
        Method to download an image to google drive from an ee.Image object.
        Ideally, this image should be part of an ee.ImageCollection object

        :param img: ee.Image object to download
        :param folder: folder on Google drive to download image to
        :param crs: CRS string (default: None, uses image native crs string)
        :param region: Region to clip the image and use for extent, ee.Geometry or ee.Feature
                       if ee.FeatureCollection is specified, first feature is used as region
                      (default: None, uses image footprint)
        :param scale: Scale in meters to use for export (default: None, uses image native scale)
        :param verbose: If some steps should be displayed (default: False)
        :param save_metadata: If the associated metadata with the image should be stored on local disk
        :param metadata_folder: Location to store image metadata as text
        """

        img_prop = ee.Image(img).getInfo()
        img_id = img_prop['id'].replace('/', '_')
        metadata_str = EEHelper.expand_image_meta(img_prop)

        if crs is None:
            crs = img_prop['bands'][0]['crs']
        crs_transform = img_prop['bands'][0]['crs_transform']

        if scale is None:
            scale = crs_transform[0]

        if region is None:
            region_geom = img_prop['properties']['system:footprint']['coordinates']
        else:
            img = img.clip(region)
            region_dict = region.getInfo()
            if region_dict['type'] == 'FeatureCollection':
                region_geom = region_dict['features'][0]['geometry']['coordinates']
            elif region_dict['type'] == 'Feature':
                region_geom = region_dict['geometry']['coordinates']
            elif region_dict['type'] == 'Geometry':
                region_geom = region_dict['coordinates']
            else:
                warnings.warn('Invalid geometry, using image footprint for export.')
                region_geom = img_prop['properties']['system:footprint']['coordinates']

        if verbose:
            sys.stdout.write('Exporting: {}\n'.format(folder + '/' + img_id))
            sys.stdout.write(metadata_str)

        task = ee.batch.Export.image.toDrive(
            image=img,
            fileNamePrefix=img_id,
            folder=folder,
            description='Export_{}'.format(img_id),
            scale=scale,
            crsTransform=crs_transform,
            crs=crs,
            region=region_geom,
            maxPixels=1e13,
            skipEmptyTiles=True)

        res = task.start()
        if verbose:
            sys.stdout.write(task)

        if save_metadata:
            with open(metadata_folder + '/' + img_id + '.txt', 'w') as metadata_file_ptr:
                metadata_file_ptr.write(metadata_str)

    @staticmethod
    def export_coll_to_drive(collection,
                             folder=None,
                             scale=None,
                             region=None,
                             crs=None,
                             verbose=False,
                             save_metadata=True,
                             metadata_folder='.'):

        """
        Method to download an Image Collection to google drive from an ee.ImageCollection object.

        :param collection: ee.ImageCollection object to download
        :param folder: folder on Google drive to download image to
        :param crs: CRS string (default: None, uses image native crs string)
        :param region: Region to clip the image and use for extent, ee.Geometry or ee.Feature
                       if ee.FeatureCollection is specified, first feature is used as region
                      (default: None, uses image footprint)
        :param scale: Scale in meters to use for export (default: None, uses image native scale)
        :param verbose: If some steps should be displayed (default: False)
        :param save_metadata: If the associated metadata with the image should be stored on local disk
        :param metadata_folder: Location to store image metadata as text
        """

        collection = collection.filterBounds(region)

        # get size info
        coll_size = collection.size().getInfo()
        sys.stdout.write("Exporting {} images from this collection.\n".format(coll_size))

        # convert collection to list
        coll_list = collection.toList(coll_size)

        # loop over all collection images and export
        for img_indx in range(coll_size):
            img = ee.Image(coll_list.get(img_indx))

            EEHelper.export_image_to_drive(img,
                                           folder=folder,
                                           scale=scale,
                                           crs=crs,
                                           region=region,
                                           verbose=verbose,
                                           save_metadata=save_metadata,
                                           metadata_folder=metadata_folder)

