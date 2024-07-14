import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns 

from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from sklearn.metrics import r2_score , mean_squared_error

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense



df = pd.read_csv("car_purchasing.csv",encoding='ISO-8859-1')


df.shape


df.head()


df.info()

df.isna().sum()

df.duplicated().sum()


df.describe()


df.drop(['customer name', 'customer e-mail', 'country', 'gender'], axis=1,inplace=True)


columns = df.columns
for column in columns:
    if df[column].dtype == 'float64':
        fig, (ax_box, ax_hist) = plt.subplots(1, 2, figsize=(10, 5))

        ax_box.boxplot(df[column], vert=False, whis=1.5)
        ax_box.set_xlabel('Value')
        ax_box.set_title(f'{column} Box')

        sns.histplot(df[column], bins=50, color='blue', kde=True, ax=ax_hist)
        ax_hist.set_xlabel('Value')
        ax_hist.set_ylabel('Frequency')
        ax_hist.set_title(f'{column} dist')

        # Show plot
        plt.tight_layout()
        plt.show()
		
		
		
X = df.drop('car purchase amount',axis = 1)
y = df['car purchase amount']


scaler = MinMaxScaler()
X = scaler.fit_transform(X)
y = scaler.fit_transform(y.values.reshape(-1, 1))


X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)


model = Sequential([
    Dense(8,activation="relu",input_dim=4),
    Dense(1,activation="linear")
])


model.summary()


model.compile(optimizer='adam', loss='MSE')


history = model.fit(X_train, y_train, epochs=100, validation_split=0.2)


# Creating a function to evaluate our model
def plot_loss(history):
    
    training_loss = history.history['loss']
    validation_loss = history.history['val_loss']
    epochs = range(1, len(training_loss) + 1)

    plt.plot(epochs, training_loss, 'b', label='Training Loss')
    plt.plot(epochs, validation_loss, 'r', label='Validation Loss')
    plt.title('Training and Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()
	
	
	
	
plot_loss(history)


y_predict = model.predict(X_test)


r2_score(y_test , y_predict)
