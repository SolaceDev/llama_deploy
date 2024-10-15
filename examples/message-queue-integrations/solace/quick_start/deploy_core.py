from llama_deploy.deploy.deploy import (
    deploy_core,
    ControlPlaneConfig,
    SolaceMessageQueueConfig,
)

async def main():
    await deploy_core(
        control_plane_config=ControlPlaneConfig(),
        message_queue_config=SolaceMessageQueueConfig(),
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
