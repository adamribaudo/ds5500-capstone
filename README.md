# DS 5500 Project Proposal: Real-Time Churn Prediction from Sequential Data

Authors: Adam Ribaudo <ribaudo.a@husky.neu.edu> , Zhengye Wang <wang.zhengy@husky.neu.edu>

_Proposed as a Quantiphi project._

## Summary

Customer churn is a metric used by businesses to understand what percentage of customers leave their service or downgrade to an unpaid service within a given time period. This metric is critical for subscription services such as streaming music providers whose main source of revenue comes from subscription dues. Predicting whether a customer is likely to churn can be valuable to these sorts of businesses as it allows for an opportunity to intervene and prevent the user from leaving. In recent decades, the digitization of customer records has provided an opportunity for businesses to apply machine learning methods that predict and respond to customers who are likely to churn. 

Most research in this area utilizes customer features that aggregate data across time [4,5] , thus discarding any information contained in the sequencing of events. More recent work has focused on incorporating this sequential information with the hypothesis that it will improve prediction results [1,2]. In this project, we’ll explore this hypothesis further by applying a recurrent neural network (RNN) variant, Long Short Term Memory (LSTM), against the sequential data contained in the KKBOX Kaggle churn prediction challenge. Our goal is to analyze the improvement in predictiction performance, if any, caused by incorporating sequential data.

In Phase 2 of our project, our model will be hosted using a public cloud provider, Google Cloud Platform (GCP), to demonstrate how such a model can be used to provide real-time predictions regarding a customer’s churn likelihood. Emphasis will be made on creating a cloud architecture that allows for an automated pipeline that re-trains the model with recent data.


## Proposed Plan of Research

For Phase 1, we’ll focus on applying both a standard classification model (ex: Logistic Regression) and an RNN model to the KKBox dataset and compare each model’s capacity to predict customer churn. Our RNN model will combine sequential data with static data through a process called “mixed data” whereas our logistic regression model will use only static data. We expect that each step will be complicated by the volume of data contained in the dataset: Over 30GB in total.

First, we’ll perform exploratory data analysis (EDA) on the data to understand relationships between various characteristics. Next, we’ll label our data using a custom definition of “customer churn” which avoids labeling issues in the original dataset (as described later). Next, we’ll create sequential features appropriate for our RNN model and aggregate features appropriate for our logistic regression model. Next, we’ll balance our class labels through a process called “undersampling”. Next, we’ll split our data into training, validation, and testing sets to ensure the validity of our results. Next, we’ll pre-process our data by performing imputation and normalization. Next, we’ll train our models and evaluate our results on our validation set so that we can tune various hyperparameters such as LSTM units and regularization parameters. Last, we’ll evaluate our tuned models against the test set and compare their performance using the receiver operating characteristic (ROC) curve. We will use AUC and recall (ratio between true positive and all real positives) as our evaluation metrics. Finding churned customers is more difficult than non-churned customers which is why recall rate is useful and a metric like accuracy is not useful. To any extent possible, we’ll interpret our models to determine underlying data patterns or features that positively or negatively affected predictions. 

A review of the KKBox Kaggle page showed that there is some controversy regarding how the competition hosts labeled training data. Primarily, participants found labeled data that did not match the hosts’ own definition of a churned user. For instance, a user whose subscription expired in February but resumed the next day may be considered “churned” contrary to the definition set in the challenge. For this reason, our team will re-label the training data based on a consistent definition of what constitutes a churned user: A user is considered churned if he/she does not renew any expired subscriptions within 30 days. Further narrowing our focus, we’ll sample only users with at least 1 year’s worth of log data, thus avoiding “cold start” problems for users without much activity. Our predictions will determine whether any of these users let their subscription lapse in February 2017 (a date predetermined by the challenge hosts).

For the second half of the semester, we’ll focus on deploying our model (or potentially models) to GCP. The target architecture will support real-time queries to the model as well as an automated training pipeline. A diagram of this proposed architecture is shown below.


![Cloud Architecture](https://i.imgur.com/YFeR9XH.jpg)

_Source: https://cloud-dot-google-developers.appspot.com/solutions/machine-learning/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning_

## Preliminary Results

The KKBox Kaggle challenge contains three tables: transactions, user logs and members. “Transactions” shows transaction details, like payment method, payment plan days for each user. One user could have multiple transactions. The “user_logs” table describes the listening behavior of each user by day. This is where the time series data comes from in the project. “Members” contains demographic information for each user and has a lot of missing values. 

Our preliminary results focus on getting a new training dataset with the well-defined churn definition. As stated before, we used the transactions dataset to label whether members churn or not. In order to get the same length of sequences of input data for each user, we only keep users who have recorded behavior before 2016. The new train dataset has 560,318 distinct customers. Figure 2 shows the percentage of churned and un-churned customers in the train data. Only 3.5% customers churned which makes the dataset highly imbalanced. 

![Class Imbalance](https://i.imgur.com/CMmOC4W.png)

We would like to find out how the customers’ listening behavior are related to their churn. We used user_logs within one month to show the association. Figure 3 shows the boxplot of Counts of date using services for different customer groups. We could see that customers who do not churn spends more time using kkbox than customers who churn on average. 

![Churn by Day](https://i.imgur.com/ocZFWr7.png)

In advance of completing EDA, KKBox data was loaded into Google Cloud Platform. Specifically, the user_logs table was uploaded to Google Big Query which made it possible to retrieve results that otherwise would have exceeded the working memory of our local workstations. Further exploration is needed to determine whether training our models will require cloud resources or if the data can be sampled to a point where local training is possible.

## References

[1] Stojanovski, F. “Churn Prediction using Sequential Activity Patterns in an On-Demand Music Streaming Service.” http://www.diva-portal.org/smash/get/diva2:1208762/FULLTEXT01.pdf. 2017

[2] Mena, C. “Churn Prediction with Sequential Data and Deep Neural Networks.” https://arxiv.org/pdf/1909.11114.pdf. 2019

[3] “WSDM - KKBox's Churn Prediction Challenge,” Accessed Jan 20, 2020. https://www.kaggle.com/c/kkbox-churn-prediction-challenge

[4] J. Hadden, A. Tiwari, R. Roy, and D. Ruta, “Churn Prediction using complaints data,” Enformatika, Vol. 13, 2006. 

[5] Wei, C. and Chiu, I. (2002) Turning Telecommunications Call Details to Churn Prediction: A Data Mining Approach, Expert systems with applications, 23, 103-112.

[6] Burez, J. “Handling class imbalance in customer churn prediction.” Expert Syst. Appl. 2009

