import re
import json
import copy
MAX_SEQ_LEN = 1500


def extract_io(src_code, io_type='input'):
    pattern = rf'\n\t*\s*{io_type}\s+([^\n]+)'
    matches = re.findall(pattern, src_code, re.DOTALL)
    names = {}
    for match in matches:
        match_bak = copy.deepcopy(match)
        match = match.strip(" ,;\n\t")
        if "//" in match:
            match = match.split("//")[0].strip(" ;,\t\n")
        if "[" in match and "]" in match:
            match = match.split("]")[-1].strip()

        if "," in match:
            name = [n.strip() for n in match.split(",")]
            for n in name:
                names[n] = match_bak
        else:
            names[match.split(" ")[-1]] = match_bak

    return names


def extract_cmt(ann_code, io_names, io_type='input'):
    ann_lines = extract_io(ann_code, io_type=io_type)

    if set(io_names) == set(list(ann_lines.keys())):
        # check "//" exists in all ann_names
        is_cmt_names = True
        for _, line in ann_lines.items():
            if "//" not in line:
                is_cmt_names = False

        if is_cmt_names:
            ann_cmt = {name: line.split('//')[1].strip()
                       for name, line in ann_lines.items()}
            if ann_cmt == {}:
                return None
            return ann_cmt

    return None


ref_path = 'is_ref_2048.json'
spec_path = 'spec_data_2048.json'
ann_path = 'ann_data_2048.json'

# Load the reference data
with open(ref_path) as f:
    ref_data = json.load(f)
with open(spec_path) as f:
    spec_data = json.load(f)
with open(ann_path) as f:
    ann_data = json.load(f)

# select from spec_data, where id is in ref_data
ref_ids = {item['id'] for item in ref_data}
src_data = {item['id']: item['src_code'] for item in ann_data}
ann_data = {item['id']: item['code_ann'] for item in ann_data}

print(type(src_data))

# 1. filter out the spec_data where the length of spec and src_code is less than MAX_SEQ_LEN
instruct_data = [{
    "id": item['id'],
    'spec': item['spec'],
    'src_code': src_data[item['id']]
} for item in spec_data if len(item['spec'].split()) + len(src_data[item['id']].split()) < MAX_SEQ_LEN]
print(
    f"Num of samples after length filtering: {len(instruct_data)}. ({len(instruct_data)/len(spec_data):.2f})")

# 2. filter out if the function is a placeholder
instruct_data = [
    item for item in instruct_data if 'placeholder' not in item['spec']]

# 3. extract input_ports and output_ports from ann_data
for data in instruct_data:
    data['input_ports'] = list(extract_io(ann_data[data['id']]).keys())
    data['output_ports'] = list(
        extract_io(ann_data[data['id']], io_type='output').keys())

# 4. extract comments from ann_data
for data in instruct_data:
    data['input_cmts'] = extract_cmt(
        ann_data[data['id']], data['input_ports'])
    data['output_cmts'] = extract_cmt(
        ann_data[data['id']], data['output_ports'], io_type='output')
instruct_data = [data for data in instruct_data if data['input_cmts']
                 is not None and data['output_cmts'] is not None]
print(
    f"Num of samples after comment filtering: {len(instruct_data)}. ({len(instruct_data)/len(spec_data):.2f})")
instruct_data_id = [data["id"] for data in instruct_data]

poor_data_id = [idx for idx in src_data.keys() if idx not in instruct_data_id]
poor_data = [{"id": idx,
              "src_code": src_data[idx],
              "ann_code": ann_data[idx]} for idx in poor_data_id]

# save them as json file seperately
with open('instruct_data.json', 'w') as f:
    json.dump(instruct_data, f, indent=4)
with open('poor_instruct_data.json', 'w') as f:
    json.dump(poor_data, f, indent=4)
