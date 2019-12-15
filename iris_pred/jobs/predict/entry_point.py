from .batch_predict import BatchPredictor
from .write_db import DBWriter


class Analyzer:
    def __init__(self, params):
        self.params = params

    def run_task(self, task: str):
        if task == 'batch_predict':
            runner = BatchPredictor(self.params)
        elif task == 'store_predictions':
            runner = DBWriter(self.params)
        runner.run()

def analyze(params, task: str):
    analyzer = Analyzer(params)
    analyzer.run_task(task)
