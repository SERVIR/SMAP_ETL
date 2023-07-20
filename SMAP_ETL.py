# Last Modified By:
#   Githika Tondapu - ~March 2017
#   Lance Gilliland - June 5, 2017
#   Lance Gilliland - February 19, 2022
#   Githika Tondapu - July 20, 2023
#   - Migrated code from python 2.7 to python 3.7 to work with a new ArcGIS server (10.9.1) and ArcGIS Pro (2.9).
#   - This script was specifically created to support an Esri service, thus the use of a mosaic dataset,
#     ArcPy, ArcGIS Pro python conda environment, etc.
#     Esri is transitioning from ArcGIS Desktop to ArcGIS Pro, thus, the decision was made to use an ArcGIS Pro
#     environment - which contains, by default, a read-only conda-based Python env. called "arcgispro-py3".
#     Since it is read-only by default, we needed to make a copy of the env. - in case we needed to add more
#     packages - which is made easier by the python package manager that is delivered with ArcGIS Pro. Please see:
#     https://pro.arcgis.com/en/pro-app/arcpy/get-started/what-is-conda.htm
#     https://pro.arcgis.com/en/pro-app/arcpy/get-started/using-conda-with-arcgis-pro.htm
#     The duplicate of the default ArcGIS Pro conda python env. was created AS "arcgispro-py3-clone", then copied into
#     this project folder.
#
#     This code currently uses both the "requests" and "urllib.*" libraries. A future enhancement would
#     be to switch to using the requests library and eliminate the urllib.* libs.
from requests.auth import HTTPBasicAuth
import arcpy
import datetime
import glob
import os
import shutil
import logging
import pickle

# Note: urllib2 was split up into urllib.request and urllib.error for Py3.x+
# Also, urllib is made up of: urllib.request, urllib.error, urllib.parse, and urllib.robotparser
import urllib.request  # required in the main entry function and refreshService3x()
import urllib.parse  # required for refreshService3x()
import json  # required for refreshService3x()
import requests  # Needed for create_token()
import socket  # Needed for create_token()
import urllib
import json

def GetStartDateFromdb(mosDS):
    # Get Start Date from the specified Raster Mosaic Dataset.
    # Note that the intent is to retrieve the date of the latest(last) successful load of raster data into the dataset.
    try:
        SQLWhere = "Name IS NOT NULL AND DateObtained IS NOT NULL"
        # Sort most recent date first (descending) so we can just grab the first row then break out of the for loop!
        # Also, only request the Name and DateObtained fields as that is all we need and it should be faster.
        rows = arcpy.SearchCursor(mosDS, SQLWhere, '', fields="Name; DateObtained", sort_fields="DateObtained D")
        theDate = None
        for r in rows:
            theDate = r.dateObtained
            break

        if theDate is None:
            theDate = datetime.datetime.strptime("2017/03/20", "%Y/%m/%d")

        return theDate

    except Exception as e:
        logging.error('### Error occurred in GetStartDateFromdb ###, %s' % e)
        return None


def LoadRasters(temp_workspace):
    # Extract to E:\Temp\SMAP_Extract\
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
                print('Processing file: %s' % raster)
                extract = arcpy.sa.ExtractByAttributes(raster, inSQLClause)
                finalRaster = os.path.join(myConfig['finalTranslateFolder'], raster)
                extract.save(finalRaster)  # writes the raster file to the final location
                # Add the raster entry to the mosaic dataset
                arcpy.AddRastersToMosaicDataset_management(mosaicDS, "Raster Dataset", finalRaster, "UPDATE_CELL_SIZES",
                                                           "NO_BOUNDARY", "NO_OVERVIEWS", "2", "#", "#", "#", "#",
                                                           "NO_SUBFOLDERS", "EXCLUDE_DUPLICATES", "BUILD_PYRAMIDS",
                                                           "CALCULATE_STATISTICS", "NO_THUMBNAILS",
                                                           "Add Raster Datasets",
                                                           "#")
                # Retrieve the row just added and update the DateObtained field with the date from the file name.
                theName = os.path.splitext(raster)[0]
                Expression = "Name= '" + theName + "'"
                rows = arcpy.UpdateCursor(mosaicDS, Expression)  # Establish r/w access to data in the query expression.
                year = theName[5:9]  # Lance added...
                month = theName[9:11]
                day = theName[11:13]
                theDate = year + "/" + month + "/" + day
                dt_obj = theDate
                for r in rows:
                    r.dateObtained = dt_obj  # here the value is being set in the proper field
                    rows.updateRow(r)  # update the values
                extract = None
                del extract, rows
            except Exception as e:
                logging.warning('### Error processing file! SKIPPING! ###, %s' % e)
                print('### Error processing file! - Skipping... ###')

        del rasters
    except Exception as e:
        logging.error('### Error occurred in LoadRasters ###, %s' % e)


# No Longer Used...
# def refreshService():
#     # Restarting the ArcGIS Service (Stop and Start)
#     pkl_file = open('config.pkl', 'rb')
#     myConfig = pickle.load(pkl_file)  # store the data from config.pkl file
#     pkl_file.close()
#     # current_Description = "SMAP Mosaic Dataset Service"
#     current_AdminDirURL = myConfig['current_AdminDirURL']
#     current_Username = myConfig['current_Username']
#     current_Password = myConfig['current_Password']
#     current_FolderName = myConfig['current_FolderName']
#     current_ServiceName = myConfig['current_ServiceName']
#     current_ServiceType = myConfig['current_ServiceType']
#     # Try and stop each service
#     try:
#         # Get a token from the Administrator Directory
#         tokenParams = urllib.urlencode(
#             {"f": "json", "username": current_Username, "password": current_Password, "client": "requestip"})
#         # logging.info("tokenParams: " + tokenParams)
#         tokenResponse = urllib.urlopen(current_AdminDirURL + "/generateToken?", tokenParams).read()
#         # logging.info("tokenResponse: " + tokenResponse)
#         tokenResponseJSON = json.loads(tokenResponse)
#         token = tokenResponseJSON["token"]
#
#         # Attempt to stop the current service
#         stopParams = urllib.urlencode({"token": token, "f": "json"})
#         stopResponse = urllib.urlopen(
#             current_AdminDirURL + "/services/" + current_FolderName + "/" + current_ServiceName + "." + current_ServiceType + "/stop?",
#             stopParams).read()
#         stopResponseJSON = json.loads(stopResponse)
#         stopStatus = stopResponseJSON["status"]
#
#         if stopStatus != "success":
#             logging.warning("SMAP Stop Service: UNABLE TO STOP SERVICE " + str(current_FolderName) + "/" + str(
#                 current_ServiceName) + "/" + str(current_ServiceType) + " STATUS = " + stopStatus)
#         else:
#             logging.info("SMAP Stop Service: Service: " + str(current_ServiceName) + " has been stopped.")
#
#     except Exception as e:
#         logging.error("SMAP Stop Service: ### ERROR ### - Stop Service failed for " + str(
#             current_ServiceName) + ", System Error Message: " + str(e))
#     # Try and start each service
#     try:
#         # Get a token from the Administrator Directory
#         tokenParams = urllib.urlencode(
#             {"f": "json", "username": current_Username, "password": current_Password, "client": "requestip"})
#         tokenResponse = urllib.urlopen(current_AdminDirURL + "/generateToken?", tokenParams).read()
#         tokenResponseJSON = json.loads(tokenResponse)
#         token = tokenResponseJSON["token"]
#
#         # Attempt to stop the current service
#         startParams = urllib.urlencode({"token": token, "f": "json"})
#         startResponse = urllib.urlopen(current_AdminDirURL + "/services/" + current_FolderName + "/" +
#                                        current_ServiceName + "." + current_ServiceType + "/start?", startParams).read()
#         startResponseJSON = json.loads(startResponse)
#         startStatus = startResponseJSON["status"]
#
#         if startStatus == "success":
#             logging.info("SMAP start Service: Started service " + str(current_FolderName) + "/" + str(
#                 current_ServiceName) + "/" + str(current_ServiceType))
#         else:
#             logging.warning("SMAP start Service: UNABLE TO START SERVICE " + str(current_FolderName) + "/" + str(
#                 current_ServiceName) + "/" + str(current_ServiceType) + " STATUS = " + startStatus)
#     except Exception as e:
#         logging.error("SMAP start Service: ### ERROR ### - Start Service failed for " + str(
#             current_ServiceName) + ", System Error Message: " + str(e))


def refreshService3x():
    """
    # Uses urllib.parse and urllib.request libraries to send requests to the configured ArcGIS Server to stop,
    #  then restart the specified Image Service.
    #
    """
    svc_AdminDirURL = myConfig['svc_AdminDirURL']
    svc_Username = myConfig['svc_Username']
    svc_Password = myConfig['svc_Password']
    svc_FolderName = myConfig['svc_FolderName']
    svc_ServiceName = myConfig['svc_ServiceName']
    svc_ServiceType = myConfig['svc_ServiceType']

    # Try and stop the service
    try:
        # Get a token from the Administrator Directory
        tokenParams = urllib.parse.urlencode(
            {"f": "json", "username": svc_Username, "password": svc_Password, "client": "requestip"})
        tokenParams = tokenParams.encode('ascii')
        tokenResponse = urllib.request.urlopen(svc_AdminDirURL + "/generateToken?", tokenParams).read()
        tokenResponseJSON = json.loads(tokenResponse)
        token = tokenResponseJSON["token"]

        # Attempt to stop the current service
        stopParams = urllib.parse.urlencode({"token": token, "f": "json"})
        stopParams = stopParams.encode('ascii')
        stopResponse = urllib.request.urlopen(
            svc_AdminDirURL + "/services/" + svc_FolderName + "/" + svc_ServiceName + "." + svc_ServiceType + "/stop?",
            stopParams).read()
        stopResponseJSON = json.loads(stopResponse)
        stopStatus = stopResponseJSON["status"]

        if stopStatus != "success":
            logging.warning("WARNING: UNABLE TO STOP SERVICE " + str(svc_FolderName) + "/" + str(
                svc_ServiceName) + "/" + str(svc_ServiceType) + " STATUS = " + stopStatus)
        else:
            logging.info("Service: " + str(svc_ServiceName) + " has been stopped.")

    except Exception as e:
        logging.error("### ERROR ### - Stop Service failed for " + str(
            svc_ServiceName) + ", System Error Message: " + str(e))

    # Try and start the service
    try:
        # Get a token from the Administrator Directory
        tokenParams = urllib.parse.urlencode(
            {"f": "json", "username": svc_Username, "password": svc_Password, "client": "requestip"})
        tokenParams = tokenParams.encode('ascii')
        tokenResponse = urllib.request.urlopen(svc_AdminDirURL + "/generateToken?", tokenParams).read()
        tokenResponseJSON = json.loads(tokenResponse)
        token = tokenResponseJSON["token"]

        # Attempt to start the current service
        startParams = urllib.parse.urlencode({"token": token, "f": "json"})
        startParams = startParams.encode('ascii')
        startResponse = urllib.request.urlopen(
            svc_AdminDirURL + "/services/" + svc_FolderName + "/" + svc_ServiceName + "." + svc_ServiceType + "/start?",
            startParams).read()
        startResponseJSON = json.loads(startResponse)
        startStatus = startResponseJSON["status"]

        if startStatus == "success":
            logging.info("Started service " + str(svc_FolderName) + "/" + str(
                svc_ServiceName) + "/" + str(svc_ServiceType))
        else:
            logging.warning("WARNING: UNABLE TO START SERVICE " + str(svc_FolderName) + "/" + str(
                svc_ServiceName) + "/" + str(svc_ServiceType) + " STATUS = " + startStatus)
    except Exception as e:
        logging.error("### ERROR ### - Start Service failed for " + str(
            svc_ServiceName) + ", System Error Message: " + str(e))


def cleanExtractFolder():
    # Clean out the extract folder
    folder = myConfig['extract_Folder']
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            logging.error('### Error occurred in cleanExtractFolder removing files ###, %s' % e)
    try:
        shutil.rmtree(folder + 'info', ignore_errors=True)
    except Exception as e:
        logging.error('### Error occurred in cleanExtractFolder removing info folder ###, %s' % e)
    try:
        shutil.rmtree(folder + 'temp', ignore_errors=True)
    except Exception as e:
        logging.error('### Error occurred in cleanExtractFolder removing temp folder ###, %s' % e)


def deleteOutOfDateRasters(mymosaicDS):
    # Delete outdated files from the mosaic dataset. a.) remove raster entries, b.) remove files.
    try:
        earlier = datetime.datetime.now() - datetime.timedelta(days=90)
        query = "DateObtained < date '" + earlier.strftime('%Y-%m-%d') + "'"
        logging.info('Removing rasters from Mosaic DS where: ' + query)
        arcpy.RemoveRastersFromMosaicDataset_management(mymosaicDS, query,
                                                        "UPDATE_BOUNDARY", "MARK_OVERVIEW_ITEMS",
                                                        "DELETE_OVERVIEW_IMAGES")
        files = glob.glob(myConfig['finalTranslateFolder'] + "\\*.tif")
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
    except Exception as e:
        logging.error('### Error occurred in deleteOutOfDateRasters ###, %s' % e)


def create_token(uid, pswd):
    op=None
    try:
        # import XML Element Tree
        from xml.etree.ElementTree import Element, SubElement, Comment, tostring

        # Find IP address
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)

        # Create XML input
        token = Element('token')
        username = SubElement(token, 'username')
        username.text = uid
        password = SubElement(token, 'password')
        password.text = pswd
        client_id = SubElement(token, 'client_id')
        client_id.text = 'NSIDC_client_id'
        user_ip_address = SubElement(token, 'user_ip_address')
        user_ip_address.text = IP
        xml = (tostring(token, encoding='us-ascii', method='xml'))
        # Request token from EarthData website using Basic HTTP Authentication
        # The max limit for the number of tokens is 2 per user.
        token = requests.post('https://urs.earthdata.nasa.gov/api/users/token', data=xml, auth=HTTPBasicAuth(username.text, password.text))
        output = token.text
        op=json.loads(output)
        tokenval = op["access_token"]
        return tokenval
    except Exception as e:
        logging.error(op)


# *********************************************SCRIPT ENTRY POINT*************************************
# ************************************************INIT PROCESS****************************************
print("SMAP ETL Started")
pkl_file = open('config.pkl', 'rb')
myConfig = pickle.load(pkl_file)
pkl_file.close()
logDir = myConfig['logFileDir']
logging.basicConfig(filename=logDir + '\\SMAP_log_' + datetime.date.today().strftime('%Y-%m-%d') + '.log',
                    level=logging.DEBUG,
                    format='%(asctime)s: %(levelname)s --- %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info('******************************SMAP ETL Started************************************************')
mosaicDS = myConfig['mosaicDS']
numProcessed = 0
# ************************************************Extract PROCESS****************************************
# DEBUGGING CODE!!!
# theStartDate = datetime.datetime.strptime("2022/02/26", "%Y/%m/%d")
theStartDate = GetStartDateFromdb(mosaicDS)  # Get the last raster date from the Mosaic DS...

if theStartDate is None:
    logging.warning('### ERROR### SMAP ETL did not run because could not determine start date.')
else:
    logging.info('Last Date Entry in Database: %s' % theStartDate.strftime('%Y-%m-%d'))

    logging.info('---------- Generating CMR ECHO API token ----------')
    print("--- Generating CMR ECHO API token ---")
    # LG 3/25/2019 - Request CMR ECHO API token. Requires "EarthData" (https://urs.earthdata.nasa.gov/) login.
    # Tokens are valid for 30 days. Grab one here and use it multiple times below.
    newtoken = create_token(myConfig['EarthData_User'], myConfig['EarthData_Pass'])

    logging.info('---------- Beginning File Downloads ----------')
    print("--- Beginning File Downloads ---")

    # DEBUGGING CODE!!! Only test a few days at a time...
    # twoDays = datetime.timedelta(days=2)
    # StartDatePlus2 = theStartDate + twoDays
    # while theStartDate.date() < StartDatePlus2.date():
    while theStartDate.date() < datetime.date.today():
        theStartDate += datetime.timedelta(days=1)
        tempDate = theStartDate.strftime('%Y-%m-%d')
        print(tempDate)

        # Check URL for granule
        # 6/15/2018 - Remove version parameter as the version changes from time to time...
        # granulesUrl = "https://cmr.earthdata.nasa.gov/search/granules?short_name=SPL3SMP&version=004&temporal="+tempDate+"T00:00:01Z/"+tempDate+"T23:59:59Z"
        granulesUrl = "https://cmr.earthdata.nasa.gov/search/granules?short_name=SPL3SMP&temporal=" + \
                      tempDate + "T00:00:01Z/" + tempDate + "T23:59:59Z"
        response = urllib.request.urlopen(granulesUrl)
        html_bytes = response.read()
        html = html_bytes.decode("utf-8")     # LG 2/23/2022 Added decode of the returned byte str because find was raising an error...
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
            # url = 'https://n5eil01u.ecs.nsidc.org/egi/request?short_name=SPL3SMP&format=GeoTIFF&time=2016-12-13,2016-12-13&Coverage=/Soil_Moisture_Retrieval_Data_AM/soil_moisture&token=' + str(newtoken) + '&email=lance.gilliland@nasa.gov&FILE_IDS=' + finalName
            # 9/2/2019 - With version 6 of the data starting 8/13/2019, we now have to specify the
            # "subagent type" to get the .tif post processed file

            # url = 'https://n5eil01u.ecs.nsidc.org/egi/request?short_name=SPL3SMP&format=GeoTIFF&time=2016-12-13,2016-12-13&Coverage=/Soil_Moisture_Retrieval_Data_AM/soil_moisture&token=' + str(
            #     newtoken) + '&email=lance.gilliland@nasa.gov&SUBAGENT_ID=HEG&FILE_IDS=' + finalName

            url='https://n5eil01u.ecs.nsidc.org/egi/request?short_name=SPL3SMP&format=GeoTIFF&time=2016-12-13,2016-12-13&Coverage=/Soil_Moisture_Retrieval_Data_AM/soil_moisture' \
                '&email=lance.gilliland@nasa.gov&SUBAGENT_ID=HEG&FILE_IDS=' + finalName
            try:
                auth_token =newtoken
                req = urllib.request.Request(url, None, {"Authorization": "Bearer %s" % auth_token})
                response = urllib.request.urlopen(req)
            except Exception as e:
                print(e)
            # NOTE! The source file might actually be missing from the DAAC and if so, the response will be a
            # URL XML response.  So check the MIME type to see if the response is other than application/octet-stream.
            # If so, we know it is not the desired raster file.
            # if 'xml' in data[:20]:    # This worked in py 2.7, but not in 3.x - so need to check content type
            info = response.info()
            # mainmimetype = info.get_content_maintype()
            if info.get_content_maintype() != 'application':
                # UH OH - response file should be a binary raster file...
                # ...this means that the raster file must not exist for download.
                logging.warning('### File is NOT a valid raster! Skipping: %s ###' % rasterFile)
            else:
                # Assume that the returned file was a raster and downloaded. Save it.
                data = response.read()
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
    print("--- Loading new Rasters to Mosaic ---")
    LoadRasters(myConfig['extract_Folder'])

    # Cleanup the temporary extract folder(s)
    logging.info('---------- Cleaning up Processing Folder ----------')
    print("--- Cleaning up Processing Folder ---")
    cleanExtractFolder()

    # Remove/delete the mosaic dataset entries older than the agreed upon timeframe.
    logging.info('---------- Removing out of date Rasters from Mosaic ----------')
    print("--- Removing out of date Rasters from Mosaic ---")
    deleteOutOfDateRasters(mosaicDS)

# Refresh the service to reflect any changes... (note - even if files were not added, some could have been removed.)
refreshService3x()

#method to revoke an existing token in order to avoid the max token limit error
def revoke_token(tkn):
    uid, pswd = myConfig['EarthData_User'], myConfig['EarthData_Pass']
    from xml.etree.ElementTree import Element, SubElement, Comment, tostring

    hostname = socket.gethostname()
    IP = socket.gethostbyname(hostname)

    # Create XML input
    token = Element('token')
    username = SubElement(token, 'username')
    username.text = uid
    password = SubElement(token, 'password')
    password.text = pswd
    client_id = SubElement(token, 'client_id')
    client_id.text = 'NSIDC_client_id'
    user_ip_address = SubElement(token, 'user_ip_address')
    user_ip_address.text = IP
    xml = (tostring(token, encoding='us-ascii', method='xml'))
    # post call to the api to revoke an existing token. Here we are passing the token we created to the following URL along with Basic HTTP Authentication
    token = requests.post('https://urs.earthdata.nasa.gov/api/users/revoke_token?token='+tkn, data=xml,
                      auth=HTTPBasicAuth(username.text, password.text))
    logging.info('---------- Successfully revoked the created token ----------')
logging.info('---------- Revoking the token from EarthData in order to avoid reaching max limit of tokens ----------')
revoke_token(newtoken)

logging.info('Total number of files downloaded for this run: %s' % numProcessed)
logging.info('******************************SMAP ETL Finished************************************************')
print('SMAP ETL Finished')
