Introduction: 
SMAP ETL fetches soil moisture active and passive data from the National Snow and Ice Data Center, processes the data into a geodatabase for use as a WMS.

Instructions to schedule the task on a machine:
1.	Go to SMAPPickle.py and enter your paths and credentials
2.	Save and run SMAPPickle.py. This should generate config.pkl file in your folder
3.	Search for Administrative tools in your machine
4.	Go to Task Scheduler
5.	Click on "Create Task" in the right pane and enter details
6.	Schedule the task in Triggers tab
7.	Upload the SMAP_ETL.bat file in the Actions tab
