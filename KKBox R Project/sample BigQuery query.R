library(bigrquery)
library(tidyverse)

bq_auth(path = "ds5500-7e5f8aa07468.json")
billing <- "ds5500"

sql <- "SELECT msno, count(msno) FROM `ds5500.kkbox.user_logs_for_members_existed_before_2016` 
group by msno order by count(msno) desc LIMIT 1000"
tb <- bq_project_query(billing, sql)
df_log_count_by_member <- bq_table_download(tb)
df_log_count_by_member

sql <- "SELECT * FROM `ds5500.kkbox.members_exist_before_2016` 
  where msno = 'w/7CiqS+abkc6DQ6cW+4fdTy4VvBeezvuHAkSJSFNq0='"
tb <- bq_project_query(billing, sql)
df_most_logs <- bq_table_download(tb)
df_most_logs

sql <- "SELECT * FROM `ds5500.kkbox.members_exist_before_2016`"
tb <- bq_project_query(billing, sql)
members <- bq_table_download(tb)
#write_csv(members, "members_existed_before_20160101.csv")

#TODO: 
# perform undersampling related to class imbalance

