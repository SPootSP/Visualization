import pandas as pd
from filter import filtered_df
df = pd.read_csv(r'C:\Users\Usuario\Downloads\CleanCovid.csv')

df = df[df['SARS-Cov-2 exam result'] == 'positive']
blood_test = list(df.columns.values[6:21])
columns = ['gravity']
columns.extend(blood_test)
df = df[columns]
df = df.dropna(how='any')
from sklearn.preprocessing import MinMaxScaler

Numerical = df[df.columns.values[1:]]
for column in Numerical.columns.values:
    Numerical[column] = Numerical[column].apply(lambda x: x.replace(',', '.'))
    Numerical[column] = Numerical[column].apply(lambda x: float(x))

All_numerical = MinMaxScaler().fit_transform(Numerical)
df[df.columns.values[1:]] = All_numerical
import matplotlib.pyplot as plt
import seaborn as sns

sns.pairplot(df, kind="scatter", hue="gravity", palette="Set2")
plt.show()
