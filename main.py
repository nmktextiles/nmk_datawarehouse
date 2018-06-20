import time
import traceback
from flask import Flask
from helpers import get_tables, Logger
from data import Data

app = Flask(__name__)


@app.route("/")
def my_main():
    # if __name__ == '__main__':
    Logger()

    # Loop through all tables provided in config
    for item in get_tables():
        try:
            time.sleep(5)

            print "Search id :", item['search_id']
            Logger.log('info', "Search id : {}".format(item['search_id']))
            searchId = item['search_id']
            table_name = item['table']

            obj = Data(searchId, table_name)
            print "fetching data from API."
            Logger.log('info', "fetching data from API.")
            data = obj.read_data()
            print data
            if data == None:
                print "No response from API"
                Logger.log('warning', "No response from API.")
            else:
                print "data fetched from API."
                Logger.log('info', "data fetched from API.")



            if item.get('truncate'):
                obj.truncate_table(table_name)
                print "table '{}' truncated.".format(table_name)
                Logger.log('info', "table '{}' truncated.".format(table_name))

            print "Calculating date till which data is updated."
            Logger.log('info', "Calculating date till which data is updated.")
            data_updated_till = obj.get_max_datetime(table_name)
            if data_updated_till:
                print "data updated till : {}".format(data_updated_till)
                Logger.log('info', "data updated till : {}".format(data_updated_till))
            else:
                print "WARNING !! Unable to find max date, GOING TO INSERT ALL DATA TO DATABASE."
                Logger.log('warning', "Unable to find max date, GOING TO INSERT ALL DATA TO DATABASE.")

            obj.insert_db(data, table_name, data_updated_till, item['id_prefix'])
            print "Done ...!!"

        except Exception as e:
            print "Exception :", e
            Logger.log('error', "Exception : {}".format(e))
            traceback.print_exc()

        print "\n\n"
    return 'Success'

# app.run(debug=True)
