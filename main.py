import time
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

ApiInstance.start()

i = 1

while i < 6:
    empty = 'None'
    conn = psycopg2.connect(dbname=os.getenv("DBNAME"), user=os.getenv("USER"), password=os.getenv("PASSWORD"), host=os.getenv("HOST"), port=os.getenv("PORT"))
    cur = conn.cursor()

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

        sql = "SELECT COUNT(*) FROM historic_data WHERE date = '" + dt_string + "';"
        cur.execute(sql)
        countedRecordsResult = cur.fetchone()
        countedRecords = int(countedRecordsResult[0])

        if countedRecords < 1:
            print("The total energy consumption for", dt_string, "is", energy_yesterday['value'])
            sql = "INSERT INTO historic_data VALUES ('" + energy_today_value + "', '" + dt_string + "');"
            cur.execute(sql)
        else:
            print("Record for yesterday already present, skipping")

    if energy_today_value != empty:

        now = datetime.now()

        dt_string = now.strftime("%Y/%m/%d %H:%M:%S")
        print("date and time =", dt_string)
        print("The energy consumption at", dt_string, "is", energy_today['value'])
        print("The water temperature is " + water_temp_value)
        print("The outside temperature is " + outside_temp_value)
        sql = "INSERT INTO current_data VALUES ('" + energy_today_value + "', '" + dt_string + "', '" + outside_temp_value + "', '" + water_temp_value + "');"
        cur.execute(sql)

    conn.commit()
    cur.close()
    conn.close()
    time.sleep(30)
