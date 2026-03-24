import numpy as np
import pandas as pd


class DropingScript:
    _PLACEHOLDERS = ("", "nan", "null", "undefined", "NaN", "None")

    def __init__(self, dataframe, max_missing_fraction=0.5):
        self.dataframe = dataframe.copy()
        self.max_missing_fraction = max_missing_fraction

    def drop_duplicates(self):
        self.dataframe = self.dataframe.drop_duplicates()
        return self

    def drop_nulls(self):
        self.dataframe = self.dataframe.dropna()
        return self

    def drop_rows_with_any_zero(self):
        numeric = self.dataframe.select_dtypes(include=np.number)
        if not numeric.empty:
            self.dataframe = self.dataframe.loc[~(numeric == 0).any(axis=1)]
        return self

    def placeholders_to_nan(self):
        self.dataframe = self.dataframe.replace(list(self._PLACEHOLDERS), np.nan)
        return self

    def drop_or_fill_missing_values(self):
        df = self.dataframe
        n_cols = df.shape[1]
        if n_cols == 0:
            return self
        max_missing = self.max_missing_fraction * n_cols
        self.dataframe = df.loc[df.isna().sum(axis=1) <= max_missing].copy()
        means = self.dataframe.select_dtypes(include=np.number).mean()
        self.dataframe = self.dataframe.fillna(means)
        return self
