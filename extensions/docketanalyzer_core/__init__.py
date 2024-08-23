modules = {
    'docketanalyzer_core': ['app'],
    'docketanalyzer_core.core.core_dataset': ['CoreDataset', 'load_dataset'],
    'docketanalyzer_core.core.docket_index': ['DocketBatch', 'DocketIndex', 'load_docket_index'],
    'docketanalyzer_core.core.docket_manager': ['DocketManager'],
    'docketanalyzer_core.core.elastic': ['load_elastic'],
    'docketanalyzer_core.core.juri': ['JuriscraperUtility'],
    'docketanalyzer_core.core.s3': ['S3Utility'],
    'docketanalyzer_core.core.task': ['Task', 'DocketTask', 'task_registry', 'register_task', 'load_tasks', 'load_task'],
    'docketanalyzer_core.core.websearch': ['WebSearch'],
}


from docketanalyzer import lazy_load_modules
lazy_load_modules(modules, globals())


def patch_cli(cli):
    from docketanalyzer_core.commands.check_dockets import check_dockets
    from docketanalyzer_core.commands.check_idb import check_idb_command
    from docketanalyzer_core.commands.open import open_command
    from docketanalyzer_core.commands.sync import push, pull
    from docketanalyzer_core.commands.tasks import tasks
    cli.add_command(check_dockets)
    cli.add_command(check_idb_command)
    cli.add_command(open_command)
    cli.add_command(push)
    cli.add_command(pull)
    cli.add_command(tasks)
