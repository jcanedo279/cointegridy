import pandas as pd
from sklearn import linear_model


def multiple_regr(predictor_seqs, trg_seq):
    
    if type(predictor_seqs) == pd.DataFrame:
        
    
    regr = linear_model.LinearRegression()
    regr.fit(X, y)

    # predictedCO2 = regr.predict([[2300, 1300]])
