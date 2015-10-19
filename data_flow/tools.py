

import pandas as pd
import numpy as np

"""
Tools to get the features
Code from Jonas Abernot
"""

##from "wrap_with_pandas 
def pq_to_timedelta(pq_time_scalar,asked_unit):
    magnitude = pq_time_scalar.rescale(asked_unit).magnitude
    rounded_magnitude = int(round(magnitude))
    print "Rounding error on quantity {0} : {1} {2}".format(pq_time_scalar, abs(magnitude - rounded_magnitude), asked_unit)
    return rounded_magnitude


## From transform_scripts.pandas_signal_parser
def apply_on_sliding_window(df, func, window_size, window_coverage,**kwargs):
    offsets = [str(int(window_size[:-1])*congruence/window_coverage)+window_size[-1] for congruence in range(window_coverage)]
#    vectorised_func = lambda array2d : np.apply_along_axis(func, 0, array2d, **kwargs)
    vec_func = lambda array2d : func(array2d, **kwargs)
    intermediate_dfs = []
    for offset in offsets:
        print offset
        intermediate_dfs.append(df.loc[pd.Timedelta(offset):,:].resample(window_size,how=vec_func))
    
    final_df = intermediate_dfs[0]
    for df in intermediate_dfs[1:]:
        final_df = final_df.combine_first(df)
    return final_df
    

def split_df_of_tuples(df):
    tuple_len = len(df.iloc[0,0])
    return (df.applymap(lambda t : t[i]) for i in range(tuple_len))