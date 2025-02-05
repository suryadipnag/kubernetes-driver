import logging
import uuid
from .defaults import DEFAULT_NAMESPACE
from openshift.dynamic.exceptions import NotFoundError
from openshift.dynamic import DynamicClient
from kubernetes.client import V1DeleteOptions
from ignition.service.logging import logging_context

logger = logging.getLogger(__name__)

class OpenshiftApiController:

    def __init__(self, base_kube_client, default_namespace=DEFAULT_NAMESPACE):
        self.base_kube_client = base_kube_client
        self.dynamic_client = DynamicClient(base_kube_client)
        self.default_namespace = default_namespace

    def __get_resource_client(self, api_version, kind):
        return self.dynamic_client.resources.get(api_version=api_version, kind=kind)

    def _generate_additional_logs(self, body, message_direction, external_request_id, content_type,
                                  message_type, protocol, protocol_metadata, driver_request_id):
        try:
            logging_context_dict = {'message_direction' : message_direction, 'tracectx.externalrequestid' : external_request_id, 'content_type' : content_type,
                                    'message_type' : message_type, 'protocol' : protocol, 'protocol_metadata' : protocol_metadata, 'tracectx.driverrequestid' : driver_request_id}
            logging_context.set_from_dict(logging_context_dict)
            logger.info(body)
        finally:
            if('message_direction' in logging_context.data):
                logging_context.data.pop("message_direction")
            if('tracectx.externalrequestid' in logging_context.data):
                logging_context.data.pop("tracectx.externalrequestid")
            if('content_type' in logging_context.data):
                logging_context.data.pop("content_type")
            if('message_type' in logging_context.data):
                logging_context.data.pop("message_type")
            if('protocol' in logging_context.data):
                logging_context.data.pop("protocol")
            if('protocol_metadata' in logging_context.data):
                logging_context.data.pop("protocol_metadata")
            if('tracectx.driverrequestid' in logging_context.data):
                logging_context.data.pop("tracectx.driverrequestid")

    
    def create_object(self, object_config, default_namespace=None, driver_request_id=None):
        resource_client = self.__get_resource_client(object_config.api_version, object_config.kind)
        create_args = self.__build_create_arguments(resource_client, object_config, default_namespace)
        external_request_id = str(uuid.uuid4())
        logger.debug("create_args : %s", create_args)
        self._generate_additional_logs(create_args['body'], 'sent', external_request_id, 'application/json',
                                       'request', 'http', {'method':'post'}, driver_request_id)
        return_obj = resource_client.create(**create_args)
        self._generate_additional_logs(return_obj.to_dict(), 'received', external_request_id, 'application/json',
                                       'response', 'http', {'method':'post'}, driver_request_id)
        return return_obj

    def __build_create_arguments(self, resource_client, object_config, supplied_default_namespace):
        args = {
            'body': object_config.data
        }
        if resource_client.namespaced:
            args['namespace'] = self.__determine_namespace(object_config, supplied_default_namespace)
        return args

    def update_object(self, object_config, default_namespace=None, driver_request_id=None):
        resource_client = self.__get_resource_client(object_config.api_version, object_config.kind)
        update_args = self.__build_update_arguments(resource_client, object_config, default_namespace)
        external_request_id = str(uuid.uuid4())
        logger.debug("update_args : %s", update_args)
        self._generate_additional_logs(update_args['body'], 'sent', external_request_id, 'application/json',
                                       'request', 'http', {'method':'put'}, driver_request_id)   
        return_obj = resource_client.replace(**update_args)
        self._generate_additional_logs(return_obj.to_dict(), 'received', external_request_id, 'application/json',
                                       'response', 'http', {'method':'put'}, driver_request_id)
        return return_obj

    def __build_update_arguments(self, resource_client, object_config, supplied_default_namespace):
        args = {
            'body': object_config.data
        }
        if resource_client.namespaced:
            args['namespace'] = self.__determine_namespace(object_config, supplied_default_namespace)
        return args

    def safe_read_object(self, api_version, kind, name, namespace=None, driver_request_id=None):
        try:
            obj = self.read_object(api_version, kind, name, namespace=namespace, driver_request_id=driver_request_id)
            return True, obj
        except NotFoundError:
            return False, None

    def read_object(self, api_version, kind, name, namespace=None, driver_request_id=None):
        resource_client = self.__get_resource_client(api_version, kind)
        read_args = self.__build_read_arguments(resource_client, name, namespace)
        external_request_id = str(uuid.uuid4())
        logger.debug("read_args : %s", read_args)
        self._generate_additional_logs('', 'sent', external_request_id, '',
                                       'request', 'http', {'method':'get'}, driver_request_id)
        return_obj = resource_client.get(**read_args)
        self._generate_additional_logs(return_obj.to_dict(), 'received', external_request_id, 'application/json',
                                       'response', 'http', {'method':'get'}, driver_request_id)
        return return_obj

    def __build_read_arguments(self, resource_client, name, namespace):
        args = {
            'name': name
        }
        if namespace is not None:
            args['namespace'] = namespace
        return args

    def delete_object(self, api_version, kind, name, namespace=None, driver_request_id=None):
        resource_client = self.__get_resource_client(api_version, kind)
        delete_args = self.__build_delete_arguments(resource_client, name, namespace)
        external_request_id = str(uuid.uuid4())
        logger.debug("delete_args : %s", delete_args)
        self._generate_additional_logs(delete_args['body'], 'sent', external_request_id, 'application/json',
                                       'request', 'http', {'method':'delete'}, driver_request_id)
        return_obj = resource_client.delete(**delete_args)
        self._generate_additional_logs(return_obj.to_dict(), 'received', external_request_id, 'application/json',
                                       'response', 'http', {'method':'delete'}, driver_request_id)

    def __build_delete_arguments(self, resource_client, name, namespace):
        args = {
            'name': name,
            'body': V1DeleteOptions()
        }
        if namespace is not None:
            args['namespace'] = namespace
        return args

    def is_object_namespaced(self, api_version, kind):
        resource_client = self.__get_resource_client(api_version, kind)
        return resource_client.namespaced

    def __determine_namespace(self, object_config, supplied_default_namespace):
        if 'namespace' in object_config.metadata:
            return object_config.metadata.get('namespace')
        elif supplied_default_namespace is not None:
            return supplied_default_namespace
        else:
            return self.default_namespace