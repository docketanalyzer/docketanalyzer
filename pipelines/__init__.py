from .DocketClassificationPipeline import DocketClassificationPipeline


def pipeline(pipeline_name, **args):
	if pipeline_name == 'docket-classification':
		return DocketClassificationPipeline(**args)
	else:
		raise Exception('%s is not a valid pipeline.' % pipeline_name)




