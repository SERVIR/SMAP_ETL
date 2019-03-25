import pickle

mydict = {'extract_Folder': 'z:\Temp\SMAP_Extract\\',
          'mosaicDS': 'E:\SERVIR\Data\Global\soil_moisture.gdb\soil_moisture',
          'finalTranslateFolder': 'E:\SERVIR\Data\Global\soil_moisture',
          'logFileDir': 'D:\Logs\ETL_Logs\SMAP',
          'current_AdminDirURL': 'https://gis1.servirglobal.net/arcgis/admin',
          'current_Username': 'YOUR_USERNAME',
          'current_Password': 'YOUR_PASSWORD',
          'current_FolderName': 'Global',
          'current_ServiceName': 'SoilMoisture',
          'current_ServiceType': 'MapServer',
          'EarthData_User': 'YOUR_USERNAME',
          'EarthData_Pass': 'YOUR_PASSWORD'
          }
output = open('config.pkl', 'wb')
pickle.dump(mydict, output)
output.close()
