
# TDEER 

## Reproduction Steps

### 1. Requirements

The model was run in a Python 3.7 environment with the requirements that can be installed with:

```bash
pip install -r requirements.txt
```

### 2. Download Pretrained BERT

Click [BERT-Base-Cased](https://storage.googleapis.com/bert_models/2018_10_18/cased_L-12_H-768_A-12.zip) to download the pretrained model and then decompress to `pretrained-bert` folder.


### 4. Train & Eval

You can use `run.py` with `--do_train` to train the model. After training, you can also use `run.py` with `--do_test` to evaluate data.

train:

```bash
python -u run.py \
--do_train \
--model_name TM \
--rel_path data/TM/rel2id.json \
--train_path data/TM/triples_train.json \
--dev_path data/TM/triples_test.json \
--bert_dir pretrained-bert/cased_L-12_H-768_A-12 \
--save_path ckpts/tm.model \
--learning_rate 0.00005 \
--neg_samples 2 \
--epoch 200 \
--verbose 2
```

evaluate (validation set):

```
python run.py \
--do_test \
--model_name TM \
--rel_path data/TM/rel2id.json \
--test_path data/TM/triples_validation.json \
--bert_dir pretrained-bert/cased_L-12_H-768_A-12 \
--ckpt_path ckpts/tm.model \
--max_len 512 \
--verbose 1
```

evaluate (test set):

```
python run.py \
--do_test \
--model_name TM \
--rel_path data/TM/rel2id.json \
--test_path data/TM/triples_test.json \
--bert_dir pretrained-bert/cased_L-12_H-768_A-12 \
--ckpt_path ckpts/tm.model \
--max_len 512 \
--verbose 1
```
