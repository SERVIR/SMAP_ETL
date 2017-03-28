import pickle
import csv
import binascii
mydict = {'extract_Folder': 'e:\Temp\SMAP_Extract\\', 'mosaicDS': 'E:\SERVIR\Data\Global\soil_moisture.gdb\soil_moisture', 'finalTranslateFolder': 'E:\SERVIR\Data\Global\soil_moisture', 'logFileDir': 'D:\Logs\ETL_Logs\SMAP','current_AdminDirURL':'http://localhost:6080/arcgis/admin','current_Username':'YOUR_USERNAME','current_Password':'YOUR_PASSWORD','current_FolderName':'Global','current_ServiceName':'SoilMoisture','current_ServiceType':'MapServer'}
output = open('config.pkl', 'wb')
pickle.dump(mydict, output)
output.close()