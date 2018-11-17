# Developer Guide

Openstack Gyan is the Machine Learning Infra as a service project. This document provides the following

  - How to setup openstack with Gyan using devstack
  - Describes the workflow in the Gyan
  - How to run the example application provided in the Gyan examples directory

# How to setup Gyan

  - Clone the devstack master branch 
    ```
    git clone https://github.com/openstack-dev/devstack
    ```
  - Copy the contents below to local.conf in devstack
    ```
    [[local|localrc]]
    HOST_IP=192.168.1.188
    SERVICE_HOST=192.168.1.188
    DATABASE_PASSWORD=password
    RABBIT_PASSWORD=password
    SERVICE_TOKEN=password
    SERVICE_PASSWORD=password
    ADMIN_PASSWORD=password
    enable_service rabbit mysql key
    enable_plugin gyan https://git.openstack.org/openstack/gyan
    enable_plugin heat https://git.openstack.org/openstack/heat
    LIBS_FROM_GIT="python-gyanclient"
    ENABLED_SERVICES+=gyan-api
    ```
  - Run stack.sh
    ```
    ./stack.sh
    ```
 
# Workflow of Gyan:
  - Create hints.yaml to specify the size of the compute node. For example
    ```
      python_version: 2.7
      cpu: 2
      memory: 1024 Mb
      disk: 20 Gb
      driver: TensorflowDriver
      additional_details: {}
    ```
  - After that create the flavor using hints template
    ```
    gyan flavor-create --hints-path flavor.yaml tensorflow
    ```
  - Compress your ML model that is already trained  and create a Gyan model
    ```
    gyan create-model --trained-model model.zip --type Tensorflow MNIST
    ```
  - Deploy model that was created in the previous step.
    ```
    gyan deploy-model <model-id>
    ```
  - The above command will launch the compute node based on the flavor details we gave in the first step. Once the compute node is launched, the gyan-compute will   be installed and connected to gyan-server.
  - We should get new host in `gyan host-list`.
  - In the last step you should see the deployed url of the model. We can find out using `gyan model-list` 

# How to use run sample example KnowThyNumber provided with Gyan:
  - Make sure you have installed golang in your system and set the GOROOT and GOPATH properly.
  -  Copy the KnowThyNumber example from `gyan/examples` to `GOPATH/src/github.com/<user-id>/KnowThyNumber`
  -  Now run `go run server.go`. This will start local server on `9000` port.
  -  We got deployed_url in the previous section. Get the openstack token using `openstack token issue`. 
  -  Open the browser and navigate to `http://localhost:9000`. Provide the `deployed_url` and `token` in the app. Now you can draw any number in the canvas and use your model to predict it.
