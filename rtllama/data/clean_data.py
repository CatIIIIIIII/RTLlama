import re
from datasets import load_dataset
from pprint import pprint
from tqdm import tqdm

def search_ports_cmt(rtl_code, ports_src):
    input_ports_ann = []
    for port in ports_src:
        pattern = rf"{port['name']}\s*,?\s*//\s*(.*)"
        match = re.search(pattern, rtl_code)
        if match:
            input_ports_ann.append({'name': port['name'], 'comment': match.group(1)})
        else:
            return None
    return input_ports_ann

def split_args(str_arg):
    
    comment = ''
    if "//" in str_arg:
        str_arg = str_arg.split("//")
        arg_name, comment = str_arg[0].strip(), str_arg[1].strip()
    else:
        arg_name = str_arg.strip()
    
    arg_name = arg_name.replace(')', '').replace('wire', '').replace('reg', '').replace(';', '')
    # arg_name remove all between []
    arg_name = re.sub(r'\[.*?\]', '', arg_name)
    # split in comma
    if "," in arg_name:
        arg_name = arg_name.split(",")
        arg_name = [a_g.strip() for a_g in arg_name if a_g != '']
        arg_name = [a_g.split(" ")[-1] if '[' in a_g and ']' in a_g else a_g for a_g in arg_name]
    else:
        arg_name = arg_name.split(" ")
        arg_name = [a_g for a_g in arg_name if a_g != '']
    arg_name = [a_g.strip() for a_g in arg_name]
    arg_list = []    
    for i in range(len(arg_name)):
        arg_list.append({'name': arg_name[i], 'comment': comment})
    return arg_list


# Function to extract module name and logic description from desc
def extract_desc(desc):
    
    # Extract logic description
    desc_split = desc.split("Logical Function Description:")
    if len(desc_split) == 1:
        logic_desc = ''
    else:
        logic_desc = desc.split("Logical Function Description:")[1].replace('```', '').strip()
    
    return logic_desc


# Function to extract parameters and ports from src_code
def extract_args(rtl_code, is_module_name=False):
    
    module_name = ''
    if is_module_name:
        # Extract module name
        module_name_match = re.search(r'module\s+(\w+)', rtl_code)
        module_name = module_name_match.group(1) if module_name_match else ''
    
    # Extract input ports and their comments
    input_ports = []
    input_matches = re.findall(r'\n\s*\(*input\s+([^\n]+)', rtl_code, re.DOTALL)
    for match in input_matches:
        arg_list = split_args(match)
        input_ports.extend(arg_list)
    
    # Extract output ports and their comments
    output_ports = []
    output_matches = re.findall(r'\n\s*\(*output\s+([^\n]+)', rtl_code, re.DOTALL)
    for match in output_matches:
        arg_list = split_args(match)
        output_ports.extend(arg_list)
        
    return module_name, input_ports, output_ports
    
    
dataset = load_dataset('json', data_files='/data/raw/code-ann-spec.jsonl')
dataset = dataset['train']
name_err = list()
desc_err = list()
len_ori = len(dataset)
outputs = []
i = 0
with tqdm(total=len(dataset)) as pbar:
    dataset_valid = []
    dataset_invalid = []
    for data in dataset:
        pbar.update(1)
        
        desc = data["spec"]
        src_code = data["src_code"]
        ann_code = data["ann_code"]
        
        # Filter out wrong keywords
        desc = desc.replace('Input', 'input').replace('Output', 'output')
        ann_code = ann_code.replace('Input', 'input').replace('Output', 'output')
        
        # Extract information
        logic_desc = extract_desc(desc)
        module_name_src, input_ports_src, output_ports_src = extract_args(src_code, is_module_name=True)
        module_name_ann, input_ports_ann, output_ports_ann = extract_args(ann_code)

        # Cross-check ports and parameters
        input_ports_match = set(port['name'] for port in input_ports_src) == set(port['name'] for port in input_ports_ann)
        output_ports_match = set(port['name'] for port in output_ports_src) == set(port['name'] for port in output_ports_ann)
        
        if not input_ports_match:
            try:
                input_ports_ann = search_ports_cmt(ann_code, input_ports_src)
                if input_ports_ann:
                    input_ports_match = True
            except:
                input_ports_match = True
        if not output_ports_match:
            try:
                output_ports_ann = search_ports_cmt(ann_code, output_ports_src)
                if output_ports_ann:
                    output_ports_match = True
            except:
                output_ports_match = True
        
        
        if input_ports_match and output_ports_match and module_name_src != '' and logic_desc != '':
            # Format the output
            instruction = f"""
Please act as a professional verilog designer. Implement a module to achieve the given implementation goal. The module must have the same name, input/output ports and parameters as described below. You could define helper modules but make that the generated file could be synthesized only. You could also define parameters in the function to make the module more flexible.

Module name:  
    {module_name_src}   
                
Input ports:
"""
            if input_ports_ann:
                for port in input_ports_ann:
                    instruction += f"    {port['name']} // {port['comment']}\n"
            else:
                instruction += "    None\n"
                
            instruction += "\nOutput ports:\n"
            if output_ports_ann:
                for port in output_ports_ann:
                    instruction += f"    {port['name']} // {port['comment']}\n"
            else:
                instruction += "    None\n"
                
            instruction += f"""
Implementation:
    {logic_desc}

Give me the complete code.

""" 
            output = src_code
            dataset_valid.append({
                "instruction": instruction, 
                "input": '',
                "output": output
                })
            
        else:
            if 'placeholder' in ann_code:
                dataset_invalid.append({
                    "id": data["id"], 
                    "src_code": src_code, 
                    "ann_code": ann_code,
                    "spec": desc
                    })
    
    print(f"Number of valid data: {len(dataset_valid)}, ({len(dataset_valid)/len_ori}%)")
    # save dataset_valid as jsonl file
    # use json dump to save the dataset_valid
    import json
    json.dump(dataset_valid, open('code-ann-spec-formatted.jsonl', 'w'))
    json.dump(dataset_invalid, open('code-ann-spec-invalid.jsonl', 'w'))

