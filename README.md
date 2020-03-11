# DS 5500 Project Proposal Phase 2: Evaluating the Benefits of Automated Model Building Pipelines

Authors: Adam Ribaudo <ribaudo.a@husky.neu.edu> , Zhengye Wang <wang.zhengy@husky.neu.edu>

_Proposed as a Quantiphi project._

## Summary

The last decade has seen an increase in businesses utilizing machine learning (ML) models as core parts of their products or the value provided to their customers [1]. For example, streaming music services add value to their service by recommending new songs or artists to users. 

The process of deploying a model into a production environment involves data collection, data preparation, feature engineering, algorithm selection, hyper-parameter optimization and more. Unfortunately, it’s common for data scientists and data engineers to sacrifice the long-term maintenance of their models for short term gains by manually completing data processing steps and creating code that isn’t split into distinct, tested modules. This trade-off of short-term vs. long-term thinking is often categorized as “technical debt” which is a metaphor introduced in 1992 “to help reason about the long term costs incurred by moving quickly in software engineering” [3].

In contrast, businesses that automate the training and deployment of their models have a competitive advantage over businesses that do not. This advantage arises from a long term reduction in manual labor, fewer chances for mistakes, increased speed to market, more reliable outcomes, and models trained on more recent data. Our project focuses on developing an automated ML training pipeline and evaluating its benefits and drawbacks as compared to the manual ML process that was developed during Phase 1.  

During Phase 1, we generated two different types of models built to classify whether a user using the KKBox music streaming service would churn in a particular month [4]. The data used to train these models included the number of songs each user listened to per day, each user’s financial transaction history, and a limited amount of user demographic information [Table 1]. The model building pipeline we expect to build during Phase 2 will use the same data as in Phase 1 but automate the process of data preprocessing, feature engineering, training, validation, and deployment.

## Proposed Plan of Research

The work to be completed during Phase 2 is broken out into two major components:

1) Developing a data preprocessing pipeline using Apache Beam and Google DataFlow
2) Developing a model training and deployment pipeline using GCP AI-Platform

These two components will then be combined into a single, scalable ML training and deployment pipeline. As a final step, we will take measurements related to the speed of training and deployment with varying amounts of training data.

### Apache Beam / Google DataFlow

Apache Beam is a data processing architecture with high level APIs written in Java, Python, and Go [2] that allows for massively parallel data pipelines. Beam was created to provide much of the same functionality as other data processing tools such as Apache Spark but with a higher level of abstraction and the capacity to swap out the underlying data processing service. In this manner, coders can focus more on business logic and less on the particulars of how data processing is parallelized and returned. 

Google DataFlow is a fully managed service used for executing Apache Beam pipelines. In Beam parlance, DataFlow is known as a “Runner” in that it can run Apache Beam pipelines. Other runners include the “Direct” runner, used for testing pipelines locally, and the Apache Flink runner which provides an open source alternative for executing Beam pipelines. One key advantage of Google DataFlow is that the number of pipeline workers necessary to complete a pipeline task is automatically determined. This means that parallelizable pipelines of nearly any scale can be processed.

Our Apache Beam pipeline will focus on the data preprocessing, feature engineering, and train/validation/test splitting process. Using BigQuery as an input, the pipeline will recreate the data processing steps finished as part of Phase 1. Wherever possible, parameters will be used to control processing steps that might affect prediction outcomes. For example, a parameter will be created indicating how many days of user log activity each user must have before they might be included in the training data. Previously, this parameter was hard-coded to 365 days.

### AI-Platform

AI-Platform is a managed service that enables data scientists to build and run their own machine learning applications quickly and cost-effectively [5]. Once the model code is completed and submitted to the cloud, AI-Platform can help manage the following stages: train the model on the provided data (involves training, evaluation, and hyperparameter tuning), deploy the trained model and provide predictions. By using AI-Platform with the  accompanied cloud calculation capability and customized options, we could deal with large datasets, making our pipeline more scalable; enable distributed training and reduce training time; enable hyperparameter tuning in parallel, expand the grid search range and increase the possibility of finding the best model. 

Our AI-Platform pipeline will focus on model training, hyperparameter tuning and prediction. The pipeline will use the data obtained by the Apache Beam pipeline directly via cloud. A python application including the Logistic Regression model and hyperparameter tuning will be built locally and submitted to AI-Platform to train the model. Once the training and tuning is finished, we will leverage the AI-Platform Prediction to provide prediction for new data. 

### Evaluation Criteria

Once the automated pipeline has been fully assembled, we plan to evaluate its performance against the following criteria:
- Time to train model (start to finish)
- Code modularity
- Risk of human error
- Scalability (time increase as data increases)

Comparisons will be made, wherever possible, to the performance of the Phase 1 manual training process.

## Preliminary Results

In phase 1, we compared the performance of Deep Neural Networks (DNN) models and Logistic Regression (LR) using the KKBox data [Table 2]. The result showed that DNN models do not have an obvious advantage over LR models when dealing with users’ transaction sequential data. In phase 2, we plan to deploy the LR model. 

We have created a simple Apache Beam pipeline that processes a CSV of KKBox user log data and filters the data to only include users with a minimum user_log date entry of a specific date. This is a crucial step in the data pre-processing pipeline to ensure that the training data only contains users with a minimum of X number of days’ worth of data. Future work will expand on this to filter user log records made in the last Y days, log transform various metrics, and split the data into training, validation, and test datasets. This code is located here on GitHub.

We have set up all the environments required for the AI-Platform and successfully trained a toy model (provided by google’s guide on Github [6]) via the platform. We will use the module structure provided in the guide to build our own application. 

## References

[1] MLOps: Continuous delivery and automation pipelines in machine learning. Accessed 3/9/2020. 
https://cloud.google.com/solutions/machine-learning/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning

[2] Apache Beam: An advanced unified programming model. Accessed 3/9/2020. 
https://beam.apache.org/

[3] Hidden Technical Debt in Machine Learning Systems. 
https://papers.nips.cc/paper/5656-hidden-technical-debt-in-machine-learning-systems.pdf

[4] “WSDM - KKBox's Churn Prediction Challenge,” Accessed 1/20/2020. 
https://www.kaggle.com/c/kkbox-churn-prediction-challenge

[5] AI-Platform. Accessed 3/10/2020.  
https://cloud.google.com/ai-platform/docs

[6] AI Platform Training. Accessed 3/10/2020.  
https://github.com/GoogleCloudPlatform/ai-platform-samples/tree/master/training/sklearn/structured/base

## Appendix
| Table        | Description                                | Size   |
|--------------|:------------------------------------------:|-------:|
| User Logs    | Listening behavior organized by date       | 29GB   |
| Transactions | Financial transactions organized by date   | 1.7GB  |
| Member       | Member data                                | 400MB  |
                        Table 1: KKBox Datasets



|   Model / Type  |        Approach        | Training Parameters |   F1   |
|:---------------:|:----------------------:|---------------------|:------:|
|  LR / Aggregate | 1. All Data            |         144         | 0.4552 |
|  LR / Aggregate | 2. User-Logs           |          24         | 0.1296 |
| DNN /Sequential | 1. All Data(Weekly)    |        8,385        | 0.3137 |
| DNN /Sequential | 2a. User-Logs (Weekly) |   5,161(32 weeks)   | 0.1936 |
| DNN /Sequential | 2b. User-Logs (Daily)  |   5,161(215 days)   | 0.2019 |
            Table 2: Final results from all models in phase 1

