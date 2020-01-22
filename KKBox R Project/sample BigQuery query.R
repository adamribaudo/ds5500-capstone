library(bigrquery)
bq_auth(path = "ds5500-7e5f8aa07468.json")
billing <- "ds5500"
sql <- "SELECT date FROM `ds5500.kkbox.user_logs_dataprep` limit 100"
tb <- bq_project_query(billing, sql)
df <- bq_table_download(tb)
df
