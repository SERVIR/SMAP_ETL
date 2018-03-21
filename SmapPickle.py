import pickle
import csv
import binascii

mydict = {'extract_Folder': 'E:\Code\SMAP\Global\TempExtractFolder\\',
          'mosaicDS': 'E:\Code\SMAP\Global\soil_moisture.gdb\soil_moisture',
          'finalTranslateFolder': 'E:\Code\SMAP\Global\soil_moisture',
          'logFileDir': 'E:\Code\SMAP_ETL',
          'current_AdminDirURL': 'https://gis1.servirglobal.net/arcgis/admin',
          'current_Username': 'YOUR_USERNAME',
          'current_Password': 'YOUR_PASSWORD',
          'current_FolderName': 'Global',
          'current_ServiceName': 'SoilMoisture',
          'current_ServiceType': 'MapServer'}
output = open('config.pkl', 'wb')
pickle.dump(mydict, output)
output.close()
