"""
CineMatch AI - MLflow PyFunc Model Wrapper
Enables full MLflow Model Registry and serving support for scikit-surprise SVD.
"""
import joblib
import pandas as pd
import mlflow.pyfunc


class SVDModelWrapper(mlflow.pyfunc.PythonModel):
    """
    MLflow PyFunc wrapper for Surprise SVD recommendation model.
    """

    def load_context(self, context):
        self.model = joblib.load(context.artifacts["model_file"])

    def predict(self, context, model_input: pd.DataFrame) -> list[float]:
        """
        Predict ratings for given (userId, movieId) pairs.
        model_input is expected to have 'userId' and 'movieId' columns.
        """
        predictions = []
        for _, row in model_input.iterrows():
            est = self.model.predict(int(row["userId"]), int(row["movieId"])).est
            predictions.append(float(est))
        return predictions
