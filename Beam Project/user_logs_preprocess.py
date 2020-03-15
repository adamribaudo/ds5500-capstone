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

import apache_beam as beam
from apache_beam.metrics.metric import Metrics
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions


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

def str2timestamp(s, fmt='%Y-%m-%d-%H-%M'):
  """Converts a string into a unix timestamp."""
  dt = datetime.strptime(s, fmt)
  epoch = datetime.utcfromtimestamp(0)
  return (dt - epoch).total_seconds()


def timestamp2str(t, fmt='%Y-%m-%d %H:%M:%S.000'):
  """Converts a unix timestamp into a formatted string."""
  return datetime.fromtimestamp(t).strftime(fmt)


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
    # super(ParseGameEventFn, self).__init__()
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


class ExtractAndSumScore(beam.PTransform):
  """A transform to extract key/score information and sum the scores.
  The constructor argument `field` determines whether 'team' or 'user' info is
  extracted.
  """
  def __init__(self, field):
    # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
    # super(ExtractAndSumScore, self).__init__()
    beam.PTransform.__init__(self)
    self.field = field

  def expand(self, pcoll):
    return (pcoll | beam.Map(lambda elem: (elem[self.field], elem['score'])) | beam.CombinePerKey(sum))

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

class WriteToBigQuery(beam.PTransform):
  """Generate, format, and write BigQuery table row information."""
  def __init__(self, table_name, dataset, schema, project):
    """Initializes the transform.
    Args:
      table_name: Name of the BigQuery table to use.
      dataset: Name of the dataset to use.
      schema: Dictionary in the format {'column_name': 'bigquery_type'}
      project: Name of the Cloud project containing BigQuery table.
    """
    # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
    # super(WriteToBigQuery, self).__init__()
    beam.PTransform.__init__(self)
    self.table_name = table_name
    self.dataset = dataset
    self.schema = schema
    self.project = project

  def get_schema(self):
    """Build the output table schema."""
    return ', '.join('%s:%s' % (col, self.schema[col]) for col in self.schema)

  def expand(self, pcoll):
    return (pcoll | 'ConvertToRow' >> beam.Map(lambda elem: {col: elem[col]
                               for col in self.schema}) | beam.io.WriteToBigQuery(self.table_name, self.dataset, self.project, self.get_schema()))

class GenerateValidUsersFromLogs(beam.PTransform):
    def __init__(self, logs_input, min_date):
        # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
        # super(HourlyTeamScore, self).__init__()
        beam.PTransform.__init__(self)
        self.logs_input = logs_input
        self.min_date = min_date
    def expand(self, pcoll):
        return (pcoll | 'ReadInputText' >> beam.io.ReadFromText(self.logs_input,skip_header_lines=1)
            | 'ParseUserLogFn' >> beam.ParDo(ParseUserLogFn())
            | 'ExtractMSNOandDate' >> beam.Map(lambda elem: (elem['msno'],elem['date']))
            | 'FindMinDate' >> beam.CombinePerKey(min)
            | 'FilterStartDate' >> beam.Filter(lambda elem: elem[1] <= self.min_date)
            #| beam.Keys() # returning key,value pair for later CoGroupByKey
        )

class HourlyTeamScore(beam.PTransform):
  def __init__(self, start_min, stop_min, window_duration):
    # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
    # super(HourlyTeamScore, self).__init__()
    beam.PTransform.__init__(self)
    self.start_timestamp = str2timestamp(start_min)
    self.stop_timestamp = str2timestamp(stop_min)
    self.window_duration_in_seconds = window_duration * 60

  def expand(self, pcoll):
    return (pcoll | 'ParseGameEventFn' >> beam.ParDo(ParseGameEventFn())

        # Filter out data before and after the given times so that it is not
        # included in the calculations.  As we collect data in batches (say, by
        # day), the batch for the day that we want to analyze could potentially
        # include some late-arriving data from the previous day.  If so, we
        # want
        # to weed it out.  Similarly, if we include data from the following day
        # (to scoop up late-arriving events from the day we're analyzing), we
        # need to weed out events that fall after the time period we want to
        # analyze.
        # [START filter_by_time_range]
        | 'FilterStartTime' >> beam.Filter(lambda elem: elem['timestamp'] > self.start_timestamp) | 'FilterEndTime' >> beam.Filter(lambda elem: elem['timestamp'] < self.stop_timestamp)
        # [END filter_by_time_range]

        # [START add_timestamp_and_window]
        # Add an element timestamp based on the event log, and apply fixed
        # windowing.
        | 'AddEventTimestamps' >> beam.Map(lambda elem: beam.window.TimestampedValue(elem, elem['timestamp'])) | 'FixedWindowsTeam' >> beam.WindowInto(beam.window.FixedWindows(self.window_duration_in_seconds))
        # [END add_timestamp_and_window]

        # Extract and sum teamname/score pairs from the event data.
        | 'ExtractAndSumScore' >> ExtractAndSumScore('team'))

from random import random
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
  """Main entry point; defines and runs the hourly_team_score pipeline."""
  parser = argparse.ArgumentParser()

  # The default maps to two large Google Cloud Storage files (each ~12GB)
  # holding two subsequent day's worth (roughly) of data.
  parser.add_argument('--input',
      type=str,
      default='data\\user_logs_small.csv',
      help='Path to the data file(s)')
  parser.add_argument('--output',
      type=str,
      default='beam_output.csv',
      help='Path to output')
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

  # We also require the --project option to access --dataset
  if options.view_as(GoogleCloudOptions).project is None:
    parser.print_usage()
    print(sys.argv[0] + ': error: argument --project is required')
    sys.exit(1)

  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  options.view_as(SetupOptions).save_main_session = save_main_session

  with beam.Pipeline(options=options) as p:
      
      # TODO input from BQ
      
      # Read raw users
      users = (
          p | 'Read Users' >> beam.io.ReadFromText("data\\users_fake.csv", skip_header_lines=1) 
        | 'Parse Users' >> beam.ParDo(ParseUsers())
        )

      # Read raw transactions
      transactions = (
            p | 'Read Transactions' >> beam.io.ReadFromText("data\\transactions_fake.csv", skip_header_lines=1) 
        | 'Parse Transactions' >> beam.ParDo(ParseTransactions())
        )

      # Find MNSOs with an expiration in the target month
      target_month_start = 20170201
      target_month_end = 20170228
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
        beam.Filter(lambda elem: elem['transaction_date'] >= 20170201 
                    and elem['transaction_date'] <= 20170331 
                    and elem['membership_expire_date'] >= 20170301
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
        p | GenerateValidUsersFromLogs("data\\user_logs_fake.csv", target_min_log_date)
        )
      
      # Generate (msno,is_churn) with inner join between valid users based on transactions and user logs
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

      # Partition into train/val/test based on random float
      train_labels, val_labels, test_labels = (validUserLabels | beam.Partition(train_test_split, 3))
      
      #train_labels | beam.Map(lambda x: print('train: {}'.format(x)))
      #val_labels| beam.Map(lambda x: print('val: {}'.format(x)))
      #test_labels | beam.Map(lambda x: print('test: {}'.format(x)))

      ###
      # Feature engineering
      ###

      # Always Auto-Renew: 1 if the user consistently have auto-renew on all transactions. 0 otherwise
      feature_autorenew = (
      transactionsFromValidUsers | beam.Map(lambda x: (x["msno"],x["is_auto_renew"])) | beam.CombinePerKey(min))

      # Discount amount mean
      feature_discount_mean = (
      transactionsFromValidUsers | beam.Map(lambda x: (x["msno"],x["discount_amount"])) | beam.CombinePerKey(AverageFn())
      )
      
      ##
      # Combine all data
      ##

      # Combine all user features with users and filter users with no data
      allOutput =( 
          {'is_churn': validUserLabels, 
           'user_demo': users, 
           'feature_autorenew':feature_autorenew,
           'feature_discount_mean':feature_discount_mean} 
          | "Combine users, labels, and features" >> beam.CoGroupByKey()
          | "Filter out empty entries" >> beam.Filter(lambda x: len(x[1]["is_churn"]) and len(x[1]["user_demo"]) > 0 and len(x[1]["feature_autorenew"]) > 0 and len(x[1]["feature_discount_mean"]) > 0)
          | beam.Map(print)
      )
      
      # TODO output to BQ
      #output = (
      #      expirationCounts | 'WriteTransactions' >> beam.io.WriteToText("output\\transactions.txt")
      #  )

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.WARNING)
  run()