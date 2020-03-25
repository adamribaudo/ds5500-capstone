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
project_input_dataset = "ds5500:kkbox." #"ds5500:beam." #"ds5500:kkbox."
project_input_dataset_standard = "ds5500.kkbox."

user_logs_tbl = "user_logs" #"user_logs_fake" # "user_logs"
users_tbl = "members" #"users_fake" # "members"
transactions_tbl = "transactions_v3" #"transactions_fake" # "transactions_v3"

project_output_dataset = "ds5500:beam."


name_suffix = str(int(datetime.now().timestamp()))
features_output_train_tbl = project_output_dataset + "features_output_train_" + name_suffix 
features_output_val_tbl = project_output_dataset + "features_output_val_" + name_suffix 
features_output_test_tbl = project_output_dataset + "features_output_test_" + name_suffix 
num_payment_ids = 45

features_output_schema = "msno:STRING,city:INTEGER,feature_autorenew:INTEGER,feature_discount_mean:FLOAT64,is_churn:INTEGER,"
for i in ('25','50','75','985','unq'):
    features_output_schema+=",avg_num_" + i + ":INTEGER"
for i in ('25','50','75','985','unq'):
    features_output_schema+=",sum_num_" + i + ":INTEGER"
for i in range(num_payment_ids):
    features_output_schema+=",payment_method_id_" + str(i+1) + ":INTEGER"


# https://beam.apache.org/releases/pydoc/2.6.0/apache_beam.transforms.core.html#apache_beam.transforms.core.CombineFn
class SummarisePaymentId(beam.CombineFn):
  def create_accumulator(self):
    return [0] * (num_payment_ids+1)

  def add_input(self, payment_ids_list, input):
      # Loop through payment Ids which will be 0 or 1 and add them to total found
      for i in range(num_payment_ids):
          payment_ids_list[i+1] += input[i+1]

      return payment_ids_list
   
  def merge_accumulators(self, accumulators):
      #[sum(x) for x in zip(list1, list2)]
    return [sum(x) for x in zip(*accumulators)]

  def extract_output(self, payment_ids_list):
    # Convert to dictionary:
    #for i in range(num_payment_ids):
        #elem["payment_method_id_"+str(i)] = int(int(elem["payment_method_id"]) == i)
    return payment_ids_list

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

def format_for_BQ(x):
    output = {"msno":x[0],
    "city":x[1]["user_demo"][0]["city"],
    "feature_autorenew":x[1]["feature_autorenew"][0],
    "feature_discount_mean":x[1]["feature_discount_mean"][0],
    # If there is no entry for this MSNO in 'not_churned_users' then is_churn=1
    "is_churn":int(len(x[1]["not_churned_users"])==0)
    }

    # User log features
    for i in ('25','50','75','985','unq'):
        key = "avg_num_" + i
        output.update({key: int(x[1]["feature_user_log_counts"][0][key])})
    for i in ('25','50','75','985','unq'):
        key = "sum_num_" + i
        output.update({key: int(x[1]["feature_user_log_counts"][0][key])})

    # One hot encoding for payment ids
    for i in range(num_payment_ids):
        output.update({"payment_method_id_"+str(i+1): int(x[1]["feature_payment_id_encoded"][0][i+1] >= 1)})

    return output


# Convert a payment ID into a list of integers one-hot encoded to the payment ID
def OneHotPaymentId(elem):
    id = elem["payment_method_id"]
    one_hot_list = [0] * (num_payment_ids+1)
    one_hot_list[id] = 1
    return one_hot_list

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
      elem["is_discount"] = int(elem["discount_amount"] > 0)

      yield elem
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

class ParseUserLogsBQ(beam.DoFn):
  def __init__(self):
    beam.DoFn.__init__(self)
    self.num_parse_errors = Metrics.counter(self.__class__, 'num_parse_errors')

  def process(self, elem):
    try:
      msno = elem["msno"]
      yield (msno,
             {
                 "user_log_entries":elem["user_log_entries"],
                 "avg_num_25":elem["avg_num_25"],
                 "avg_num_50":elem["avg_num_50"],
                 "avg_num_75":elem["avg_num_75"],
                 "avg_num_985":elem["avg_num_985"],
                 "avg_num_100":elem["avg_num_100"],
                 "avg_num_unq":elem["avg_num_unq"],
                 "sum_num_25":elem["sum_num_25"],
                 "sum_num_50":elem["sum_num_50"],
                 "sum_num_75":elem["sum_num_75"],
                 "sum_num_985":elem["sum_num_985"],
                 "sum_num_100":elem["sum_num_100"],
                 "sum_num_unq":elem["sum_num_unq"]
              }
             )
    except:
      # Log and count parse errors
      self.num_parse_errors.inc()
      logging.error('Parse error in User Logs on "%s"', elem)

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
  google_cloud_options.region = "us-east1"
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
      # TODO add these as cmd line arguments
      target_month_start = 20170201
      target_month_end = 20170228
      user_logs_start = 20160301

      # Read valid user transactions from BQ
      query_params = {'users_tbl':project_input_dataset_standard+users_tbl,
                'transactions_tbl':project_input_dataset_standard+transactions_tbl,
                'user_logs_tbl':project_input_dataset_standard+user_logs_tbl,
                'target_month_start':target_month_start,
                'target_month_end':target_month_end,
                'user_logs_start':user_logs_start}

      # Filter to include only transactions with users who had expirations in the target month
      transactions = (
          p | 'Query valid user transactions' >> beam.io.Read(beam.io.BigQuerySource(query = 
            """#standardSQL
            SELECT t.transaction_date,t.membership_expire_date,t.msno,t.payment_method_id,payment_plan_days,t.plan_list_price,t.actual_amount_paid,t.is_auto_renew,t.is_cancel
                from `{transactions_tbl}` t
            where t.msno in
                (SELECT MSNO from `{transactions_tbl}` where membership_expire_date >= {target_month_start} and membership_expire_date <= {target_month_end})
            """.format(**query_params), use_standard_sql=True)) | beam.ParDo(ParseTransactionsBQ())
          )

      user_log_features = (
          p | 'Query user_logs' >> beam.io.Read(beam.io.BigQuerySource(query = 
            """ #standardSQL
                SELECT msno,
                count(msno) as user_log_entries,
                avg(num_25) as avg_num_25,
                avg(num_50) as avg_num_50,
                avg(num_75) as avg_num_75,
                avg(num_985) as avg_num_985,
                avg(num_100) as avg_num_100,
                avg(num_unq) as avg_num_unq,
                sum(num_25) as sum_num_25,
                sum(num_50) as sum_num_50,
                sum(num_75) as sum_num_75,
                sum(num_985) as sum_num_985,
                sum(num_100) as sum_num_100,
                sum(num_unq) as sum_num_unq,
                from `{user_logs_tbl}` 
                group by msno having min(CAST(date as INT64)) <= {user_logs_start}
                
            """.format(**query_params), use_standard_sql=True))
          | beam.ParDo(ParseUserLogsBQ())
          )
      
      ###
      # Generate Labels
      ###
      # TODO add these as cmd line arguments
      final_month_start = 20170301
      final_month_end = 20170331
      
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

      # TODO features: 
      # received_discount as max(is_discount) from transactions
      # membership duration from today using registration date
      # payment method id - one hot
      # average/std_dev amount paid
      # add bd


      # Always Auto-Renew: 1 if the user consistently have auto-renew on all transactions. 0 otherwise
      feature_autorenew = (
      transactions | beam.Map(lambda x: (x["msno"],x["is_auto_renew"])) | beam.CombinePerKey(min))

      # Discount amount mean
      feature_discount_mean = (
      transactions | beam.Map(lambda x: (x["msno"],x["discount_amount"])) | beam.CombinePerKey(AverageFn())
      )

      # Payment ID encoding
      feature_payment_id_encoded = (
          # Converte transactions into key,value pair of (msno,one-hot-encoded-payment-method)
      transactions | beam.Map(lambda x: (x["msno"],OneHotPaymentId({"payment_method_id":x["payment_method_id"]})))
          | beam.CombinePerKey(SummarisePaymentId())
      )
      
      
      def print_fun(x):
          print(x)

      ##
      # Combine all data
      ##

      # Combine all user features with users and filter users with no data
      allOutput =( 
          {'user_demo': users, 
           'feature_user_log_counts':user_log_features,
           'feature_autorenew':feature_autorenew,
           'feature_discount_mean':feature_discount_mean,
           'feature_payment_id_encoded':feature_payment_id_encoded,
           'not_churned_users':not_churned_users} 
          | "Combine users, labels, and features" >> beam.CoGroupByKey()
          | "Filter out empty entries" >> beam.Filter(lambda x: len(x[1]["user_demo"]) > 0 and
                                                      len(x[1]["feature_user_log_counts"]) > 0 and
                                                      len(x[1]["feature_autorenew"]) > 0 and 
                                                      len(x[1]["feature_discount_mean"]) > 0 and
                                                      len(x[1]["feature_payment_id_encoded"]) > 0)
      | "Flatten to single dictionary for BQ" >> beam.Map(format_for_BQ) 
      )

      # partition into train/val/test based on random float
      train, val, test = (allOutput | beam.Partition(train_test_split, 3))
      
      # write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE causes the function to sleep for 150 seconds to wait for delete to finalize before write

      # output to BQ
      val| "Validation output" >> beam.io.WriteToBigQuery(table=features_output_val_tbl,schema=features_output_schema)
      train | "Training output" >> beam.io.WriteToBigQuery(table=features_output_train_tbl,schema=features_output_schema)
      test | "Testing output" >> beam.io.WriteToBigQuery(table=features_output_test_tbl,schema=features_output_schema)

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()