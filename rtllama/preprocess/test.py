import json
import matplotlib.pyplot as plt

# load jsonl 
data = []
with open('rtllama/preprocess/test.jsonl', 'r') as f:
    for line in f:
        data.append(json.loads(line))
        

# 提取 epoch 和 loss for every 5 epochs
data = data[::5]
epochs = [entry['epoch'] for entry in data]
losses = [entry['loss'] for entry in data]

# 绘制损失函数曲线
plt.figure(figsize=(10, 6))
plt.plot(epochs, losses, label='Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Loss Function over Epochs')
plt.legend()
plt.grid(True)
# set y to log scale
# plt.xscale('log')
plt.show()
plt.savefig('loss.png')