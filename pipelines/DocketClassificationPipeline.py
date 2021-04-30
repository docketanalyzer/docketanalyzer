import os
import torch
from transformers import AutoConfig, AutoTokenizer, AutoModel
from simpletransformers.classification import MultiLabelClassificationModel

class DocketClassificationPipeline(object):
	def __init__(self, batch_size=8, use_cuda=None, quantize=None, model_name='docketanalyzer/distilroberta-base-ddcl'):
		if use_cuda is None:
			use_cuda = torch.cuda.is_available()
		if quantize is None:
			quantize = not use_cuda

		model_args = {
			'eval_batch_size': batch_size,
			'no_cache': True,
		}
		if quantize:
			model_args['dynamic_quantize'] = True

		self.model_name = model_name
		self.config = AutoConfig.from_pretrained(self.model_name)
		self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
		self.model = MultiLabelClassificationModel('roberta', self.model_name, use_cuda=use_cuda, args=model_args)

	def __call__(self, docs):
		preds = self.model.predict(docs)[0]
		for i in range(len(preds)):
			preds[i] = [
				self.config.id2label[xi] 
				for xi in range(len(preds[i])) 
				if preds[i][xi] == 1
			]
		return preds


