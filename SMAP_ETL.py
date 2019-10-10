# Last Modified By:
#   Githika Tondapu - ~March 2017
#   Lance Gilliland - June 5, 2017
#       - Added a new GetStartDateFromdb() to include an updated SQLWhere; included specific fields in the query
#           and sorted results in descending order to be able to grab the first result and then break from the for
#           loop - this was done to help with performance.
#       - Set arcpy.env.overwriteOutput = True in LoadRasters() so that previously downloaded files could be
#           reprocessed in case they were not successfully added to the mosaic dataset on last run; commented out the
#           joinedPath code as it is not used; added back in: year = theName[5:9] that was somehow missing.
#       - Minor readability edits and cleanup.

import arcpy
import datetime
import glob
import os
import shutil
import logging
import urllib2
import urllib
import json
import pickle
import requests  # Needed for create_token()
import socket  # Needed for create_token()


# Get Start Date from E:\SERVIR\Data\Global\soil_moisture.gdb\soil_moisture
def orig_GetStartDateFromdb(mosaicDS):
    try:
        Expression = "Name IS NOT NULL"  # No names should be NULL, this is just precautionary
        rows = arcpy.UpdateCursor(mosaicDS, Expression, '', '', "DateObtained ASC")
        theDate = None
        for r in rows:
            theDate = r.dateObtained
        if theDate == None:
            return datetime.datetime.strptime("2015/09/10", "%Y/%m/%d")
        return theDate
    except Exception, e:
        logging.error('### Error occurred in GetStartDateFromdb ###, %s' % e)
        return None


    # Get Start Date from the specified Raster Mosaic Dataset.
    # Note that the intent is to retrieve the date of the latest(last) successful load of raster data into the dataset.
def GetStartDateFromdb(mosaicDS):
        try:
            SQLWhere = "Name IS NOT NULL AND DateObtained IS NOT NULL"
            # Sort most recent date first (descending) so we can just grab the first row then break out of the for loop!
            # Also, only request the Name and DateObtained fields as that is all we need and it should be faster.
            rows = arcpy.SearchCursor(mosaicDS, SQLWhere, '', fields="Name; DateObtained", sort_fields="DateObtained D")
            theDate = None
            for r in rows:
                theDate = r.dateObtained
                break

            if theDate is None:
                theDate = datetime.datetime.strptime("2017/03/20", "%Y/%m/%d")

            return theDate

        except Exception, e:
            logging.error('### Error occurred in GetStartDateFromdb ###, %s' % e)
            return None


# Extract to E:\Temp\SMAP_Extract\		
def LoadRasters(temp_workspace):
    try:
        arcpy.CheckOutExtension("Spatial")
        inSQLClause = "VALUE >= 0"
        arcpy.env.workspace = temp_workspace  # E:\Temp\SMAP_Extract\
        arcpy.env.overwriteOutput = True  # Lance added...
        rasters = arcpy.ListRasters()
        for raster in rasters:
            # In case the file is not a valid raster file...  add a try / catch exception
            try:
                logging.info('Processing file: %s' % raster)
                print ('Processing file: %s' % raster)
                extract = arcpy.sa.ExtractByAttributes(raster, inSQLClause)
                finalRaster = os.path.join(myConfig['finalTranslateFolder'], raster)
                extract.save(finalRaster)
                arcpy.AddRastersToMosaicDataset_management(mosaicDS, "Raster Dataset", finalRaster, "UPDATE_CELL_SIZES",
                                                           "NO_BOUNDARY", "NO_OVERVIEWS", "2", "#", "#", "#", "#",
                                                           "NO_SUBFOLDERS", "EXCLUDE_DUPLICATES", "BUILD_PYRAMIDS",
                                                           "CALCULATE_STATISTICS", "NO_THUMBNAILS", "Add Raster Datasets",
                                                           "#")
                theName = os.path.splitext(raster)[0]
                Expression = "Name= '" + theName + "'"
                rows = arcpy.UpdateCursor(mosaicDS, Expression)  # Establish r/w access to data in the query expression.
                year = theName[5:9]  # Lance added...
                month = theName[9:11]
                day = theName[11:13]
                theStartDate = year + "/" + month + "/" + day
                dt_obj = theStartDate  # dt_str.strptime('%Y/%m/%d')
                for r in rows:
                    r.dateObtained = dt_obj  # here the value is being set in the proper field
                    rows.updateRow(r)  # update the values
                extract = None
                del extract, rows
            except Exception, e:
                logging.warning('### Error processing file! SKIPPING! ###, %s' % e)
                print ('### Error processing file! - Skipping... ###')

        del rasters
    except Exception, e:
        logging.error('### Error occurred in LoadRasters ###, %s' % e)


# Restarting the ArcGIS Service (Stop and Start)
def refreshService():
    pkl_file = open('config.pkl', 'rb')
    myConfig = pickle.load(pkl_file)  # store the data from config.pkl file
    pkl_file.close()
    #current_Description = "SMAP Mosaic Dataset Service"
    current_AdminDirURL = myConfig['current_AdminDirURL']
    current_Username = myConfig['current_Username']
    current_Password = myConfig['current_Password']
    current_FolderName = myConfig['current_FolderName']
    current_ServiceName = myConfig['current_ServiceName']
    current_ServiceType = myConfig['current_ServiceType']
    # Try and stop each service
    try:
        # Get a token from the Administrator Directory
        tokenParams = urllib.urlencode({"f":"json","username":current_Username,"password":current_Password,"client":"requestip"})
        #logging.info("tokenParams: " + tokenParams)
        tokenResponse = urllib.urlopen(current_AdminDirURL+"/generateToken?",tokenParams).read()
        #logging.info("tokenResponse: " + tokenResponse)
        tokenResponseJSON = json.loads(tokenResponse)
        token = tokenResponseJSON["token"]

        # Attempt to stop the current service
        stopParams = urllib.urlencode({"token":token,"f":"json"})
        stopResponse = urllib.urlopen(current_AdminDirURL+"/services/"+current_FolderName+"/"+current_ServiceName+"."+current_ServiceType+"/stop?",stopParams).read()
        stopResponseJSON = json.loads(stopResponse)
        stopStatus = stopResponseJSON["status"]

        if stopStatus <> "success":
            logging.warning("SMAP Stop Service: UNABLE TO STOP SERVICE "+str(current_FolderName)+"/"+str(current_ServiceName)+"/"+str(current_ServiceType)+" STATUS = "+stopStatus)
        else:
            logging.info("SMAP Stop Service: Service: " + str(current_ServiceName) + " has been stopped.")

    except Exception, e:
        logging.error("SMAP Stop Service: ### ERROR ### - Stop Service failed for " + str(current_ServiceName) + ", System Error Message: "+ str(e))
    # Try and start each service
    try:
        # Get a token from the Administrator Directory
        tokenParams = urllib.urlencode({"f":"json","username":current_Username,"password":current_Password,"client":"requestip"})
        tokenResponse = urllib.urlopen(current_AdminDirURL+"/generateToken?",tokenParams).read()
        tokenResponseJSON = json.loads(tokenResponse)
        token = tokenResponseJSON["token"]

        # Attempt to stop the current service
        startParams = urllib.urlencode({"token":token,"f":"json"})
        startResponse = urllib.urlopen(current_AdminDirURL+"/services/"+current_FolderName+"/"+current_ServiceName+"."+current_ServiceType+"/start?",startParams).read()
        startResponseJSON = json.loads(startResponse)
        startStatus = startResponseJSON["status"]

        if startStatus == "success":
            logging.info("SMAP start Service: Started service "+str(current_FolderName)+"/"+str(current_ServiceName)+"/"+str(current_ServiceType))
        else:
            logging.warning("SMAP start Service: UNABLE TO START SERVICE "+str(current_FolderName)+"/"+str(current_ServiceName)+"/"+str(current_ServiceType)+" STATUS = "+startStatus)
    except Exception, e:
        logging.error("SMAP start Service: ### ERROR ### - Start Service failed for " + str(current_ServiceName) + ", System Error Message: "+ str(e))


# Clean out the extract folder
def cleanExtractFolder():
    folder = myConfig['extract_Folder']
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception, e:
            logging.error('### Error occurred in cleanExtractFolder removing files ###, %s' % e)
    try:
        shutil.rmtree(folder + 'info', ignore_errors=True)
    except Exception, e:
            logging.error('### Error occurred in cleanExtractFolder removing info folder ###, %s' % e)
    try:
        shutil.rmtree(folder + 'temp', ignore_errors=True)
    except Exception, e:
            logging.error('### Error occurred in cleanExtractFolder removing temp folder ###, %s' % e)


# Delete outdated files in E:\SERVIR\Data\Global\soil_moisture
def deleteOutOfDateRasters(mymosaicDS):
    try:
        earlier = datetime.datetime.now() - datetime.timedelta(days=90)
        query = "DateObtained < date '" + earlier.strftime('%Y-%m-%d') + "'"
        logging.info('Removing rasters from Mosaic DS where: ' + query)
        arcpy.RemoveRastersFromMosaicDataset_management(mymosaicDS, query,
                                                        "UPDATE_BOUNDARY", "MARK_OVERVIEW_ITEMS",
                                                        "DELETE_OVERVIEW_IMAGES")
        files = glob.glob(myConfig['finalTranslateFolder'] + "\*.tif")
        rasterses = []
        for file in files:
            theName = file.rsplit('\\', 1)[-1]
            theDate = theName.rsplit('_')[1]
            dateObject = datetime.datetime.strptime(theDate, "%Y%m%d")
            if earlier > dateObject:
                rasterses.append(theName)
        arcpy.env.workspace = myConfig['finalTranslateFolder']
        for oldraster in rasterses:
            arcpy.Delete_management(oldraster) 
    except Exception, e:
            logging.error('### Error occurred in deleteOutOfDateRasters ###, %s' % e)


def create_token (uid, pswd):
    try:
        #import XML Element Tree
        from xml.etree.ElementTree import Element, SubElement, Comment, tostring

        #Find IP address
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)

        #Create XML input
        token = Element('token')
        username = SubElement(token, 'username')
        username.text = uid
        password = SubElement(token, 'password')
        password.text = pswd
        client_id = SubElement(token, 'client_id')
        client_id.text = 'NSIDC_client_id'
        user_ip_address = SubElement(token, 'user_ip_address')
        user_ip_address.text = IP

        # xml = (tostring(token, encoding='unicode', method='xml'))
        xml = (tostring(token, encoding='us-ascii', method='xml'))

        # Request token from Common Metadata Repository
        headers = {'Content-Type': 'application/xml'}
        # token = requests.post('https://api.echo.nasa.gov/echo-rest/tokens', data=xml, headers=headers)
        token = requests.post('https://cmr.earthdata.nasa.gov/legacy-services/rest/tokens', data=xml, headers=headers)
        output = token.text

        # Grab token string
        start = '<id>'
        end = '</id>'
        tokenval = (output.split(start))[1].split(end)[0]

        return tokenval

    except Exception, e:
            logging.error('### Error occurred in create_token() ###, %s' % e)


# *********************************************SCRIPT ENTRY POINT*************************************
# ************************************************INIT PROCESS****************************************
print "SMAP ETL Started"
pkl_file = open('config.pkl', 'rb')
myConfig = pickle.load(pkl_file)
pkl_file.close()
logDir = myConfig['logFileDir']
logging.basicConfig(filename=logDir + '\SMAP_log_' + datetime.date.today().strftime('%Y-%m-%d') + '.log',
                    level=logging.DEBUG,
                    format='%(asctime)s: %(levelname)s --- %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info('******************************SMAP ETL Started************************************************')
mosaicDS = myConfig['mosaicDS']
numProcessed = 0
# ************************************************Extract PROCESS****************************************
# DEBUGGING CODE!!!
# theStartDate = datetime.datetime.strptime("2019/08/12", "%Y/%m/%d")
theStartDate = GetStartDateFromdb(mosaicDS)   # Original code...

if theStartDate is None:
    logging.warn('### ERROR### SMAP ETL did not run because could not determine start date.')
else:
    logging.info('Last Date Entry in Database: %s' % theStartDate.strftime('%Y-%m-%d'))

    logging.info('---------- Generating CMR ECHO API token ----------')
    print "--- Generating CMR ECHO API token ---"
    # LG 3/25/2019 - Request CMR ECHO API token. Requires "EarthData" (https://urs.earthdata.nasa.gov/) login.
    # Tokens are valid for 30 days. Grab one here and use it multiple times below.
    token = create_token(myConfig['EarthData_User'], myConfig['EarthData_Pass'])

    logging.info('---------- Beginning File Downloads ----------')
    print "--- Beginning File Downloads ---"

    # DEBUGGING CODE!!! Only test a few days at a time...
    # threeDays = datetime.timedelta(days=3)
    # StartDatePlus3 = theStartDate + threeDays
    # while theStartDate.date() < StartDatePlus3.date():
    while theStartDate.date() < datetime.date.today():
        theStartDate += datetime.timedelta(days=1)
        tempDate = theStartDate.strftime('%Y-%m-%d')
        print tempDate

        # Check URL for granule
        # 6/15/2018 - Remove version parameter as the version changes from time to time...
        # granulesUrl = "https://cmr.earthdata.nasa.gov/search/granules?short_name=SPL3SMP&version=004&temporal="+tempDate+"T00:00:01Z/"+tempDate+"T23:59:59Z"
        granulesUrl = "https://cmr.earthdata.nasa.gov/search/granules?short_name=SPL3SMP&temporal="+tempDate+"T00:00:01Z/"+tempDate+"T23:59:59Z"
        response = urllib2.urlopen(granulesUrl)
        html = response.read()
        startValue = html.find("<name>") + 6

        if startValue > 7:
            # Parse granule name/ID
            endValue = html.find("</name>") - len(html)
            parsedName = html[startValue:endValue]
            lastColon = parsedName.rfind(':')
            finalName = parsedName[lastColon + 1:len(parsedName)]
            logging.info('New granule name: ' + finalName)

            rasterFile = myConfig['extract_Folder'] + 'SMAP_' + theStartDate.strftime('%Y%m%d') + '_soil_moisture.tif'
            logging.info('File to be downloaded: ' + rasterFile)

            # Build and check URL to download granule file
            # url = 'https://n5eil01u.ecs.nsidc.org/egi/request?short_name=SPL3SMP&version=004&format=GeoTIFF&time=2016-12-13,2016-12-13&Coverage=/Soil_Moisture_Retrieval_Data_AM/soil_moisture&token=75E5CEBE-6BBB-2FB5-A613-0368A361D0B6&email=billy.ashmall@nasa.gov&FILE_IDS=' + finalName
            # 6/15/2018 - Remove version parameter as the version changes from time to time...
            # url = 'https://n5eil01u.ecs.nsidc.org/egi/request?short_name=SPL3SMP&format=GeoTIFF&time=2016-12-13,2016-12-13&Coverage=/Soil_Moisture_Retrieval_Data_AM/soil_moisture&token=75E5CEBE-6BBB-2FB5-A613-0368A361D0B6&email=billy.ashmall@nasa.gov&FILE_IDS=' + finalName
            # 3/25/2019 - Include dynamic token generated above...
            # url = 'https://n5eil01u.ecs.nsidc.org/egi/request?short_name=SPL3SMP&format=GeoTIFF&time=2016-12-13,2016-12-13&Coverage=/Soil_Moisture_Retrieval_Data_AM/soil_moisture&token=' + str(token) + '&email=lance.gilliland@nasa.gov&FILE_IDS=' + finalName
            # 9/2/2019 - With version 6 of the data starting 8/13/2019, we now have to specify the "subagent type" to get the .tif post processed file
            url = 'https://n5eil01u.ecs.nsidc.org/egi/request?short_name=SPL3SMP&format=GeoTIFF&time=2016-12-13,2016-12-13&Coverage=/Soil_Moisture_Retrieval_Data_AM/soil_moisture&token=' + str(token) + '&email=lance.gilliland@nasa.gov&SUBAGENT_ID=HEG&FILE_IDS=' + finalName

            # logging.info('Granule file url: ' + url)
            response = urllib.urlopen(url)
            data = response.read()
            # NOTE! The source file might actually be missing from the DAAC and if so, the return value will be a
            # URL XML response.  So check to see if the response contains a string of "xml".  If so, we know it is not
            # the desired raster file.
            if 'xml' in data[:20]:
                # UH OH - data should contain a binary raster file...
                # ...this means that the raster file must not exist for download.
                logging.warn('### File is NOT a valid raster! Skipping: %s ###' % rasterFile)
            else:
                # Assume that the file was a raster and downloaded ok. Save it.
                if not os.path.exists(os.path.dirname(rasterFile)):
                    os.makedirs(os.path.dirname(rasterFile))
                out_file = open(rasterFile, 'wb')
                out_file.write(data)
                out_file.close()
                numProcessed += 1

    # ************************************************Transform and Load PROCESS****************************************
    # Up to here, we have downloaded the raster file granules to the temp processing extract folder, but now we need to
    # process the files and extract only the values > 0, saving the results to the final raster translate folder.
    logging.info('---------- Loading new Rasters to Mosaic ----------')
    print "--- Loading new Rasters to Mosaic ---"
    LoadRasters(myConfig['extract_Folder'])

    # Cleanup the temporary extract folder(s)
    logging.info('---------- Cleaning up Processing Folder ----------')
    print "--- Cleaning up Processing Folder ---"
    cleanExtractFolder()

    # Remove/delete the mosaic dataset entries older than the agreed upon timeframe.
    logging.info('---------- Removing out of date Rasters from Mosaic ----------')
    print "--- Removing out of date Rasters from Mosaic ---"
    deleteOutOfDateRasters(mosaicDS)

# Refresh the service to reflect any changes...
refreshService()
logging.info('Total number of processed files for this run: %s' % numProcessed)
logging.info('******************************SMAP ETL Finished************************************************')
print 'SMAP ETL Finished'
