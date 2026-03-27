import os
import pandas as pd


class DatasetLoader:
    def __init__(self):
        self.datasets = {}

    def load_all(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))

        possible_paths = {
            "colleges": [
                os.path.join(base_dir, "data", "cleaned", "Colleges_cleaned.csv"),
                os.path.join(base_dir, "data", "colleges_cleaned.csv"),
            ],
            "jobs_exams": [
                os.path.join(base_dir, "data", "cleaned", "Job&Exam_cleaned.csv"),
                os.path.join(base_dir, "data", "Job&Exam_cleaned.csv"),
            ],
            "internships": [
                os.path.join(base_dir, "data", "cleaned", "Job&Exam_cleaned.csv"),
                os.path.join(base_dir, "data", "cleaned", "internships_cleaned.csv"),
            ],
            "scholarships": [
                os.path.join(base_dir, "data", "cleaned", "haryana_scholarships_cleaned.csv"),
            ],
            "schemes": [
                os.path.join(base_dir, "data", "cleaned", "schemes_cleaned.csv"),
                os.path.join(base_dir, "data", "schemes_cleaned.csv"),
            ],
        }

        for key, paths in possible_paths.items():
            loaded = False

            for path in paths:
                if os.path.exists(path):
                    try:
                        self.datasets[key] = pd.read_csv(path)
                        print(f"[DATASET LOADED] {key}: {path}")
                        print(f"[COLUMNS] {key}: {list(self.datasets[key].columns)}")
                        loaded = True
                        break
                    except Exception as e:
                        print(f"[DATASET LOAD ERROR] {key}: {path} -> {e}")

            if not loaded:
                self.datasets[key] = pd.DataFrame()
                print(f"[DATASET NOT FOUND] {key}")

    def get(self, name: str):
        return self.datasets.get(name, pd.DataFrame())


dataset_loader = DatasetLoader()