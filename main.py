import logging
import time
import traceback

import psycopg2

from aristonremotethermo.ariston import AristonHandler
from datetime import datetime
from dateutil.relativedelta import relativedelta

from dotenv import load_dotenv
import os

load_dotenv()

ApiInstance = AristonHandler(
    username=os.getenv("API_KEY"),
    password=os.getenv("API_SECRET"),
    period_get_request=35,
    period_set_request=35,
    sensors=['ch_energy2_today',
             'ch_energy2_yesterday',
             'ch_flow_temperature',
             'outside_temperature']
)

try:
    ApiInstance.start()

except Exception as e:
    print("Error connecting to the Ariston API")
    logging.error(traceback.format_exc())

i = 1

while i < 6:
    empty = 'None'

    try:
        conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("USER"), password=os.getenv("PASSWORD"),
                                host=os.getenv("HOST"), port=os.getenv("PORT"))
        cur = conn.cursor()
    except Exception as e:
        print("Error connecting to Database")
        logging.error(traceback.format_exc())

    energy_yesterday = ApiInstance.sensor_values.get('ch_energy2_yesterday')

    energy_today = ApiInstance.sensor_values.get('ch_energy2_today')
    outside_temp = ApiInstance.sensor_values.get('outside_temperature')
    water_temp = ApiInstance.sensor_values.get('ch_flow_temperature')

    energy_yesterday_value = str(energy_yesterday['value'])
    energy_today_value = str(energy_today['value'])
    outside_temp_value = str(outside_temp['value'])
    water_temp_value = str(water_temp['value'])

    if energy_yesterday_value != empty:
        currentTimeDate = datetime.now() - relativedelta(days=1)
        dt_string = currentTimeDate.strftime("%Y/%m/%d")

        countedRecords = 0

        try:
            sql = "SELECT COUNT(*) FROM historic_data WHERE date = '" + dt_string + "';"
            cur.execute(sql)
            countedRecordsResult = cur.fetchone()
            countedRecords = int(countedRecordsResult[0])
        except Exception as e:
            print("Error reading historic_data table")
            logging.error(traceback.format_exc())

        if countedRecords < 1:
            print("The total energy consumption for", dt_string, "is", energy_yesterday['value'])
        try:
            sql = "INSERT INTO historic_data VALUES ('" + energy_today_value + "', '" + dt_string + "');"
            cur.execute(sql)
        except Exception as e:
            print("Error writing data to historic_data table")
            logging.error(traceback.format_exc())
        else:
            print("Record for yesterday already present, skipping")

    if energy_today_value != empty:
        # datetime object containing current date and time
        now = datetime.now()

        # dd/mm/YY H:M:S
        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        print("date and time =", dt_string)
        print("The energy consumption at", dt_string, "is", energy_today['value'])
        print("The water temperature is " + water_temp_value)
        try:
            sql = "INSERT INTO current_data VALUES ('" + energy_today_value + "', '" + dt_string + "', '" + outside_temp_value + "', '" + water_temp_value + "');"
            cur.execute(sql)
        except Exception as e:
            print("Error writing data to current_data table")
            logging.error(traceback.format_exc())

    try:
        conn.commit()
    except Exception as e:
        print("Error committing data to database")
        logging.error(traceback.format_exc())

    try:
        cur.close()
        conn.close()
    except Exception as e:
        print("Error in closing database connection")
        logging.error(traceback.format_exc())

    time.sleep(300)
