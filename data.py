import csv
import urllib2
from datetime import datetime
from helpers import get_db, Logger


class Data:
    """ Fetch data from API and Insert that data to DB tables
    """

    column_check_date = 'last_modified'  # DB column name from which we calculate upto which previous data was collected
    nmk_id_field = 'id'  # DB column name for id

    def __init__(self, searchId, table_name):
        """ Initializes the API url from which data is fetched.
            Parameter: searchId
        """
        self.searchId = searchId
        # ignore date parameter for item_master_db and inventory_master_db tables
        if searchId == "347" or searchId == "358" or searchId == "361":
            self.url = 'https://forms.na2.netsuite.com/app/site/hosting/scriptlet.nl?script=96&deploy=1' \
                       '&compid=4122587&h=b8c538c9142b9c5833aa&searchId=' + self.searchId
        else:
            startDate = str(self.get_max_datetime(table_name).strftime('%m/%d/%Y'))
            endDate = str(datetime.today().strftime('%m/%d/%Y'))
            self.url = 'https://forms.na2.netsuite.com/app/site/hosting/scriptlet.nl?script=96&deploy=1' \
                    '&compid=4122587&h=b8c538c9142b9c5833aa&searchId=' + self.searchId +'&startDate=' + startDate + \
                       '&endDate=' + endDate

    def __get_datetime(self, value_string):
        """ Returns datetime object from a string which contains datetime value in a the format MM/DD/YYYY hh:mm am
            Parameter: string value of datetime
        """
        return datetime.strptime(value_string, '%m/%d/%Y %I:%M %p')

    def __append_id(self, id_prefix, row, _id, table_name):
        """ Returns row tuple after appending generated id with prefix
            Parameters: prefix of id
                        row
                        id
        """
        row.append(id_prefix + '{0:08d}'.format(_id))
        if table_name == "inventory_master_db":
            row.append(datetime.strptime(str(datetime.now()), '%Y-%m-%d %H:%M:%S.%f').strftime('%m/%d/%Y'))
        return tuple(row)

    def read_data(self):
        """ Returns full data set after fetching for API
        """
        print "getting data from url: " + self.url
        try:
            response = urllib2.urlopen(self.url)
            data = csv.reader(response)
            return data
        except Exception as e:
            print "Exception while calling API: " + e


    def truncate_table(self, table_name):
        """ Truncates a given table
            Parameter: table name
        """
        db = get_db()
        query = "truncate table {}".format(table_name)
        cursor = db.cursor()
        cursor.execute(query)
        db.close()

    def __alter_table_collumn_add(self, db, table_name, new_collumns):
        """ Alters a table by adding new columns where data type will always be varchar(500)
            Parameters: a database connection object
                        name of table
                        list of new columns to be added
        """
        for item in new_collumns:
            print "adding new column '{}' to '{}'".format(item, table_name)
            Logger.log('info', "adding new column '{}' to '{}'".format(item, table_name))
            query = '''ALTER TABLE {} ADD {} varchar(500)'''.format(table_name, item)
            db.cursor().execute(query)
            print "column added."
            Logger.log('info', "column added.")

    def __get_current_max_id(self, db, prefix, table_name):
        """ Returns maximum id (excluding prefix) present in a given table
            Parameters: a database connection object
                        prefix of id
                        name of the table
        """
        query = "select max(id) from {}".format(table_name)
        cursor = db.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        result = result[0][0]
        if result is None:
            return 0
        else:
            length_prefix = len(prefix)
            return result[length_prefix:]

    def get_max_datetime(self, table_name):
        """ Calculates and returns the maximum date up to which data is already present in DB
            Parameter: name of table
        """
        db = get_db()
        query = '''select {} from {}'''.format(self.column_check_date, table_name)
        cursor = db.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            dates = list()
            for item in result:
                dates.append(self.__get_datetime(item[0]))
            db.close()
            return max(dates)
        except Exception as e:
            try:
                db.close()
            except:
                pass
            print "Exception while generating max date :", e
            Logger.log('error', "Exception while generating max date : {}.".format(e))
            return None

    def insert_db(self, data, table_name, data_updated_till, id_prefix):
        """ Inserts data to a given table
            Parameters: data from the API
                        name of table
                        maximum datetime up to which data is already update in the table
                        prefix of id of table
        """
        print "inside insert_db method"
        db = get_db()

        # Fetching columns in API
        fieldnames_api = data.next()
        fieldnames_api = [item.lower().replace(" : ", "_").replace(" ", "_").replace("-", "_") for item in
                          fieldnames_api]

        try:
            column_check_date_index = fieldnames_api.index(self.column_check_date)
        except:
            print "WARNING !! {} not found in API response, GOING TO INSERT ALL DATA TO DATABASE.".format(
                ' '.join(self.column_check_date.split('_')))
            Logger.log('warning', "{} not found in API response, GOING TO INSERT ALL DATA TO DATABASE.".format(
                ' '.join(self.column_check_date.split('_'))))
            column_check_date_index = None

        # Fetching columns already present in out DB table
        query = "show columns from {}".format(table_name)
        cursor = db.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        fieldnames_db = list()
        for item in result[1:]:
            fieldnames_db.append(item[0])

        difference = list(set(fieldnames_api) - set(fieldnames_db))
        if len(difference) > 0:
            print "found new column(s)."
            Logger.log('info', "found new column(s).")
            try:
                self.__alter_table_collumn_add(db, table_name, difference)
            except Exception as e:
                print "Exception during alter table :", e
                Logger.log('error', "Exception during alter table : {}".format(e))
                return None

        # fields structure to build the insert query
        if table_name == "inventory_master_db":
            fields = "%s, " * (len(fieldnames_api) + 2)
        else:
            fields = "%s, " * (len(fieldnames_api) + 1)
        fields = fields[:-2]



        max_id = self.__get_current_max_id(db, id_prefix, table_name)
        max_id = int(max_id)

        # fields to build the query string for building the insert query
        query_str = ''

        for item in fieldnames_api:
            query_str += item + ", "
        query_str = query_str + self.nmk_id_field
        if table_name == "inventory_master_db":
            query_str = query_str + ", last_modified"

        # building the final insert query
        query = '''insert into {} ({}) values ({})'''.format(table_name, query_str, fields)

        cursor = db.cursor()

        # Append id in each row of data to be inserted in DB table
        final_data = list()
        for row in data:
            row = [str(item) for item in row]
            if (column_check_date_index is not None) and (data_updated_till is not None):
                try:
                    current_row_date_value = row[column_check_date_index]
                    date = self.__get_datetime(current_row_date_value)
                except Exception as e:
                    continue
                if data_updated_till < date:
                    max_id += 1
                    final_data.append(self.__append_id(id_prefix, row, max_id, table_name))
            else:
                max_id += 1
                final_data.append(self.__append_id(id_prefix, row, max_id, table_name))

        if (column_check_date_index is not None) and (data_updated_till is not None):
            print "Number of new row(s) found : {}".format(len(final_data))
            Logger.log('info', "Number of new row(s) found : {}".format(len(final_data)))

        # If we have values to be inserted in table then we insert all data at once
        if len(final_data):
            try:
                print "inserting data into table '{}'".format(table_name)
                Logger.log('info', "inserting data into table '{}'".format(table_name))
                row_count = cursor.executemany(query, final_data)
                db.commit()
                print "Number of row(s) inserted : {}".format(row_count)
                Logger.log('info', "Number of row(s) inserted : {}".format(row_count))
            except Exception as e:
                print "Database insertion exception :", e
                Logger.log('error', "Database insertion exception : {}".format(e))

        db.close()
