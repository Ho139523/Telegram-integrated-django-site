import warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


#loading data
data_df = pd.read_csv("./data/heart_failure_clinical_records_dataset.csv")
data_df.head()

# Checking for any missing values across the dataset
data_df.info()

#Evaluating the target and finding out the potential skewness in the data
cols= ["#CD5C5C","#FF0000"]
ax = sns.countplot(x= data_df["DEATH_EVENT"], palette= cols)
ax.bar_label(ax.containers[0])

# Doing Univariate Analysis for statistical description and understanding of dispersion of data
data_df.describe().T

#Doing Bivariate Analysis by examaning a corelation matrix of all the features using heatmap
cmap = sns.diverging_palette(2, 165, s=80, l=55, n=9)
corrmat = data_df.corr()
plt.subplots(figsize=(20,20))
sns.heatmap(corrmat,cmap= cmap,annot=True, square=True)

#Evauating age distribution as per the deaths happened
plt.figure(figsize=(15,10))
Days_of_week=sns.countplot(x=data_df['age'],data=data_df, hue ="DEATH_EVENT",palette = cols)
Days_of_week.set_title("Distribution Of Age", color="#774571")

"""### **Note:**
* "time" is the most important feature as it would've been very crucial to get diagnosed early with cardivascular issue so as to get timely treatment thus, reducing the chances of any fatality. (Evident from the inverse relationship)

* "serum_creatinine" is the next important feature as serum's (essential component of blood) abundancy in blood makes it easier for heart to function.

* "ejection_fraction" has also significant influence on target variable which is expected since it is basically the efficiency of the heart.

* Can be seen from the inverse relation pattern that heart's functioning declines with ageing.
"""

# Checking for potential outliers using the "Boxen and Swarm plots" of non binary features.
feature = ["age","creatinine_phosphokinase","ejection_fraction","platelets","serum_creatinine","serum_sodium", "time"]
for i in feature:
    plt.figure(figsize=(10,7))
    sns.swarmplot(x=data_df["DEATH_EVENT"], y=data_df[i], color="black", alpha=0.7)
    sns.boxenplot(x=data_df["DEATH_EVENT"], y=data_df[i], palette=cols)
    plt.show()
    
"""### **Note:**
* Few Outliers can be seen in almost all the features
* Considering the size of the dataset and relevancy of it, we won't be dropping such outliers in data preprocessing which wouldn't bring any statistical fluke.
"""

# Plotting "Kernel Density Estimation (kde plot)" of time and age features -  both of which are significant ones.
sns.kdeplot(x=data_df["time"], y=data_df["age"], hue =data_df["DEATH_EVENT"], palette=cols)

"""### **Note:**
* With less follow-up days, patients often died only when they aged more.
* More the follow-up days  more the probability is, of any fatality.

<a id="title-four"></a>
<h1 style='background:#F08080; border:0; border-radius: 10px; color:black'><center>DATA PREPROCESSING</center></h1>
"""