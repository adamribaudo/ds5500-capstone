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
project_input_dataset = "ds5500:kkbox."#"ds5500:beam." #"ds5500:kkbox."
user_logs_tbl = project_input_dataset  + "user_logs_dataprep"#"user_logs_fake" # "user_logs_dataprep"
users_tbl = project_input_dataset + "members"#"users_fake" # "members"
transactions_tbl = project_input_dataset + "transactions_v2"#"transactions_fake" # "transactions_v2"

project_output_dataset = "ds5500:beam."
users_output_schema = "msno:STRING,city:INTEGER,bd:INTEGER,gender:STRING,registered_via:INTEGER,registration_init_time:INTEGER"
users_output_tbl = project_output_dataset + "users_fake_output"
features_output_schema = "msno:STRING,city:INTEGER,is_churn:INTEGER,feature_discount_mean:FLOAT64"
features_output_train_tbl = project_output_dataset + "features_output_train"
features_output_val_tbl = project_output_dataset + "features_output_val"
features_output_test_tbl = project_output_dataset + "features_output_test"

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
  """Parses the raw transaction data into dictionary.

   msno	payment_method_id	payment_plan_days	plan_list_price	actual_amount_paid	is_auto_renew	transaction_date	membership_expire_date	is_cancel
  """
  def __init__(self):
    # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
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
    # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
    # super(ParseGameEventFn, self).__init__()
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
    # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
    # super(ParseGameEventFn, self).__init__()
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
    except:  # pylint: disable=bare-except
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
        # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
        # super(HourlyTeamScore, self).__init__()
        beam.PTransform.__init__(self)
        self.min_date = min_date
    def expand(self, pcoll):
        # TODO user logs data in BQ uses DATETIME for the 'date' column
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
          p | 'Query Users table in BQ' >> beam.io.Read(beam.io.BigQuerySource(table=users_tbl)) 
        | 'Parse Users' >> beam.ParDo(ParseUsersBQ())
        )

      # Read raw transactions
      transactions = (
            p | 'Query Transactions table in BQ' >> beam.io.Read(beam.io.BigQuerySource(table=transactions_tbl))
            | beam.ParDo(ParseTransactionsBQ())
        )
      
      ## Find MNSOs with an expiration in the target month
      target_month_start = 20170201
      target_month_end = 20170228
      final_month_start = 20170303
      final_month_end = 20170331
      msnosWithValidExpiration = (
            transactions | 'Find Expirations in Feb' >> beam.Filter(lambda elem: elem['membership_expire_date'] >= target_month_start and elem['membership_expire_date'] <= target_month_end)
            | 'Select MSNO Column' >> beam.Map(lambda elem: (elem['msno']))
            | 'Return Distinct MSNOs' >> beam.transforms.util.Distinct()
        )
      
      # Filter transactions based on users with correct expiration to help with future filtering of user logs
      transactionsFromUsersWithExpiration = (
        transactions | 'Filter transactions on users with valid expirations' >> beam.Filter(
            lambda transaction,
            msnosWithValidExpiration: transaction['msno'] in msnosWithValidExpiration,
            msnosWithValidExpiration=beam.pvalue.AsIter(msnosWithValidExpiration),
            ) 
        )
      
      # Find users who did not churn based on transaction records to later assign 1 or 0
      notChurnedUsers = (
        transactionsFromUsersWithExpiration | 'Filter Transactions in Feb AND Expiration is not Feb' >> 
        beam.Filter(lambda elem: elem['transaction_date'] >= target_month_start 
                    and elem['transaction_date'] <= final_month_end 
                    and elem['membership_expire_date'] >= final_month_start
                    and elem['is_cancel'] == 0)
        | 'Select No Churn MSNOs' >> beam.Map(lambda elem: (elem['msno'])) 
        | 'Return Distinct No Churn MSNOs' >> beam.transforms.util.Distinct()
            )
      
      # Set users in not churned to is_churn = 0 otherwise is_churn = 1
      userLabelsFromTransactions = (
            msnosWithValidExpiration | 'Set is_churn' >> beam.Map(
            lambda msnoWithValidExpiration,
            notChurnedUsers: (msnoWithValidExpiration,0) if msnoWithValidExpiration in notChurnedUsers else (msnoWithValidExpiration,1),
            notChurnedUsers=beam.pvalue.AsIter(notChurnedUsers),
            ) 
            )

      # Generate (msno,min_date) from user logs for users with min_date of <= target_min_log_date
      target_min_log_date = 20150501
      validUsersFromUserLogs = (
        p | GenerateValidUsersFromLogs(target_min_log_date)
        )

      ## Generate (msno,is_churn) with inner join between valid users based on transactions and user logs
      validUserLabels = ({'left': userLabelsFromTransactions, 'right': validUsersFromUserLogs} | beam.CoGroupByKey() | beam.ParDo(InnerJoinValidUsers())
                        )
      
      # Generate just the valid MSNOs
      validMSNOs = validUserLabels | "Get MSNO from valid user labels" >> beam.Keys()

      # Regenerate valid transactions based on new understanding of what a valid user is
      # TODO make this a class or function
      transactionsFromValidUsers = (
        transactions | 'Filter transactions on valid users ' >> beam.Filter(
            lambda transaction,
            validMSNOs: transaction['msno'] in validMSNOs,
            validMSNOs=beam.pvalue.AsIter(validMSNOs),
            ) 
        )


      ####
      ## Feature engineering
      ####

      # Always Auto-Renew: 1 if the user consistently have auto-renew on all transactions. 0 otherwise
      feature_autorenew = (
      transactionsFromValidUsers | beam.Map(lambda x: (x["msno"],x["is_auto_renew"])) | beam.CombinePerKey(min))

      # Discount amount mean
      feature_discount_mean = (
      transactionsFromValidUsers | beam.Map(lambda x: (x["msno"],x["discount_amount"])) | beam.CombinePerKey(AverageFn())
      )
      
      ###
      ## Combine all data
      ###

      # Combine all user features with users and filter users with no data
      allOutput =( 
          {'is_churn': validUserLabels, 
           'user_demo': users, 
           'feature_autorenew':feature_autorenew,
           'feature_discount_mean':feature_discount_mean} 
          | "Combine users, labels, and features" >> beam.CoGroupByKey()
          | "Filter out empty entries" >> beam.Filter(lambda x: len(x[1]["is_churn"]) and len(x[1]["user_demo"]) > 0 and len(x[1]["feature_autorenew"]) > 0 and len(x[1]["feature_discount_mean"]) > 0)
          | "Flatten data to single dictionary for BQ" >> beam.Map(lambda x: {"msno":x[0], 
                                                                              "city":x[1]["user_demo"][0]["bd"],
                                                                              "is_churn":x[1]["is_churn"][0],
                                                                              "feature_discount_mean":x[1]["feature_discount_mean"][0]
                                                                              })
          ) 

      # partition into train/val/test based on random float
      train, val, test = (allOutput | beam.Partition(train_test_split, 3))
      
      #output to BQ
      val| "Validation output" >> beam.io.WriteToBigQuery(table=features_output_val_tbl,schema=features_output_schema)
      train | "Training output" >> beam.io.WriteToBigQuery(table=features_output_train_tbl,schema=features_output_schema)
      test | "Testing output" >> beam.io.WriteToBigQuery(table=features_output_test_tbl,schema=features_output_schema)

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()