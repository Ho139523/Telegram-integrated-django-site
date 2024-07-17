"""
# <h1 style='background:#F08080; border:2; border-radius: 10px; font-size:250%; font-weight: bold; color:black'><center>HEART FAILURE PREDICTION</center></h1>

<img src = "https://media.giphy.com/media/3X1PyBANma99aeSOad/giphy.gif" width = 900 height = 900/>

Cardiovascular diseases (CVDs) are the number 1 cause of death globally, taking an estimated 17.9 million lives each year, which accounts for 31% of all deaths worlwide.
Heart failure is a common event caused by CVDs and this dataset contains 12 features that can be used to predict mortality by heart failure.

Most cardiovascular diseases can be prevented by addressing behavioural risk factors such as tobacco use, unhealthy diet and obesity, physical inactivity and harmful use of alcohol using population-wide strategies.

People with cardiovascular disease or who are at high cardiovascular risk (due to the presence of one or more risk factors such as hypertension, diabetes, hyperlipidaemia or already established disease) need early detection and management wherein a machine learning model can be of great help.

<a id='top'></a>
<div class="list-group" id="list-tab" role="tablist">
    
<h1 style='background:#F08080; border:0; border-radius: 10px; color:black'><center> TABLE OF CONTENTS </center></h1>"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from sklearn import svm
from keras.layers import Dense, BatchNormalization, Dropout, LSTM
from keras.models import Sequential
from keras import callbacks
from sklearn.metrics import precision_score, recall_score, confusion_matrix, classification_report, accuracy_score, f1_score
import pickle
import joblib


"""<a id="title-two"></a>
<h1 style='background:#F08080; border:0; border-radius: 10px; color:black'><center>LOADING DATA</center></h1>
"""

#loading data
data_df = pd.read_csv("./data/heart_failure_clinical_records_dataset.csv")


"""<div style="border-radius:10px;
            border : black solid;
            background-color: 	#FFFFF0;
            font-size:110%;
            text-align: left">

<h2 style='; border:0; border-radius: 10px; font-weight: bold; color:black'><center>About the data (Description of attributes)</center></h2>  
    
* **age:** Age of the patient
* **anaemia:** Haemoglobin level of patient (Boolean)
* **creatinine_phosphokinase:** Level of the CPK enzyme in the blood (mcg/L)
* **diabetes:** If the patient has diabetes (Boolean)
* **ejection_fraction:** Percentage of blood leaving the heart at each contraction
* **high_blood_pressure:** If the patient has hypertension (Boolean)
* **platelets:** Platelet count of blood (kiloplatelets/mL)
* **serum_creatinine:** Level of serum creatinine in the blood (mg/dL)
* **serum_sodium:** Level of serum sodium in the blood (mEq/L)
* **sex:** Sex of the patient
* **smoking:** If the patient smokes or not (Boolean)
* **time:** Follow-up period (days)
* **DEATH_EVENT:** If the patient deceased during the follow-up period (Boolean)

**[Attributes having Boolean values:** 0 = Negative (No); 1 = Positive (Yes)]

<a id="title-three"></a>
<h1 style='background:#F08080; border:0; border-radius: 10px; color:black'><center>DATA ANALYSIS</center></h1>
"""



# Defining independent and dependent attributes in training and test sets
X=data_df.drop(["DEATH_EVENT"],axis=1)
y=data_df["DEATH_EVENT"]

# Setting up a standard scaler for the features and analyzing it thereafter
col_names = list(X.columns)
s_scaler = preprocessing.StandardScaler()
X_scaled= s_scaler.fit_transform(X)
X_scaled = pd.DataFrame(X_scaled, columns=col_names)
X_scaled.describe().T

#Plotting the scaled features using boxen plots
# colors =["#CD5C5C","#F08080","#FA8072","#E9967A","#FFA07A"]
# plt.figure(figsize=(20,10))
# sns.boxenplot(data = X_scaled,palette = colors)
# plt.xticks(rotation=60)
# plt.show()

#spliting variables into training and test sets
X_train, X_test, y_train,y_test = train_test_split(X_scaled,y,test_size=0.30,random_state=25)

"""<a id="title-MB"></a>
<h1 style='background:#F08080; border:0; border-radius: 10px; color:black'><center>MODEL BUILDING</center></h1>

## <a id = "title-five"></a>**<span style="color:#CD5C5C;">1. SUPPORT VECTOR MACHINE (SVM) </span>**
"""

# Instantiating the SVM algorithm
model1=svm.SVC()

# Fitting the model
model1.fit (X_train, y_train)

# Predicting the test variables
y_pred = model1.predict(X_test)

# Getting the score
model1.score (X_test, y_test)

# Printing classification report (since there was biasness in target labels)
print(classification_report(y_test, y_pred))

# Getting the confusion matrix
# cmap1 = sns.diverging_palette(2, 165, s=80, l=55, n=9)
# plt.subplots(figsize=(10,7))
# cf_matrix = confusion_matrix(y_test, y_pred)
# sns.heatmap(cf_matrix/np.sum(cf_matrix), cmap = cmap1, annot = True, annot_kws = {'size':25})

"""## <a id = "title-six"></a>**<span style="color:#CD5C5C;">2. Artificial Neural Network (ANN) </span>**"""

early_stopping = callbacks.EarlyStopping(
    min_delta=0.001, # minimium amount of change to count as an improvement
    patience=20, # how many epochs to wait before stopping
    restore_best_weights=True)

# Initialising the NN
model = Sequential()

# layers
model.add(Dense(units = 16, kernel_initializer = 'uniform', activation = 'relu', input_dim = 12))
model.add(Dense(units = 8, kernel_initializer = 'uniform', activation = 'relu'))
model.add(Dropout(0.25))
model.add(Dense(units = 8, kernel_initializer = 'uniform', activation = 'relu'))
model.add(Dropout(0.5))
model.add(Dense(units = 1, kernel_initializer = 'uniform', activation = 'sigmoid'))

# Compiling the ANN
model.compile(optimizer = 'adam', loss = 'binary_crossentropy', metrics = ['accuracy'])

# Train the ANN
history = model.fit(X_train, y_train, batch_size = 25, epochs = 80,callbacks=[early_stopping], validation_split=0.25)

val_accuracy = np.mean(history.history['val_accuracy'])
print("\n%s: %.2f%%" % ('val_accuracy is', val_accuracy*100))

history_df = pd.DataFrame(history.history)

# plt.plot(history_df.loc[:, ['loss']], "#CD5C5C", label='Training loss')
# plt.plot(history_df.loc[:, ['val_loss']],"#FF0000", label='Validation loss')
# plt.title('Training and Validation loss')
# plt.xlabel('Epochs')
# plt.ylabel('Loss')
# plt.legend(loc="best")

# plt.show()

history_df = pd.DataFrame(history.history)

# plt.plot(history_df.loc[:, ['accuracy']], "#CD5C5C", label='Training accuracy')
# plt.plot(history_df.loc[:, ['val_accuracy']],"#FF0000", label='Validation accuracy')

# plt.title('Training and Validation accuracy')
# plt.xlabel('Epochs')
# plt.ylabel('Accuracy')
# plt.legend()
# plt.show()

# Predicting the test set results
y_pred = model.predict(X_test)
y_pred = (y_pred > 0.4)
np.set_printoptions()

# Getting the confusion matrix
# cmap1 = sns.diverging_palette(2, 165, s=80, l=55, n=9)
# plt.subplots(figsize=(10,7))
# cf_matrix = confusion_matrix(y_test, y_pred)
# sns.heatmap(cf_matrix/np.sum(cf_matrix), cmap = cmap1, annot = True, annot_kws = {'size':25})

print(classification_report(y_test, y_pred))

"""<img src = "https://media.giphy.com/media/QtOU1ZJDKis9fGuA1Q/giphy.gif" width = "900" height = "900"/>

<a id="title-seven"></a>
# <h1 style='background:#F08080; border:2; border-radius: 10px; font-size:250%; font-weight: bold; color:black'><center>END</center></h1>
"""

# Creating pickle file from the compiled model so as to be able to call it everytime without running the whole code and training the data again.

filename='heart_failure_ann.pkl'
joblib.dump(model, filename)