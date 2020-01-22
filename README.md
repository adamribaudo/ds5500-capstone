# DS 5500 Project Proposal: Real-Time Churn Prediction from Sequential Data

Authors: Adam Ribaudo <ribaudo.a@husky.neu.edu> , Zhengye Wang <wang.zhengy@husky.neu.edu>

## Summary

Customer churn is a metric used by businesses to understand what percentage of customers leave their service (or downgrade to an unpaid service) within a given time period. This metric is critical for subscription services such as streaming music provides whose main source of revenue comes from subscriber dues. Using machine learning techniques, many businesses attempt to predict a customer’s likelihood to churn so that an intervention (such as a promotional offer) can take place that prevents the customer from leaving.

Most research in this area ustilizes input data with features that aggregate metrics across time, thus discarding any information contained in the chronological sequence of events that comprise this aggregate data. This project team hypothesizes that the information contained in sequential data is important and can improve area under the curve (AUC) scores for customer churn prediction. By applying a recurrent neural network (RNN) variant, Long Short Term Memory (LSTM), against the sequential data contained in the KKBOX Kaggle churn prediction challenge, our project seeks to show the value of incorporating sequential data in churn prediction. 

As a future step, our model will be hosted using a public cloud provider, Google Cloud Platform (GCP), to demonstrate how such a model can be used to provide a business with real-time predictions regarding a customer’s churn likelihood. Emphasis will be made on creating a cloud architecture that allows for continuous training (CT) of the model based on customer data as it arrives. 


## Proposed Plan of Research

For the first-half of the semester, we’ll focus on applying both a Random Forest (RF) and RNN model to KKBox dataset and comparing their capacity to predict customer churn. First, we will perform exploratory data analysis (EDA) on the data to understand relationships between various characteristics. Next, we’ll set definitions for what constitutes a “churned” user. After that, we’ll then prepare the data for use with A) an RNN model that expects data in a sequently format and B) a Random Forest model that aggregates data across time. This may include steps such as feature engineering and, in the case of the RNN, padding missing sequences. Finally, we’ll split our data into training and testing sets and produce evaluation metrics based on each models’ performance. To any extent possible, we’ll interpret our models to determine underlying data patterns that positively or negatively affected predictions. 

For the second half of the semester, we’ll focus on deploying our LSTM model to GCP. The target architecture will support real-time queries to the model as well as continuous training. A diagram of this architecture is shown below. 

![Cloud Architecture](https://cloud-dot-google-developers.appspot.com/solutions/images/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning-3-ml-automation-ct.svg)

_Source: https://cloud-dot-google-developers.appspot.com/solutions/machine-learning/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning_