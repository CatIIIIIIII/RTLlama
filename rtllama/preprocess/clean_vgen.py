import re
from datasets import load_dataset
from tqdm import tqdm


def redact_email(text):
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    return email_pattern.sub("", text)

def redact_phone(text):
    phone_pattern = re.compile(r'\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b|\(\d{3}\)\s*\d{3}[-.\s]??\d{4}\b|\b\d{3}[-.\s]??\d{4}\b')
    return phone_pattern.sub("", text)

def redact_ssn(text):
    ssn_pattern = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    return ssn_pattern.sub("", text)

def redact_text(text):
    text = redact_email(text)
    text = redact_phone(text)
    text = redact_ssn(text)
    return text


data_files = {"train": "vgen_nodupl.csv"}
data_raw = load_dataset(path="/data/raw", data_files=data_files)["train"]
data_raw_ = []
data_length = []
with tqdm(len(data_raw)) as pbar:
    for data in data_raw:
        modified_text = redact_text(data["text"])
        length = len(modified_text.split())
        if length < 2000:
            data_length.append(length)
            data_raw_.append({"text": modified_text})
        pbar.update(1)

# save data_raw_ as new json file
import json
with open('vgen_nodupl_noiop.jsonl', 'w') as f:
    json.dump(data_raw_, f)

# plot the distribution of the length of the text
import matplotlib.pyplot as plt
plt.hist(data_length, bins=100)
plt.savefig('text_length_distribution.png')

from datasets import load_dataset
ds = load_dataset("json", data_files="vgen_nodupl_noiop.jsonl")
print(len(ds["train"]))