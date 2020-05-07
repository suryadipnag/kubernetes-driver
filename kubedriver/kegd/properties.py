from ignition.service.framework import Service, Capability
from ignition.service.config import ConfigurationPropertiesGroup, ConfigurationProperties

class KegDeploymentProperties(ConfigurationPropertiesGroup, Service, Capability):

    def __init__(self):
        super().__init__('kegd')
        self.strategy = KegDeploymentStrategyProperties()
        self.element = KegDeploymentElementProperties()

class KegDeploymentStrategyProperties(ConfigurationProperties, Service, Capability):

    def __init__(self):
        self.templating = TemplatingProperties()
        self.templating.syntax['block_start_string'] = '!{%'
        self.templating.syntax['block_end_string'] = '%}!'
        self.templating.syntax['variable_start_string'] = '!{{'
        self.templating.syntax['variable_end_string'] = '}}!'

class KegDeploymentElementProperties(ConfigurationProperties, Service, Capability):

    def __init__(self):
        self.templating = TemplatingProperties()

class TemplatingProperties(ConfigurationProperties):
    
    def __init__(self):
        self.syntax = {
            'block_start_string': '{%',
            'block_end_string': '%}',
            'variable_start_string': '{{',
            'variable_end_string': '}}'
        }
