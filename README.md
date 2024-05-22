# RTLlama

## Continual Pre-training
bash rtllama/scripts/single_node.sh rtllama/configs/pretrain/codellama_full.yaml

## Instruction Clean-up
python rtllama/data/clean_data.py

## Instruction Finetuning
bash rtllama/scripts/single_node.sh rtllama/configs/finetune/codellama_full.yaml
