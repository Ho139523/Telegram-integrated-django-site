# Loading necessary libraries
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from keras.layers import Dense, Dropout
from keras.models import Sequential
from keras import callbacks

# Loading data
data_df = pd.read_csv('./data/heart_failure_clinical_records_dataset.csv')

# Defining independent and dependent attributes
X = data_df.drop(["DEATH_EVENT"], axis=1)
y = data_df["DEATH_EVENT"]

# Setting up a standard scaler for the features
col_names = list(X.columns)
s_scaler = StandardScaler()

# Fitting the scaler on the training data
X_scaled = s_scaler.fit_transform(X)

# Saving the fitted scaler
filename = 'scaler.pkl'
joblib.dump(s_scaler, filename)

# Converting scaled data back to DataFrame
X_scaled = pd.DataFrame(X_scaled, columns=col_names)

# Splitting variables into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.30, random_state=25)

# Initializing EarlyStopping callback
early_stopping = callbacks.EarlyStopping(
    min_delta=0.001, 
    patience=20, 
    restore_best_weights=True
)

# Initializing the ANN model
model = Sequential()

# Adding layers
model.add(Dense(units=16, kernel_initializer='uniform', activation='relu', input_dim=12))
model.add(Dense(units=8, kernel_initializer='uniform', activation='relu'))
model.add(Dropout(0.25))
model.add(Dense(units=8, kernel_initializer='uniform', activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(units=1, kernel_initializer='uniform', activation='sigmoid'))

# Compiling the ANN model
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Training the ANN
history = model.fit(X_train, y_train, batch_size=25, epochs=80, callbacks=[early_stopping], validation_split=0.25)

# Saving the trained model
filename = 'heart_failure_ann.pkl'
joblib.dump(model, filename)

# Predicting the test set results
y_pred = model.predict(X_test)
y_pred = (y_pred > 0.4)

# Printing classification report
from sklearn.metrics import classification_report
print(classification_report(y_test, y_pred))
