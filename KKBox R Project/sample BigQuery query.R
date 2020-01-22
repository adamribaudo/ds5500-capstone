library(bigrquery)
library(tidyverse)

bq_auth(path = "ds5500-7e5f8aa07468.json")
billing <- "ds5500"

sql <- "SELECT date FROM `ds5500.kkbox.user_logs_dataprep` limit 100"
tb <- bq_project_query(billing, sql)
df_example <- bq_table_download(tb)
df_example

sql <- "SELECT msno, COUNT(*) as member_count FROM `ds5500.kkbox.user_logs_dataprep` 
  group by msno order by member_count desc limit 100"
tb <- bq_project_query(billing, sql)
df_log_count_by_member <- bq_table_download(tb, max_results = 100)
df_log_count_by_member

sql <- "SELECT * FROM `ds5500.kkbox.user_logs_dataprep` 
  where msno = 'w/7CiqS+abkc6DQ6cW+4fdTy4VvBeezvuHAkSJSFNq0='"
tb <- bq_project_query(billing, sql)
df_most_logs <- bq_table_download(tb)
df_most_logs

#TODO: 
# - find all members with 1yr of user_log & transaction data before evaluation window
# - perform undersampling related to class imbalance
