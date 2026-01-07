



transport = streamablehttp_client(
            url= mcp_url,
            headers={"Authorization": f"Bearer {mcp_token}"}
            )

            async with transport as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    tools = await experimental_mcp_client.load_mcp_tools(
                        session=session, 
                        format="openai"
                    )

                    tools = _filter_tools(tools, tools_filter)