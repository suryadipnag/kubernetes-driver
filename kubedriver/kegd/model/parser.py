import yaml
from kubedriver.kegd.model.exceptions import InvalidDeploymentStrategyError
from kubedriver.kegd.model.deployment_strategy import DeploymentStrategy
from kubedriver.kegd.model.deploy_task import DeployTask
from kubedriver.kegd.model.compose import ComposeScript

class DeploymentStrategyParser:

    def __init__(self, strategy_class=DeploymentStrategy):
        self._strategy_class = strategy_class

    def read_dict(self, data):
        compose = self.__read_compose(data)
        return self._strategy_class(compose=compose)

    def __read_compose(self, data):
        compose = []
        compose_defs = data.get('compose')
        if compose_defs != None:
            if not isinstance(compose_defs, list):
                raise InvalidDeploymentStrategyError(f'compose must be a list but was {type(compose_defs)}')
            seen_names = []
            for compose_def in compose_defs:
                compose_name = compose_def.get('name')
                if compose_name is None:
                    raise InvalidDeploymentStrategyError(f'compose entry missing name {compose_def}')
                if compose_name in seen_names:
                    raise InvalidDeploymentStrategyError(f'compose entry with duplicate name {compose_name}')
                else:
                    seen_names.append(compose_name)
                compose.append(self.__read_compose_def(compose_name, compose_def))
        return compose

    def __read_compose_def(self, compose_name, compose_def):
        deploy_tasks = []
        deploy_task_defs = compose_def.get('deploy')
        if deploy_task_defs != None:
            if not isinstance(deploy_task_defs, list):
                raise InvalidDeploymentStrategyError(f'compose deploy must be a list but was {type(deploy_task_defs)}')
            for deploy_task_def in deploy_task_defs:
                deploy_tasks.append(self.__read_deploy_task(deploy_task_def))
        reverse = compose_def.get('reverse')
        return ComposeScript(compose_name, deploy=deploy_tasks, reverse=reverse)
    
    def __read_deploy_task(self, deploy_task_def):
        if not isinstance(deploy_task_def, dict):
            raise InvalidDeploymentStrategyError(f'compose deploy task must be a dict/map but found a {type(deploy_task_def)}')
        return DeployTask.on_read(**deploy_task_def) 

