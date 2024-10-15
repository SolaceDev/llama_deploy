# Description
This example demonstrates how to run a workflow called deploy_workflow and interact with it. The workflow responds to each query with, ‘I am doing something!’ You can customize the deploy_workflow to add more features and functionalities to the agent.

## Installation
Install the [Solace PubSub+ event broker](https://docs.solace.com/Get-Started/Getting-Started-Try-Broker.htm). Ensure that the broker is running.

## Run
Deploy the core on a terminal.

``` bash
python -m examples.message-queue-integrations.solace.quick_start.deploy_core
```

Deploy the workflow on a terminal.

``` bash
python -m examples.message-queue-integrations.solace.quick_start.deploy_workflow
```

Interact with the workflow. This script generates a task, which sends a query to the workflow.

``` bash
python -m examples.message-queue-integrations.solace.quick_start.interaction
```

## Verification
Open the PubSub+ interface in your browser. If you’re running PubSub+ locally, go to http://localhost:8080. Use ‘admin’ for both the username and password. Once the dashboard loads, click on ‘Try Me’ from the left-side menu. Then, subscribe to the ‘my_workflow’ topic to monitor events.
