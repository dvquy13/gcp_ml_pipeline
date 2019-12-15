from .data_importer import DataImporter

class Analyzer:
    def __init__(self, params):
        self.params = params

    def run_task(self, task: str):
        if task == 'query_train_pred':
            runner = DataImporter(self.params)
        runner.run()

def analyze(params, task: str):
    analyzer = Analyzer(params)
    analyzer.run_task(task)