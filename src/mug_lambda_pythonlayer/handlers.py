import logging
from typing import Any, MutableMapping, Optional
import subprocess
import os, shutil, base64
import s3fs
import traceback

from cloudformation_cli_python_lib import (
    Action,
    HandlerErrorCode,
    OperationStatus,
    ProgressEvent,
    Resource,
    SessionProxy,
    exceptions,
)

from .models import ResourceHandlerRequest, ResourceModel

# Use this logger to forward log messages to CloudWatch Logs.
LOG = logging.getLogger(__name__)
LIBS = '/tmp/libs'
ZIP_EXE = f'{os.getcwd()}/mug_lambda_pythonlayer/zip'
TYPE_NAME = "MuG::Lambda::PythonLayer"

resource = Resource(TYPE_NAME, ResourceModel)
test_entrypoint = resource.test_entrypoint

class LambdaLayer:
    def __init__(self, state, session):
        self.state = state
        self.client = session.client("lambda")
        print('================================', state.Requirements)
        self.zip_path = f'/tmp/{state.Name}.zip'
        self.requirements = ','.join(state.Requirements)
        self.s3_path = f'/{state.S3Bucket}/{state.Name}.zip'
        self.layers_list = self.client.list_layer_versions(LayerName=self.state.Name)

    def exists(self, Name=None):
        if Name:
            return len(self.client.list_layer_versions(LayerName=Name)['LayerVersions']) > 0
        else:
            return len(self.layers_list['LayerVersions']) > 0

    def _init_libs(self):
        shutil.rmtree(LIBS, ignore_errors=True)
        os.makedirs(LIBS)

    def _executute(self, cmd, cwd=None):
        out = subprocess.Popen(cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, 
                cwd=cwd)
        stdout, stderr = out.communicate()
        return stdout, stderr

    def install(self, show_logs=True):
        cmd = ['pip', 'install', *self.requirements.split(','), '-t', LIBS, '--no-cache-dir']
        stdout, stderr = self._executute(cmd)
        if show_logs:
            for line in (stdout if stdout else stderr).decode('utf-8').splitlines(): 
                print(line)

    def _s3_upload(self):
        s3 = s3fs.S3FileSystem(anon=False)
        with open(self.zip_path, 'rb') as zf:
            with s3.open(self.s3_path, 'wb') as s3f:
                s3f.write(zf.read())

    def package(self):
        cmd = [ZIP_EXE, '-r', self.zip_path,  '.']
        stdout, stderr = self._executute(cmd, cwd=LIBS)
        self._s3_upload()

    def publish(self):
        response = self.client.publish_layer_version(
            LayerName=self.state.Name,
            Description=f'The Layer Contains: {self.requirements}',
            Content={
                'S3Bucket': self.state.S3Bucket,
                'S3Key': f'{self.state.Name}.zip'
            },
            CompatibleRuntimes = ['python3.6','python3.7','python3.8']
        )
        return response['LayerArn'], response['LayerVersionArn'], str(response['Version'])

    def delete(self, Name=None):
        if Name:
            layers_list = self.client.list_layer_versions(LayerName=Name)
            for layer in layers_list['LayerVersions']:               
                _ = self.client.delete_layer_version(
                    LayerName=self.state.Name,
                    VersionNumber=int(layer['Version'])
                ) 
        else:
            for layer in self.layers_list['LayerVersions']:               
                _ = self.client.delete_layer_version(
                    LayerName=self.state.Name,
                    VersionNumber=int(layer['Version'])
                )
        

    def create_model(self):
        return [ResourceModel(
            Name = self.state.Name,
            S3Bucket = self.state.S3Bucket,
            Requirements = self.state.Requirements,
            LayerArn = layer['LayerVersionArn'].replace(f":{layer['Version']}", ''),
            LayerVersionArn = layer['LayerVersionArn'],
            Version = layer['Version']
        ) for layer in self.layers_list['LayerVersions']]


@resource.handler(Action.CREATE)
def create_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:
    model = request.desiredResourceState
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
        resourceModel=model,
    )
    
    print("""
       __________  _________  ____________
      / ____/ __ \/ ____/   |/_  __/ ____/
     / /   / /_/ / __/ / /| | / / / __/   
    / /___/ _, _/ /___/ ___ |/ / / /___   
    \____/_/ |_/_____/_/  |_/_/ /_____/   
                                          
    """)
    
    layer = LambdaLayer(model, session)
    print(model)
    
    if (hasattr(model, 'Version') and model.Version != None or\
            hasattr(model, 'LayerVersionAr') and model.LayerVersionAr != None or\
                 hasattr(model, 'LayerArn') and model.LayerArn != None):
            raise exceptions.InvalidRequest(TYPE_NAME, model.Name)
    if layer.exists():
        raise exceptions.AlreadyExists(TYPE_NAME, model.Name)

    layer.install()
    layer.package()

    model.LayerArn, \
    model.LayerVersionArn, \
    model.Version = layer.publish()

    return ProgressEvent(status=OperationStatus.SUCCESS, resourceModel=model)


@resource.handler(Action.DELETE)
def delete_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:
    model = request.desiredResourceState
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
        resourceModel=model,
    )
    print("""
        ____  ________    __________________
       / __ \/ ____/ /   / ____/_  __/ ____/
      / / / / __/ / /   / __/   / / / __/   
     / /_/ / /___/ /___/ /___  / / / /___   
    /_____/_____/_____/_____/ /_/ /_____/                                    
                                          
    """)
    
    layer = LambdaLayer(model, session)
    
    if layer.exists():
        layer.delete()
    else:
        raise exceptions.NotFound(TYPE_NAME, model.Name)

    return ProgressEvent(status=OperationStatus.SUCCESS)

@resource.handler(Action.UPDATE)
def update_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:
    model = request.desiredResourceState
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS,
        resourceModel=model,
    )
    print(""" 
       __  ______  ____  ___  ____________
      / / / / __ \/ __ \/   |/_  __/ ____/
     / / / / /_/ / / / / /| | / / / __/   
    / /_/ / ____/ /_/ / ___ |/ / / /___   
    \____/_/   /_____/_/  |_/_/ /_____/   
    """)
    
    layer = LambdaLayer(model, session)
    try:
        if request.previousResourceState.Name != request.desiredResourceState.Name:
            layer.delete(request.previousResourceState.Name)
    except:
        pass
    
    if layer.exists(request.previousResourceState.Name):

        layer.delete(request.previousResourceState.Name)
        layer.install()
        layer.package()

        model.LayerArn, \
        model.LayerVersionArn, \
        model.Version = layer.publish()

        return ProgressEvent(status=OperationStatus.SUCCESS, resourceModel=model)
    else:
        raise exceptions.NotFound(TYPE_NAME, model.Name)


@resource.handler(Action.READ)
def read_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:
    model = request.desiredResourceState

    print("""
        ____  _________    ____ 
       / __ \/ ____/   |  / __ \
      / /_/ / __/ / /| | / / / /
     / _, _/ /___/ ___ |/ /_/ / 
    /_/ |_/_____/_/  |_/_____/  
                                
    """)

    layer = LambdaLayer(model, session)

    if not layer.exists():
        raise exceptions.NotFound(TYPE_NAME, model.Name)

    return ProgressEvent(
        status=OperationStatus.SUCCESS,
        resourceModel=model,
    )

@resource.handler(Action.LIST)
def list_handler(
    session: Optional[SessionProxy],
    request: ResourceHandlerRequest,
    callback_context: MutableMapping[str, Any],
) -> ProgressEvent:
    model = request.desiredResourceState
    print("""
        __    _______________
       / /   /  _/ ___/_  __/
      / /    / / \__ \ / /   
     / /____/ / ___/ // /    
    /_____/___//____//_/     
                            
    """)

    layer = LambdaLayer(model, session)

    if not layer.exists():
        return ProgressEvent(
            status=OperationStatus.SUCCESS,
            resourceModels=[],
        )
    else:
        return ProgressEvent(
            status=OperationStatus.SUCCESS,
            resourceModels=[model],
        )       
