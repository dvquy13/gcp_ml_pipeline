from .train import Trainer


class Analyzer:
    def __init__(self, params):
        self.params = params

    def run_task(self, task: str):
        if task == 'fit':
            runner = Trainer(self.params, load=False)
        runner.run()

def analyze(params, task: str):
    analyzer = Analyzer(params)
    analyzer.run_task(task)
