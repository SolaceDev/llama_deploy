from llama_deploy import LlamaDeployClient, ControlPlaneConfig

# points to deployed control plane
client = LlamaDeployClient(ControlPlaneConfig())

# create a session
session = client.create_session()

# # kick off run
task_id = session.run_nowait("my_workflow", arg1="hello_world")

print("task_id:", task_id)
# # stream events -- the will yield a dict representing each event
for event in session.get_task_result_stream(task_id):
    print("task result:", event)
    
print("Done")