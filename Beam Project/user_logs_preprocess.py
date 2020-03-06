"""
Optionally include the `--input` argument to specify a batch input file. To
indicate a time after which the data should be filtered out, include the
`--stop_min` arg. E.g., `--stop_min=2015-10-18-23-59` indicates that any data
timestamped after 23:59 PST on 2015-10-18 should not be included in the
analysis. To indicate a time before which data should be filtered out, include
the `--start_min` arg. If you're using the default input
"gs://dataflow-samples/game/gaming_data*.csv", then
`--start_min=2015-11-16-16-10 --stop_min=2015-11-17-16-10` are good values.

For a description of the usage and options, use -h or --help.

To specify a different runner:
  --runner YOUR_RUNNER

NOTE: When specifying a different runner, additional runner-specific options
      may have to be passed in as well

EXAMPLES
--------

# DirectRunner
python hourly_team_score.py \
    --project $PROJECT_ID \
    --dataset $BIGQUERY_DATASET

# DataflowRunner
python hourly_team_score.py \
    --project $PROJECT_ID \
    --dataset $BIGQUERY_DATASET \
    --runner DataflowRunner \
    --temp_location gs://$BUCKET/user_score/temp
"""

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
    return (
        pcoll
        | beam.Map(lambda elem: (elem[self.field], elem['score']))
        | beam.CombinePerKey(sum))


class TeamScoresDict(beam.DoFn):
  """Formats the data into a dictionary of BigQuery columns with their values

  Receives a (team, score) pair, extracts the window start timestamp, and
  formats everything together into a dictionary. The dictionary is in the format
  {'bigquery_column': value}
  """
  def process(self, team_score, window=beam.DoFn.WindowParam):
    team, score = team_score
    start = timestamp2str(int(window.start))
    yield {
        'team': team,
        'total_score': score,
        'window_start': start,
        'processing_time': timestamp2str(int(time.time()))
    }


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
    return (
        pcoll
        | 'ConvertToRow' >>
        beam.Map(lambda elem: {col: elem[col]
                               for col in self.schema})
        | beam.io.WriteToBigQuery(
            self.table_name, self.dataset, self.project, self.get_schema()))


# [START main]
class HourlyTeamScore(beam.PTransform):
  def __init__(self, start_min, stop_min, window_duration):
    # TODO(BEAM-6158): Revert the workaround once we can pickle super() on py3.
    # super(HourlyTeamScore, self).__init__()
    beam.PTransform.__init__(self)
    self.start_timestamp = str2timestamp(start_min)
    self.stop_timestamp = str2timestamp(stop_min)
    self.window_duration_in_seconds = window_duration * 60

  def expand(self, pcoll):
    return (
        pcoll
        | 'ParseGameEventFn' >> beam.ParDo(ParseGameEventFn())

        # Filter out data before and after the given times so that it is not
        # included in the calculations. As we collect data in batches (say, by
        # day), the batch for the day that we want to analyze could potentially
        # include some late-arriving data from the previous day. If so, we want
        # to weed it out. Similarly, if we include data from the following day
        # (to scoop up late-arriving events from the day we're analyzing), we
        # need to weed out events that fall after the time period we want to
        # analyze.
        # [START filter_by_time_range]
        | 'FilterStartTime' >>
        beam.Filter(lambda elem: elem['timestamp'] > self.start_timestamp)
        | 'FilterEndTime' >>
        beam.Filter(lambda elem: elem['timestamp'] < self.stop_timestamp)
        # [END filter_by_time_range]

        # [START add_timestamp_and_window]
        # Add an element timestamp based on the event log, and apply fixed
        # windowing.
        | 'AddEventTimestamps' >> beam.Map(
            lambda elem: beam.window.TimestampedValue(elem, elem['timestamp']))
        | 'FixedWindowsTeam' >> beam.WindowInto(
            beam.window.FixedWindows(self.window_duration_in_seconds))
        # [END add_timestamp_and_window]

        # Extract and sum teamname/score pairs from the event data.
        | 'ExtractAndSumScore' >> ExtractAndSumScore('team'))


def run(argv=None, save_main_session=True):
  """Main entry point; defines and runs the hourly_team_score pipeline."""
  parser = argparse.ArgumentParser()

  # The default maps to two large Google Cloud Storage files (each ~12GB)
  # holding two subsequent day's worth (roughly) of data.
  parser.add_argument(
      '--input',
      type=str,
      default='data\\user_logs_small.csv',
      help='Path to the data file(s)')
  parser.add_argument(
      '--output',
      type=str,
      default='beam_output.csv',
      help='Path to output')
  parser.add_argument(
      '--dataset',
      type=str,
      required=True,
      help='BigQuery Dataset to write tables to. '
      'Must already exist.')
  parser.add_argument(
      '--table_name',
      default='hourly_scores',
      help='The BigQuery table name. Should not already exist.')
  parser.add_argument(
      '--window_duration',
      type=int,
      default=60,
      help='Numeric value of fixed window duration, in minutes')
  parser.add_argument(
      '--start_min',
      type=str,
      default='1970-01-01-00-00',
      help='String representation of the first minute after '
      'which to generate results in the format: '
      'yyyy-MM-dd-HH-mm. Any input data timestamped '
      'prior to that minute won\'t be included in the '
      'sums.')
  parser.add_argument(
      '--stop_min',
      type=str,
      default='2100-01-01-00-00',
      help='String representation of the first minute for '
      'which to generate results in the format: '
      'yyyy-MM-dd-HH-mm. Any input data timestamped '
      'after to that minute won\'t be included in the '
      'sums.')

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
    (  # pylint: disable=expression-not-assigned
        p
        # https://beam.apache.org/releases/pydoc/2.19.0/apache_beam.io.textio.html
        | 'ReadInputText' >> beam.io.ReadFromText(args.input, skip_header_lines=1)
        | 'ParseUserLogFn' >> beam.ParDo(ParseUserLogFn())
        | 'ExtractMSNOandDate' >> beam.Map(lambda elem: (elem['msno'], elem['date']))
        | 'FindMinDate' >> beam.CombinePerKey(min)
        # TODO, how to work with tuples as key value pair and address them by field name?
        | 'FilterStartDate' >> beam.Filter(lambda elem: elem[1] <= 20150501)
        # TODO: group by MSNO and min(date) to filter users with a min(date) > somethreshold
        | 'WriteUserLogs' >> beam.io.WriteToText(args.output)
    )

# [END main]

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()