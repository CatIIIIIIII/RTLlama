from datasets import load_dataset

data_files = {"train": "vgen.csv"}
dataset = load_dataset("data/pretrain", data_files=data_files)
dataset = dataset["train"]
print(dataset[0])