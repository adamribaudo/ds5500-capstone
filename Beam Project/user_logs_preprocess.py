# pytype: skip-file
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import csv
import logging
import sys
import time
from datetime import datetime
from random import random
import os
import apache_beam as beam
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions

# Set GCP credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\Owner\\Google Drive\\Northeastern\\DS 5500 Capstone\\ds5500-capstone\\ds5500-7e5f8aa07468.json"

# TODO paramaterize these
project_input_dataset = "ds5500:beam." #"ds5500:beam." #"ds5500:kkbox."
project_input_dataset_standard = "ds5500.beam."

user_logs_tbl = "user_logs_fake" #"user_logs_fake" # "user_logs"
users_tbl = "users_fake" #"users_fake" # "members"
transactions_tbl = "transactions_fake" #"transactions_fake" # "transactions_v3"

project_output_dataset = "ds5500:beam."
users_output_schema = "msno:STRING,city:INTEGER,bd:INTEGER,gender:STRING,registered_via:INTEGER,registration_init_time:INTEGER"
users_output_tbl = project_output_dataset + "users_fake_output"
features_output_schema = "msno:STRING,city:INTEGER,feature_autorenew:INTEGER,feature_discount_mean:FLOAT64,is_churn:INTEGER"
name_suffix = str(int(datetime.now().timestamp()))
features_output_train_tbl = project_output_dataset + "features_output_train_" + name_suffix 
features_output_val_tbl = project_output_dataset + "features_output_val_" + name_suffix 
features_output_test_tbl = project_output_dataset + "features_output_test_" + name_suffix 

class AverageFn(beam.CombineFn):
  def create_accumulator(self):
    return (0.0, 0)

  def add_input(self, sum_count, input):
    (sum, count) = sum_count
    return sum + input, count + 1

  def merge_accumulators(self, accumulators):
    sums, counts = zip(*accumulators)
    return sum(sums), sum(counts)

  def extract_output(self, sum_count):
    (sum, count) = sum_count
    return sum / count if count else float('NaN')

class ParseUserLogFn(beam.DoFn):
  """Parses the raw user log data into dictionary.

  Each event line has the following format:
    msno	date	num_25	num_50	num_75	num_985	num_100	num_unq	total_secs
  """
  def __init__(self):
    # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
    # super(ParseGameEventFn, self).__init__()
    beam.DoFn.__init__(self)
    self.num_parse_errors = Metrics.counter(self.__class__, 'num_parse_errors')

  def process(self, elem):
    try:
      row = list(csv.reader([elem]))[0]
      yield {
          'msno': row[0],
          'date': int(row[1]),
          'num_25': int(row[2]),
          'num_50': int(row[3]),
          'num_75': int(row[4]),
          'num_985': int(row[5]),
          'num_100': int(row[6]),
          'num_unq': int(row[7]),
          'total_secs': float(row[8])
      }
    except:  # pylint: disable=bare-except
      # Log and count parse errors
      self.num_parse_errors.inc()
      logging.error('Parse error on "%s"', elem)

class ParseTransactions(beam.DoFn):
  """Parses the raw transaction data into dictionary.

   msno	payment_method_id	payment_plan_days	plan_list_price	actual_amount_paid	is_auto_renew	transaction_date	membership_expire_date	is_cancel
  """
  def __init__(self):
    # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
    beam.DoFn.__init__(self)
    self.num_parse_errors = Metrics.counter(self.__class__, 'num_parse_errors')

  def process(self, elem):
    try:
      row = list(csv.reader([elem]))[0]
      yield {
          'msno': row[0],
          'payment_method_id': int(row[1]),
          'payment_plan_days': int(row[2]),
          'plan_list_price': float(row[3]),
          'actual_amount_paid': float(row[4]),
          'is_auto_renew': int(row[5]),
          'transaction_date': int(row[6]),
          'membership_expire_date': int(row[7]),
          'is_cancel': int(row[8]),
          'discount_amount': float(row[3])-float(row[4]),
      }
    except:  # pylint: disable=bare-except
      # Log and count parse errors
      self.num_parse_errors.inc()
      logging.error('Parse error on "%s"', elem)

class ParseTransactionsBQ(beam.DoFn):
  def __init__(self):
    beam.DoFn.__init__(self)
    self.num_parse_errors = Metrics.counter(self.__class__, 'num_parse_errors')

  def process(self, elem):
    try:
      elem["payment_method_id"] = int(elem["payment_method_id"])
      elem["payment_plan_days"] = int(elem["payment_plan_days"])
      elem["plan_list_price"] = float(elem["plan_list_price"])
      elem["actual_amount_paid"] = float(elem["actual_amount_paid"])
      elem["is_auto_renew"] = int(elem["is_auto_renew"])
      elem["transaction_date"] = int(elem["transaction_date"])
      elem["membership_expire_date"] = int(elem["membership_expire_date"])
      elem["is_cancel"] = int(elem["is_cancel"])
      elem["discount_amount"] = float(elem["plan_list_price"]) - float(elem["actual_amount_paid"])
      elem["registration_init_time"] = int(elem["registration_init_time"])
      elem["registered_via"] = int(elem["registered_via"])

      yield elem
    except:  # pylint: disable=bare-except
      # Log and count parse errors
      self.num_parse_errors.inc()
      logging.error('Parse error on "%s"', elem)
class ParseUsers(beam.DoFn):
  """Parses the raw user data into dictionary.

   msno	city	bd	gender	registered_via	registration_init_time
  """
  def __init__(self):
    beam.DoFn.__init__(self)
    self.num_parse_errors = Metrics.counter(self.__class__, 'num_parse_errors')

  def process(self, elem):
    try:
      row = list(csv.reader([elem]))[0]
      msno = row[0]
      yield (msno,
             {
          'city': int(row[1]),
          'bd': int(row[2]),
          'gender': (row[3]),
          'registered_via': int(row[4]),
          'registration_init_time': int(row[5])
      })

    except:  # pylint: disable=bare-except
      # Log and count parse errors
      self.num_parse_errors.inc()
      logging.error('Parse error on "%s"', elem)

class ParseUsersBQ(beam.DoFn):
  """Parses the BQ rows into key, value pairs.

   msno	city	bd	gender	registered_via	registration_init_time
  """
  def __init__(self):
    beam.DoFn.__init__(self)
    self.num_parse_errors = Metrics.counter(self.__class__, 'num_parse_errors')

  def process(self, elem):
    try:
      
      msno = elem["msno"]
      yield (msno,
             {
          'city': int(elem["city"]),
          'bd': int(elem["bd"]),
          'registered_via': int(elem["registered_via"]),
          'registration_init_time': int(elem["registration_init_time"])
      })
    except:
      # Log and count parse errors
      self.num_parse_errors.inc()
      logging.error('Parse error on "%s"', elem)


# Join together user labels and valid users and return the subset that match (similar to inner join)
class InnerJoinValidUsers(beam.DoFn):
  def process(self, user_data, window=beam.DoFn.WindowParam):
    msno = user_data[0]
    is_churn = user_data[1]["left"]
    min_date = user_data[1]["right"]
    
    # Drop records that are missing data from the left or right
    if len(is_churn) > 0 and len(min_date) > 0:
        # TODO not sure why I need to use 0 index on is_churn
        yield (msno,is_churn[0])

class GenerateValidUsersFromLogs(beam.PTransform):
    def __init__(self, min_date):
        beam.PTransform.__init__(self)
        self.min_date = min_date
    def expand(self, pcoll):
        
        # TODO replace this with single BQ query
        return (pcoll | 'Read User Logs from BQ' >> beam.io.Read(beam.io.BigQuerySource(table=user_logs_tbl))
            | 'ExtractMSNOandDate' >> beam.Map(lambda elem: (elem['msno'],int(elem['date'])))
            | 'FindMinDate' >> beam.CombinePerKey(min)
            | 'FilterStartDate' >> beam.Filter(lambda elem: elem[1] <= self.min_date)
        )


def train_test_split(user, num_partitions):
    rand_float = random()
    # train,val,test:.6, .2, .2 split
    if rand_float < .6:
        return 0
    elif rand_float >=.6 and rand_float < .8:
        return 1
    else:
        return 2

def run(argv=None, save_main_session=True):
  parser = argparse.ArgumentParser()

  parser.add_argument('--dataset',
      type=str,
      required=True,
      help='BigQuery Dataset to write tables to. '
      'Must already exist.')
  parser.add_argument('--table_name',
      default='hourly_scores',
      help='The BigQuery table name. Should not already exist.')


  args, pipeline_args = parser.parse_known_args(argv)

  options = PipelineOptions(pipeline_args)

  google_cloud_options = options.view_as(GoogleCloudOptions)

  google_cloud_options.staging_location = 'gs://arr-beam-test/temp'
  google_cloud_options.temp_location = 'gs://arr-beam-test/temp'
  
  # look into not using public IPs 
  # https://cloud.google.com/dataflow/docs/guides/specifying-exec-params
  # https://cloud.google.com/dataflow/docs/guides/specifying-networks#public_ip_parameter
  # no_use_public_ips The public IPs parameter requires the Beam SDK for Python. The Dataflow SDK for Python does not support this parameter.	

  # We also require the --project option to access --dataset
  if google_cloud_options.project is None:
    parser.print_usage()
    print(sys.argv[0] + ': error: argument --project is required')
    sys.exit(1)

  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  options.view_as(SetupOptions).save_main_session = save_main_session

  with beam.Pipeline(options=options) as p:
      
      # Read users from BQ
      users = (
          p | 'Query Users table in BQ' >> beam.io.Read(beam.io.BigQuerySource(table=project_input_dataset+users_tbl))
          | beam.ParDo(ParseUsersBQ())
          )

      ## Find MNSOs with an expiration in the target month
      # TODO add this to BQ query and parameterize them
      target_month_start = 20170201
      target_month_end = 20170228
      final_month_start = 20170303
      final_month_end = 20170331

      # Read valid user transactions from BQ
      tables_dict = {'users_tbl':project_input_dataset_standard+users_tbl,'transactions_tbl':project_input_dataset_standard+transactions_tbl,'user_logs_tbl':project_input_dataset_standard+user_logs_tbl}
      transactions = (
          p | 'Query valid user transactions' >> beam.io.Read(beam.io.BigQuerySource(query = 
            """#standardSQL
            SELECT t.transaction_date,t.membership_expire_date,t.msno,t.payment_method_id,payment_plan_days,t.plan_list_price,t.actual_amount_paid,t.is_auto_renew,t.is_cancel,m.city,m.bd,m.registered_via,m.registration_init_time

                from `{transactions_tbl}` t
            INNER JOIN `{users_tbl}` m on t.msno = m.MSNO
            where t.msno in
                (SELECT MSNO from `{transactions_tbl}` where membership_expire_date >= 20170201 and membership_expire_date <= 20170228)

            and t.msno in
                (SELECT MSNO from `{user_logs_tbl}` group by MSNO having min(CAST(date as INT64)) <= 20160301 )  """.format(**tables_dict), use_standard_sql=True)) | beam.ParDo(ParseTransactionsBQ())
          )
      
      # Find users who did not churn based on transaction records to later assign 1 or 0
      not_churned_users = (
        transactions | 'Filter Transactions in Feb AND Expiration is not Feb' >> 
        beam.Filter(lambda elem: elem['transaction_date'] >= target_month_start 
                    and elem['transaction_date'] <= final_month_end 
                    and elem['membership_expire_date'] >= final_month_start
                    and elem['is_cancel'] == 0)
        | 'Create key-value pair with 0 for no churn' >> beam.Map(lambda elem: (elem['msno'],0)) 
            )
      
      ####
      ## Feature engineering
      ####

      # Always Auto-Renew: 1 if the user consistently have auto-renew on all transactions. 0 otherwise
      feature_autorenew = (
      transactions | beam.Map(lambda x: (x["msno"],x["is_auto_renew"])) | beam.CombinePerKey(min))

      # Discount amount mean
      feature_discount_mean = (
      transactions | beam.Map(lambda x: (x["msno"],x["discount_amount"])) | beam.CombinePerKey(AverageFn())
      )
      
      #TODO as a last step, combine notChurnedUsers by key, later set any null values to 1 and assume they churned


      ###
      ## Combine all data
      ###

      # Combine all user features with users and filter users with no data
      allOutput =( 
          {'user_demo': users, 
           'feature_autorenew':feature_autorenew,
           'feature_discount_mean':feature_discount_mean,
           'not_churned_users':not_churned_users} 
          | "Combine users, labels, and features" >> beam.CoGroupByKey()
          | "Filter out empty entries" >> beam.Filter(lambda x: len(x[1]["user_demo"]) > 0 and len(x[1]["feature_autorenew"]) > 0 and len(x[1]["feature_discount_mean"]) > 0)
          | "Flatten data to single dictionary for BQ" >> beam.Map(lambda x: {"msno":x[0],
                                                                              "city":x[1]["user_demo"][0]["city"],
                                                                              "feature_autorenew":x[1]["feature_autorenew"][0],
                                                                              "feature_discount_mean":x[1]["feature_discount_mean"][0],
                                                                              # If there is no entry for this MSNO in 'not_churned_users' then is_churn=1
                                                                              "is_churn":int(len(x[1]["not_churned_users"])==0)
                                                                              })
          ) 

      # partition into train/val/test based on random float
      train, val, test = (allOutput | beam.Partition(train_test_split, 3))
      
      #output to BQ
      # write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE causes the function to sleep for 150 seconds to wait for delete to finalize before write

      val| "Validation output" >> beam.io.WriteToBigQuery(table=features_output_val_tbl,schema=features_output_schema)
      train | "Training output" >> beam.io.WriteToBigQuery(table=features_output_train_tbl,schema=features_output_schema)
      test | "Testing output" >> beam.io.WriteToBigQuery(table=features_output_test_tbl,schema=features_output_schema)

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()