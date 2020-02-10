library(tidyverse)
library(pROC)
library(Deducer)

X <- read.csv("data\\X_train_transformed_100_pct_under.csv")
y <- read.csv("data\\y_train_100_pct_under.csv", header=F)

X <- X %>% select(-msno)
X$response <- y$V2

fit <- glm(response ~ ., data=X, family="binomial")
summary(fit)
prob <- predict(fit, type=c("response"))
rocplot(fit)
